#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consulta_anual_sargazo.py

Consulta la base de datos de resultados de sargazo y genera UN UNICO archivo
GeoJSON con todas las detecciones (puntos) de toda la region para un anio dado.

El archivo resultante reproduce las mismas propiedades que la salida operativa
(x, y en UTM, clave, idpoligono, tile, fecha, fechadia, distcosta_km, area_km2,
lugar, nom_playa) y la geometria de cada punto en EPSG:4326.

Este archivo esta pensado para que despues se le haga una LIMPIEZA MANUAL de
falsos positivos. El archivo ya limpio es el que entra al script de estadisticas
(estadisticas_anual_sargazo.py).

Uso:
    python3 consulta_anual_sargazo.py --anio 2024
    python3 consulta_anual_sargazo.py --anio 2024 --region 1 --salida /ruta/resultados/

@author: urielm
"""
import os
import json
import argparse
import datetime

import psycopg2
import base


# ------------------------------------------------------------------------------
# Tablas de resultados por region
# ------------------------------------------------------------------------------
TABLAS_REGION = {
    1: "sargazo",     # region principal (datos completos)
    2: "sargazo_2",   # region secundaria
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Genera un GeoJSON anual de toda la region a partir de la BD de sargazo."
    )
    parser.add_argument("--anio", type=int, required=True,
                        help="Anio a consultar, p.ej. 2024.")
    parser.add_argument("--region", type=int, default=1, choices=[1, 2],
                        help="Region/tabla a consultar: 1=sargazo (default), 2=sargazo_2.")
    parser.add_argument("--salida", type=str,
                        default="/data/output/sentinel2/l2/geojson/sargazo_anual/",
                        help="Carpeta de salida donde se guarda el GeoJSON anual.")
    parser.add_argument("--utm-epsg", type=int, default=32616,
                        help="EPSG UTM para calcular x,y (default 32616 = UTM 16N).")
    parser.add_argument("--lote", type=int, default=50000,
                        help="Tamanio del lote para lectura por servidor (default 50000).")
    return parser.parse_args()


def conexionDB():
    conect = psycopg2.connect(
        host=base.DB_host,
        database=base.DB_name,
        user=base.DB_user,
        password=base.DB_password,
        port=base.DB_port,
        connect_timeout=30,
    )
    return conect


def consulta_anual(conect, tabla, anio, utm_epsg, salida, lote):
    """Escribe el GeoJSON anual de forma incremental (streaming) para no cargar
    en memoria millones de puntos."""

    os.makedirs(salida, exist_ok=True)

    # ST_DumpPoints garantiza que cada feature sea un punto, aunque alguna
    # geometria almacenada sea MultiPoint.
    sql = """
        SELECT
            t.id                                            AS clave,
            t.idpoligono                                    AS idpoligono,
            t.tile                                          AS tile,
            t.fecha                                         AS fecha,
            to_char(t.fechadia, 'YYYY-MM-DD')               AS fechadia,
            t.distcosta_km                                  AS distcosta_km,
            t.area_km2                                      AS area_km2,
            t.lugar                                         AS lugar,
            t.nom_playa                                     AS nom_playa,
            ST_X(dp.geom)                                   AS lon,
            ST_Y(dp.geom)                                   AS lat,
            ST_X(ST_Transform(dp.geom, %(epsg)s))           AS x,
            ST_Y(ST_Transform(dp.geom, %(epsg)s))           AS y
        FROM {tabla} t,
             LATERAL ST_DumpPoints(t.geom) dp
        WHERE EXTRACT(YEAR FROM t.fechadia) = %(anio)s
        ORDER BY t.fechadia, t.idpoligono, t.id
    """.format(tabla=tabla)

    archivo = os.path.join(salida, "sargazo_region{r}_{a}.geojson".format(
        r=_region_de_tabla(tabla), a=anio))

    # Cursor del lado del servidor para iterar sin traer todo a memoria.
    cur = conect.cursor(name="cur_anual_sargazo")
    cur.itersize = lote
    cur.execute(sql, {"epsg": utm_epsg, "anio": anio})

    n = 0
    with open(archivo, "w", encoding="utf-8") as f:
        f.write('{\n"type": "FeatureCollection",\n"features": [\n')
        primero = True
        while True:
            filas = cur.fetchmany(lote)
            if not filas:
                break
            bloque = []
            for (clave, idpoligono, tile, fecha, fechadia, distcosta_km,
                 area_km2, lugar, nom_playa, lon, lat, x, y) in filas:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "x": _r(x, 1),
                        "y": _r(y, 1),
                        "clave": clave,
                        "idpoligono": idpoligono,
                        "tile": tile,
                        "fecha": fecha,
                        "fechadia": fechadia,
                        "distcosta_km": _r(distcosta_km, 4),
                        "area_km2": _r(area_km2, 4),
                        "lugar": lugar,
                        "nom_playa": nom_playa if nom_playa is not None else "null",
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    },
                }
                prefijo = ",\n" if not primero else ""
                bloque.append(prefijo + json.dumps(feature, ensure_ascii=False))
                primero = False
            f.write("".join(bloque))
            n += len(filas)
            print("  ... {} puntos escritos".format(n))
        f.write("\n]\n}\n")

    cur.close()
    return archivo, n


def _region_de_tabla(tabla):
    for r, t in TABLAS_REGION.items():
        if t == tabla:
            return r
    return tabla


def _r(valor, ndec):
    if valor is None:
        return None
    return round(float(valor), ndec)


def main():
    args = parse_args()
    tabla = TABLAS_REGION[args.region]

    print("=" * 70)
    print("Consulta anual de sargazo")
    print("  Region : {} (tabla '{}')".format(args.region, tabla))
    print("  Anio   : {}".format(args.anio))
    print("  UTM    : EPSG:{}".format(args.utm_epsg))
    print("  Salida : {}".format(args.salida))
    print("=" * 70)

    t0 = datetime.datetime.now()
    conect = conexionDB()
    try:
        archivo, n = consulta_anual(conect, tabla, args.anio,
                                    args.utm_epsg, args.salida, args.lote)
    finally:
        conect.close()

    dt = (datetime.datetime.now() - t0).total_seconds()
    print("-" * 70)
    if n == 0:
        print("ADVERTENCIA: no se encontraron detecciones para el anio {} en '{}'."
              .format(args.anio, tabla))
    print("GeoJSON generado: {}".format(archivo))
    print("Total de puntos : {}".format(n))
    print("Tiempo          : {:.1f} s".format(dt))
    print("Siguiente paso  : limpieza manual de falsos positivos sobre este archivo,")
    print("                  luego correr estadisticas_anual_sargazo.py")


if __name__ == "__main__":
    main()
