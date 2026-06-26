#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consulta_municipios_sargazo.py

Paso 1 de 2. Consulta la base de datos de resultados de sargazo (tabla `sargazo`,
region 1) para un anio dado (default 2026) y construye un GeoJSON de POLIGONOS
enriquecido con:

  - municipio  : municipio de Quintana Roo asignado por cercania (sjoin_nearest).
  - banda_costa: franja de distancia a la LINEA DE COSTA, calculada con buffers
                 que siguen la forma de la costa (0 m playa / 0-10 m / 10-100 m /
                 100 m-1 km / 1-10 km / >10 km).
  - dist_costa_m: distancia (m) de cada poligono a la linea de costa.

La base ya esta limpia, por lo que NO hay paso de limpieza manual. La salida de
este script alimenta a estadisticas_municipios_sargazo.py.

NOTA SRID: los poligonos de sargazo pueden estar almacenados en UTM y la capa de
municipios en geograficas. El script detecta el SRID real de la tabla y normaliza
todo a EPSG:4326 al leer; los calculos metricos (distancias, areas, buffers) se
hacen reproyectando a UTM (--utm-epsg, default 32616).

Linea de costa: se deriva del borde (boundary) de la mascara de tierra que usan
los scripts de procesamiento (p.ej. land_UTM16N_20m_2021.geojson). Asi las bandas
"siguen la forma de la costa". Se recorta a un buffer de los municipios para
descartar los bordes artificiales de los tiles.

Uso (en el servidor, con el entorno adecuado):
    python3 consulta_municipios_sargazo.py --anio 2026 \
        --mascara-tierra /home/sargazo/LANOT_sentinel2_sargazo/data/masks/land_UTM16N_20m_2021.geojson

@author: urielm
"""
import os
import json
import argparse
import datetime

import numpy as np
import pandas as pd
import geopandas as gpd
import psycopg2
import base

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------------------
# Configuracion por defecto
# ------------------------------------------------------------------------------
TABLAS_REGION = {1: "sargazo", 2: "sargazo_2"}
DEF_MUNICIPIOS = os.path.join(RAIZ, "data", "limites", "municipios_QR.geojson")
CAMPO_MUNI_DEF = "NOMGEO"
UTM_EPSG = 32616  # UTM 16N (Caribe mexicano)

# Banda especial para sargazo que cae SOBRE tierra/costa.
ETIQ_PLAYA = "0 m (playa)"
# Cortes de distancia (m) a la costa para el sargazo en el MAR (5 intervalos).
CORTES_M = [0, 10, 100, 1000, 10000, np.inf]
ETIQ_MAR = ["0-10 m", "10-100 m", "100 m-1 km", "1-10 km", ">10 km"]
# Orden completo (playa + mar) para reportes posteriores.
ETIQ_BANDA = [ETIQ_PLAYA] + ETIQ_MAR


def parse_args():
    p = argparse.ArgumentParser(
        description="Consulta sargazo por anio y lo cruza con municipios y bandas de costa.")
    p.add_argument("--anio", type=int, default=2026, help="Anio a consultar (default 2026).")
    p.add_argument("--region", type=int, default=1, choices=[1, 2],
                   help="Region/tabla: 1=sargazo (default, unico solicitado).")
    p.add_argument("--municipios", default=DEF_MUNICIPIOS,
                   help="GeoJSON de municipios de Quintana Roo.")
    p.add_argument("--campo-municipio", default=CAMPO_MUNI_DEF,
                   help="Columna con el nombre del municipio (default NOMGEO).")
    p.add_argument("--mascara-tierra", default=None,
                   help="GeoJSON poligonal de tierra; su borde es la linea de costa.")
    p.add_argument("--linea-costa", default=None,
                   help="GeoJSON de LINEA de costa ya lista (alternativa a --mascara-tierra).")
    p.add_argument("--zee", default=None,
                   help="GeoJSON de la ZEE (Caribe). Si se da, calcula la serie diaria de "
                        "TODA la ZEE (sin filtro municipal) y su dia de mayor arribazon.")
    p.add_argument("--salida", default=os.path.join(RAIZ, "data", "2026"),
                   help="Carpeta de salida.")
    p.add_argument("--max-dist-municipio-km", type=float, default=50.0,
                   help="Descarta poligonos a mas de esta distancia del municipio mas cercano.")
    p.add_argument("--utm-epsg", type=int, default=UTM_EPSG, help="EPSG metrico (default 32616).")
    p.add_argument("--precision", type=int, default=8, help="Decimales de coords en el GeoJSON.")
    p.add_argument("--exporta-bandas", action="store_true",
                   help="Exporta tambien las geometrias de los anillos de banda (para mapas).")
    return p.parse_args()


def _union(geoms):
    """unary_union compatible con geopandas viejo y nuevo (union_all)."""
    if hasattr(geoms, "union_all"):
        return geoms.union_all()
    return geoms.unary_union


def conexionDB():
    return psycopg2.connect(host=base.DB_host, database=base.DB_name, user=base.DB_user,
                            password=base.DB_password, port=base.DB_port, connect_timeout=30)


def detecta_srid(conect, tabla, utm_epsg):
    """Devuelve el SRID con que estan almacenadas las geometrias de la tabla.
    Los datos de sargazo pueden estar en UTM; municipios en geograficas."""
    cur = conect.cursor()
    cur.execute("SELECT ST_SRID(geom) FROM {tabla} WHERE geom IS NOT NULL LIMIT 1".format(tabla=tabla))
    fila = cur.fetchone()
    cur.close()
    srid = fila[0] if fila else 0
    print("  SRID detectado en '{}': {}".format(tabla, srid))
    return srid if srid and srid > 0 else utm_epsg


def lee_sargazo(anio, tabla, precision, utm_epsg):
    """Trae los poligonos del anio como GeoDataFrame en EPSG:4326,
    detectando y reproyectando desde el SRID real de la tabla (UTM o geo)."""
    print("Consultando BD (tabla '{}', anio {})...".format(tabla, anio))
    conect = conexionDB()
    try:
        srid = detecta_srid(conect, tabla, utm_epsg)
        # Geometria normalizada a 4326 sin importar como este almacenada.
        if srid == 4326:
            geom_4326 = "t.geom"
        else:
            geom_4326 = "ST_Transform(ST_SetSRID(t.geom, {srid}), 4326)".format(srid=srid)
        sql = """
            SELECT t.id AS clave, t.idpoligono, t.tile, t.fecha,
                   to_char(t.fechadia,'YYYY-MM-DD') AS fechadia,
                   COALESCE(t.area_km2, ST_Area({g4326}::geography)/1e6) AS area_km2,
                   t.distcosta_km, t.lugar, t.nom_playa,
                   ST_AsGeoJSON({g4326}, %(prec)s) AS gj
            FROM {tabla} t
            WHERE EXTRACT(YEAR FROM t.fechadia) = %(anio)s
        """.format(tabla=tabla, g4326=geom_4326)
        cur = conect.cursor(name="cur_muni")
        cur.itersize = 20000
        cur.execute(sql, {"prec": precision, "anio": anio})
        regs, geoms = [], []
        for (clave, idp, tile, fecha, fechadia, area_km2, dist, lugar, nom, gj) in cur:
            regs.append((clave, idp, tile, fecha, fechadia, area_km2, dist, lugar, nom))
            geoms.append(gj)
        cur.close()
    finally:
        conect.close()
    if not regs:
        return gpd.GeoDataFrame(columns=["clave"], geometry=[], crs="EPSG:4326")
    from shapely.geometry import shape
    df = pd.DataFrame(regs, columns=["clave", "idpoligono", "tile", "fecha", "fechadia",
                                     "area_km2", "distcosta_km", "lugar", "nom_playa"])
    gseries = gpd.GeoSeries([shape(json.loads(g)) for g in geoms], crs="EPSG:4326")
    gdf = gpd.GeoDataFrame(df, geometry=gseries, crs="EPSG:4326")
    print("  poligonos leidos: {:,}".format(len(gdf)))
    return gdf


def asigna_municipio(gdf_utm, municipios_utm, campo, max_dist_m):
    """Asigna el municipio mas cercano a cada poligono y filtra por distancia."""
    muni = municipios_utm[[campo, "geometry"]].rename(columns={campo: "municipio"})
    print("Asignando municipio por cercania...")
    joined = gpd.sjoin_nearest(gdf_utm, muni, how="left", distance_col="dist_mun_m")
    joined = joined[~joined.index.duplicated(keep="first")].copy()
    joined.drop(columns=[c for c in joined.columns if c.startswith("index_")],
                inplace=True, errors="ignore")
    antes = len(joined)
    joined = joined[joined["dist_mun_m"] <= max_dist_m].copy()
    print("  descartados por > {:.0f} km del municipio: {:,}".format(
        max_dist_m / 1000.0, antes - len(joined)))
    return joined


def linea_costa(args, municipios_utm, utm_epsg):
    """Devuelve la linea de costa (geometria unaria, UTM) recortada a la zona."""
    if args.linea_costa:
        costa = gpd.read_file(args.linea_costa).to_crs(epsg=utm_epsg)
        geom = _union(costa.geometry)
    elif args.mascara_tierra:
        tierra = gpd.read_file(args.mascara_tierra).to_crs(epsg=utm_epsg)
        geom = _union(tierra.geometry).boundary
    else:
        raise SystemExit("Falta --mascara-tierra o --linea-costa para construir las bandas.")
    # Recorta la costa a un buffer de los municipios (descarta bordes de tile).
    zona = _union(municipios_utm.geometry).buffer(60000)  # 60 km
    geom = geom.intersection(zona)
    return geom


def clasifica_bandas(gdf_utm, costa_geom, tierra_geom=None):
    """Distancia (m) a la costa y banda.
    - Sargazo SOBRE tierra/costa  -> banda '0 m (playa)' (dist 0).
    - Sargazo en el MAR           -> 5 bandas por distancia a la costa.
    """
    print("Calculando distancia a la costa y banda...")
    reps = gdf_utm.geometry.representative_point()
    dist = reps.distance(costa_geom)
    sobre_tierra = reps.within(tierra_geom) if tierra_geom is not None \
        else pd.Series(False, index=gdf_utm.index)
    dist = dist.where(~sobre_tierra.values, 0.0)

    # Bandas de mar (5 intervalos) con pd.cut; luego override de playa.
    banda = pd.cut(dist, bins=CORTES_M, labels=ETIQ_MAR,
                   right=False, include_lowest=True).astype("object")
    banda = banda.where(~sobre_tierra.values, ETIQ_PLAYA)

    gdf_utm = gdf_utm.copy()
    gdf_utm["dist_costa_m"] = np.round(dist.values, 1)
    gdf_utm["banda_costa"] = pd.Series(banda).fillna(ETIQ_MAR[-1]).values
    return gdf_utm


def exporta_bandas(costa_geom, tierra_geom, salida, anio, utm_epsg):
    """Anillos de buffer (lado mar) para usar en mapas."""
    radios = [r for r in CORTES_M[1:] if np.isfinite(r)]
    anillos, prev = [], None
    etiquetas_anillo = ETIQ_MAR[:len(radios)]  # bandas de mar con buffer finito
    for r, et in zip(radios, etiquetas_anillo):
        b = costa_geom.buffer(r)
        anillo = b if prev is None else b.difference(prev)
        if tierra_geom is not None:
            anillo = anillo.difference(tierra_geom)  # solo lado mar
        anillos.append({"banda_costa": et, "radio_m": r, "geometry": anillo})
        prev = b
    gdf = gpd.GeoDataFrame(anillos, crs="EPSG:{}".format(utm_epsg)).to_crs(4326)
    ruta = os.path.join(salida, "bandas_costa_{}.geojson".format(anio))
    gdf.to_file(ruta, driver="GeoJSON")
    print("  bandas (anillos) exportadas: {}".format(ruta))


def _escribe_serie_diaria(gdf_utm, salida, anio, sufijo):
    """Serie diaria (area y nº de poligonos) de un GeoDataFrame; escribe CSV y
    devuelve el dia de mayor arribazon. No aplica ningun recorte."""
    sub = gdf_utm.copy()
    sub["fechadia"] = pd.to_datetime(sub["fechadia"], errors="coerce")
    sub["dia"] = sub["fechadia"].dt.date.astype(str)
    serie = (sub.groupby("dia", as_index=False)
             .agg(n_poligonos=("area_km2", "size"),
                  area_km2=("area_km2", "sum"))
             .sort_values("area_km2", ascending=False))
    serie["area_km2"] = serie["area_km2"].round(4)
    ruta = os.path.join(salida, "sargazo_{}_serie_diaria_{}.csv".format(sufijo, anio))
    serie.sort_values("dia").to_csv(ruta, index=False)
    return ruta, serie.iloc[0]


def serie_diaria_region_total(gdf_utm, salida, anio):
    """Serie diaria de TODA la region monitoreada (toda la tabla del anio, sin
    recorte espacial). Reproduce un 'SUM(area_km2) GROUP BY fechadia'."""
    print("Calculando serie diaria de toda la region monitoreada (sin recorte)...")
    ruta, top = _escribe_serie_diaria(gdf_utm, salida, anio, "total")
    print("  poligonos: {:,} | serie exportada: {}".format(len(gdf_utm), ruta))
    print("  DIA DE MAYOR ARRIBAZON (toda la region): {} -> {:.3f} km2 ({:,} poligonos)".format(
        top["dia"], top["area_km2"], int(top["n_poligonos"])))
    return ruta


def serie_diaria_zee(gdf_utm, zee_path, utm_epsg, salida, anio):
    """Serie diaria de sargazo dentro de la ZEE mexicana (Caribe), sin filtro
    municipal. Captura el sargazo de mar abierto que el analisis por municipio
    (umbral 50 km) descarta, pero solo lo que cae dentro de aguas mexicanas."""
    print("Calculando serie diaria recortada a la ZEE mexicana...")
    zee = gpd.read_file(zee_path).to_crs(epsg=utm_epsg)
    zee_geom = _union(zee.geometry)
    reps = gdf_utm.geometry.representative_point()
    dentro = reps.within(zee_geom)
    sub = gdf_utm.loc[dentro.values].copy()
    print("  poligonos dentro de la ZEE: {:,} de {:,}".format(len(sub), len(gdf_utm)))
    if sub.empty:
        return None
    ruta, top = _escribe_serie_diaria(sub, salida, anio, "zee")
    print("  serie diaria ZEE exportada: {}".format(ruta))
    print("  DIA DE MAYOR ARRIBAZON (ZEE mexicana): {} -> {:.3f} km2 ({:,} poligonos)".format(
        top["dia"], top["area_km2"], int(top["n_poligonos"])))
    return ruta


def main():
    args = parse_args()
    tabla = TABLAS_REGION[args.region]
    os.makedirs(args.salida, exist_ok=True)

    print("=" * 70)
    print("Consulta de sargazo por municipio y banda de costa")
    print("  Anio       : {}".format(args.anio))
    print("  Tabla      : {}".format(tabla))
    print("  Municipios : {}".format(args.municipios))
    print("=" * 70)

    gdf = lee_sargazo(args.anio, tabla, args.precision, args.utm_epsg)
    if gdf.empty:
        raise SystemExit("No hay detecciones para el anio {}.".format(args.anio))

    municipios = gpd.read_file(args.municipios)
    municipios_utm = municipios.to_crs(epsg=args.utm_epsg)
    tierra_geom = None
    if args.mascara_tierra:
        tierra_geom = _union(gpd.read_file(args.mascara_tierra).to_crs(epsg=args.utm_epsg).geometry)

    gdf_utm = gdf.to_crs(epsg=args.utm_epsg)

    # Series diarias sobre el universo completo (antes del filtro municipal):
    #  1) toda la region monitoreada (sin recorte; = SUM(area) GROUP BY fechadia)
    #  2) recortada a la ZEE mexicana (solo aguas de Mexico), si se da --zee
    serie_diaria_region_total(gdf_utm, args.salida, args.anio)
    if args.zee:
        serie_diaria_zee(gdf_utm, args.zee, args.utm_epsg, args.salida, args.anio)

    gdf_utm = asigna_municipio(gdf_utm, municipios_utm, args.campo_municipio,
                               args.max_dist_municipio_km * 1000.0)
    costa = linea_costa(args, municipios_utm, args.utm_epsg)
    gdf_utm = clasifica_bandas(gdf_utm, costa, tierra_geom)

    # Recalcula area_km2 desde geometria si viniera nula.
    falt = gdf_utm["area_km2"].isna()
    if falt.any():
        gdf_utm.loc[falt, "area_km2"] = gdf_utm.loc[falt].geometry.area / 1e6

    salida_gdf = gdf_utm.to_crs(4326)
    cols = ["clave", "idpoligono", "tile", "fecha", "fechadia", "area_km2",
            "distcosta_km", "dist_costa_m", "municipio", "banda_costa",
            "lugar", "nom_playa", "geometry"]
    salida_gdf = salida_gdf[[c for c in cols if c in salida_gdf.columns]]

    ruta = os.path.join(args.salida, "sargazo_municipios_{}.geojson".format(args.anio))
    salida_gdf.to_file(ruta, driver="GeoJSON")

    if args.exporta_bandas:
        exporta_bandas(costa, tierra_geom, args.salida, args.anio, args.utm_epsg)

    print("-" * 70)
    print("GeoJSON enriquecido: {}".format(ruta))
    print("Poligonos finales  : {:,}".format(len(salida_gdf)))
    print("Municipios presentes: {}".format(
        ", ".join(sorted(salida_gdf["municipio"].dropna().unique()))))
    print("Reparto por banda:")
    print(salida_gdf["banda_costa"].value_counts().to_string())
    print("Siguiente paso: estadisticas_municipios_sargazo.py --entrada {}".format(ruta))


if __name__ == "__main__":
    main()
