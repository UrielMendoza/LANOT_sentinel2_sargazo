#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consulta_anual_sargazo.py

Consulta la base de datos de resultados de sargazo y genera UN UNICO archivo
GeoJSON con todos los POLIGONOS de deteccion de toda la region para un anio dado,
tal cual estan almacenados en la tabla (no se convierten a puntos).

Cada feature es un poligono de sargazo con sus atributos:
clave (id), idpoligono, tile, fecha, fechadia, distcosta_km, area_km2, lugar,
nom_playa. La geometria sale en EPSG:4326 (como esta en la BD).

El valor de area (area_km2) se toma de la tabla de atributos; si viniera nulo se
recalcula a partir de la geometria (ST_Area sobre geography). Con esas areas se
sacan despues las estadisticas de biomasa.

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
        description="Genera un GeoJSON anual de poligonos de toda la region desde la BD de sargazo."
    )
    parser.add_argument("--anio", type=int, required=True,
                        help="Anio a consultar, p.ej. 2024.")
    parser.add_argument("--region", type=int, default=1, choices=[1, 2],
                        help="Region/tabla a consultar: 1=sargazo (default), 2=sargazo_2.")
    parser.add_argument("--salida", type=str,
                        default="/data/output/sentinel2/l2/geojson/sargazo_anual/",
                        help="Carpeta de salida donde se guarda el GeoJSON anual.")
    parser.add_argument("--precision", type=int, default=8,
                        help="Decimales de coordenadas en el GeoJSON (default 8).")
    parser.add_argument("--lote", type=int, default=5000,
                        help="Tamanio del lote para lectura por servidor (default 5000).")
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


def consulta_anual(conect, tabla, region, anio, precision, salida, lote):
    """Escribe el GeoJSON anual de poligonos de forma incremental (streaming)."""

    os.makedirs(salida, exist_ok=True)

    # area_km2: se usa el atributo de la tabla; si es nulo se recalcula con
    # ST_Area sobre geography (geom esta en 4326) y se pasa a km2.
    sql = """
        SELECT
            t.id                                                AS clave,
            t.idpoligono                                        AS idpoligono,
            t.tile                                              AS tile,
            t.fecha                                             AS fecha,
            to_char(t.fechadia, 'YYYY-MM-DD')                   AS fechadia,
            t.distcosta_km                                      AS distcosta_km,
            COALESCE(t.area_km2, ST_Area(t.geom::geography) / 1e6) AS area_km2,
            t.lugar                                             AS lugar,
            t.nom_playa                                         AS nom_playa,
            ST_AsGeoJSON(t.geom, %(prec)s)                      AS geom_json
        FROM {tabla} t
        WHERE EXTRACT(YEAR FROM t.fechadia) = %(anio)s
        ORDER BY t.fechadia, t.idpoligono, t.id
    """.format(tabla=tabla)

    archivo = os.path.join(salida, "sargazo_region{r}_{a}.geojson".format(r=region, a=anio))

    # Cursor del lado del servidor para iterar sin traer todo a memoria.
    cur = conect.cursor(name="cur_anual_sargazo")
    cur.itersize = lote
    cur.execute(sql, {"prec": precision, "anio": anio})

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
                 area_km2, lugar, nom_playa, geom_json) in filas:
                feature = {
                    "type": "Feature",
                    "properties": {
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
                    # geom_json ya es un objeto GeoJSON serializado por PostGIS.
                    "geometry": json.loads(geom_json),
                }
                prefijo = ",\n" if not primero else ""
                bloque.append(prefijo + json.dumps(feature, ensure_ascii=False))
                primero = False
            f.write("".join(bloque))
            n += len(filas)
            print("  ... {} poligonos escritos".format(n))
        f.write("\n]\n}\n")

    cur.close()
    return archivo, n


def _r(valor, ndec):
    if valor is None:
        return None
    return round(float(valor), ndec)


def main():
    args = parse_args()
    tabla = TABLAS_REGION[args.region]

    print("=" * 70)
    print("Consulta anual de sargazo (poligonos)")
    print("  Region : {} (tabla '{}')".format(args.region, tabla))
    print("  Anio   : {}".format(args.anio))
    print("  Salida : {}".format(args.salida))
    print("=" * 70)

    t0 = datetime.datetime.now()
    conect = conexionDB()
    try:
        archivo, n = consulta_anual(conect, tabla, args.region, args.anio,
                                    args.precision, args.salida, args.lote)
    finally:
        conect.close()

    dt = (datetime.datetime.now() - t0).total_seconds()
    print("-" * 70)
    if n == 0:
        print("ADVERTENCIA: no se encontraron detecciones para el anio {} en '{}'."
              .format(args.anio, tabla))
    print("GeoJSON generado : {}".format(archivo))
    print("Total poligonos  : {}".format(n))
    print("Tiempo           : {:.1f} s".format(dt))
    print("Siguiente paso   : limpieza manual de falsos positivos sobre este archivo,")
    print("                   luego correr estadisticas_anual_sargazo.py")


if __name__ == "__main__":
    main()
