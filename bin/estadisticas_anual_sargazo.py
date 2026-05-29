#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
estadisticas_anual_sargazo.py

Toma el GeoJSON anual de POLIGONOS de sargazo YA LIMPIO (sin falsos positivos)
que produce consulta_anual_sargazo.py y calcula estadisticas anuales para
reporte, incluida una estimacion de biomasa de sargazo en oceano.

------------------------------------------------------------------------------
ESTIMACION DE BIOMASA (Sentinel-2 MSI, sargazo en oceano)
------------------------------------------------------------------------------
La deteccion de este flujo es BINARIA: cada feature es un poligono vectorial de
sargazo con su area (area_km2). No se conserva el valor de AFAI, por lo que la
fraccion de cobertura (FC) no se recupera; se aplica como un factor configurable
(--fc) sobre el area detectada.

    area_presencia  = suma de area_km2 de los poligonos
    area_cobertura  = area_presencia * FC
    biomasa_humeda  = area_cobertura * densidad_tapete_puro

Donde:
  - FC: fraccion de cobertura del poligono detectado. Para Sentinel-2 MSI en
    oceano los trabajos recientes convergen en FC = AFAI_desv / K con K ~ 0.08;
    debe recalibrarse localmente. Como la deteccion aqui es binaria, FC se
    entrega como parametro (--fc, default 1.0) y ademas se reporta una tabla de
    escenarios (0.10 / 0.20 / 0.40 / 1.0) para el reporte.
  - densidad_tapete_puro: kg de sargazo humedo por m2 de cobertura plena
    (--densidad, default 3.4 kg/m2, valor de literatura para tapetes flotantes).

El area se toma de la columna area_km2; si falta, se recalcula a partir de la
geometria (reproyectada a un CRS metrico).

Referencias:
  Descloitres et al. (2021) Remote Sensing 13(24), 5106. doi:10.3390/rs13245106
  Laval et al. (2023) Remote Sensing 15(4), 1104. doi:10.3390/rs15041104

Uso:
    python3 estadisticas_anual_sargazo.py --entrada sargazo_region1_2024_limpio.geojson
    python3 estadisticas_anual_sargazo.py --entrada limpio.geojson --fc 0.2 --densidad 3.4

@author: urielm
"""
import os
import json
import argparse
import datetime

import numpy as np
import pandas as pd
import geopandas as gpd


# Escenarios de FC reportados siempre (ademas del --fc elegido).
FC_ESCENARIOS = [0.10, 0.20, 0.40, 1.00]

# Bins de distancia a costa (km) para el reporte.
BINS_COSTA = [0, 1, 5, 20, np.inf]
ETIQ_COSTA = ["0-1 km", "1-5 km", "5-20 km", ">20 km"]

# CRS metrico para recalcular areas si hiciera falta (UTM 16N, region zona 16).
CRS_METRICO = 32616


def parse_args():
    parser = argparse.ArgumentParser(
        description="Estadisticas anuales y biomasa de sargazo a partir del GeoJSON de poligonos limpio."
    )
    parser.add_argument("--entrada", type=str, required=True,
                        help="GeoJSON anual de poligonos YA LIMPIO de falsos positivos.")
    parser.add_argument("--salida", type=str,
                        default="/data/output/sentinel2/l2/estadisticas/",
                        help="Carpeta de salida para los reportes.")
    parser.add_argument("--anio", type=int, default=None,
                        help="Anio del reporte (si se omite, se infiere de fechadia).")
    parser.add_argument("--fc", type=float, default=1.0,
                        help="Fraccion de cobertura aplicada al area detectada (default 1.0).")
    parser.add_argument("--densidad", type=float, default=3.4,
                        help="Densidad de biomasa humeda de tapete pleno (kg/m2, default 3.4).")
    parser.add_argument("--recalcula-area", action="store_true",
                        help="Ignora area_km2 y recalcula el area desde la geometria.")
    return parser.parse_args()


def carga(entrada, recalcula_area):
    gdf = gpd.read_file(entrada)

    if "fechadia" not in gdf.columns:
        raise ValueError("El archivo no tiene la columna 'fechadia'.")

    # Area por poligono: atributo area_km2, o recalculada desde la geometria.
    if recalcula_area or "area_km2" not in gdf.columns or gdf["area_km2"].isna().all():
        gdf["area_km2"] = _area_desde_geometria(gdf)
    else:
        gdf["area_km2"] = pd.to_numeric(gdf["area_km2"], errors="coerce")
        faltantes = gdf["area_km2"].isna()
        if faltantes.any():
            gdf.loc[faltantes, "area_km2"] = _area_desde_geometria(gdf.loc[faltantes])

    df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
    df["fechadia"] = pd.to_datetime(df["fechadia"], errors="coerce")
    df = df.dropna(subset=["fechadia"])
    df["mes"] = df["fechadia"].dt.month
    df["mes_nom"] = df["fechadia"].dt.strftime("%Y-%m")

    if "distcosta_km" in df.columns:
        df["distcosta_km"] = pd.to_numeric(df["distcosta_km"], errors="coerce")
    for col in ["tile", "lugar", "nom_playa", "idpoligono"]:
        if col not in df.columns:
            df[col] = None
    return df


def _area_desde_geometria(gdf):
    proj = gdf.to_crs(epsg=CRS_METRICO)
    return proj.geometry.area / 1e6  # m2 -> km2


def biomasa(area_cobertura_m2, densidad_kg_m2):
    """Devuelve biomasa humeda en toneladas."""
    return area_cobertura_m2 * densidad_kg_m2 / 1000.0


def resumen_grupo(df, fc, densidad):
    """Calcula metricas agregadas de un (sub)conjunto de poligonos."""
    area_presencia_km2 = float(df["area_km2"].sum(skipna=True))
    area_cobertura_km2 = area_presencia_km2 * fc
    area_cobertura_m2 = area_cobertura_km2 * 1e6
    return {
        "n_poligonos": int(len(df)),
        "area_presencia_km2": round(area_presencia_km2, 4),
        "area_cobertura_km2": round(area_cobertura_km2, 4),
        "biomasa_humeda_ton": round(biomasa(area_cobertura_m2, densidad), 2),
    }


def tabla_por(df, col, fc, densidad, etiqueta=None):
    filas = []
    for val, sub in df.groupby(col, dropna=False):
        r = resumen_grupo(sub, fc, densidad)
        r[etiqueta or col] = val
        filas.append(r)
    out = pd.DataFrame(filas)
    if not out.empty:
        cols = [etiqueta or col] + [c for c in out.columns if c != (etiqueta or col)]
        out = out[cols].sort_values((etiqueta or col)).reset_index(drop=True)
    return out


def main():
    args = parse_args()

    if not os.path.isfile(args.entrada):
        raise SystemExit("No existe el archivo de entrada: {}".format(args.entrada))

    print("=" * 70)
    print("Estadisticas anuales de sargazo (poligonos)")
    print("  Entrada  : {}".format(args.entrada))
    print("  FC       : {}".format(args.fc))
    print("  Densidad : {} kg/m2 (humedo)".format(args.densidad))
    print("=" * 70)

    df = carga(args.entrada, args.recalcula_area)
    anio = args.anio if args.anio else int(df["fechadia"].dt.year.mode().iloc[0])
    os.makedirs(args.salida, exist_ok=True)
    base_nom = "estadisticas_sargazo_{}".format(anio)

    # --- Metricas globales --------------------------------------------------
    glob = resumen_grupo(df, args.fc, args.densidad)
    area_poligono_media = round(float(df["area_km2"].mean(skipna=True)), 4)
    area_poligono_max = round(float(df["area_km2"].max(skipna=True)), 4)
    n_dias_obs = int(df["fechadia"].dt.date.nunique())
    n_pasadas = int(df["fecha"].nunique()) if "fecha" in df.columns else None

    # --- Tablas por categoria ----------------------------------------------
    por_mes = tabla_por(df, "mes_nom", args.fc, args.densidad, etiqueta="mes")
    por_tile = tabla_por(df, "tile", args.fc, args.densidad)
    por_lugar = tabla_por(df, "lugar", args.fc, args.densidad)

    # Por distancia a costa.
    if "distcosta_km" in df.columns and df["distcosta_km"].notna().any():
        df["_bin_costa"] = pd.cut(df["distcosta_km"], bins=BINS_COSTA,
                                  labels=ETIQ_COSTA, right=False)
        por_costa = tabla_por(df, "_bin_costa", args.fc, args.densidad,
                              etiqueta="dist_costa")
    else:
        por_costa = pd.DataFrame()

    # Mes pico (mayor area de presencia).
    mes_pico = None
    if not por_mes.empty:
        mes_pico = por_mes.loc[por_mes["area_presencia_km2"].idxmax(), "mes"]

    # --- Escenarios de FC para el reporte -----------------------------------
    escenarios = []
    fcs = sorted(set(FC_ESCENARIOS + [args.fc]))
    for fc in fcs:
        r = resumen_grupo(df, fc, args.densidad)
        r["fc"] = fc
        r["es_seleccionado"] = (abs(fc - args.fc) < 1e-9)
        escenarios.append(r)
    df_escenarios = pd.DataFrame(escenarios)[
        ["fc", "es_seleccionado", "n_poligonos", "area_presencia_km2",
         "area_cobertura_km2", "biomasa_humeda_ton"]]

    # --- Ensamble del resumen ----------------------------------------------
    resumen = {
        "anio": anio,
        "archivo_entrada": os.path.abspath(args.entrada),
        "fecha_calculo": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "parametros": {
            "fc": args.fc,
            "densidad_kg_m2": args.densidad,
            "area_recalculada": bool(args.recalcula_area),
        },
        "totales": {
            "n_poligonos": glob["n_poligonos"],
            "area_presencia_km2": glob["area_presencia_km2"],
            "area_cobertura_km2": glob["area_cobertura_km2"],
            "biomasa_humeda_ton": glob["biomasa_humeda_ton"],
            "area_poligono_media_km2": area_poligono_media,
            "area_poligono_max_km2": area_poligono_max,
            "n_dias_con_observacion": n_dias_obs,
            "n_pasadas": n_pasadas,
            "mes_pico": mes_pico,
        },
        "escenarios_fc": df_escenarios.to_dict(orient="records"),
        "por_mes": por_mes.to_dict(orient="records"),
        "por_tile": por_tile.to_dict(orient="records"),
        "por_lugar": por_lugar.to_dict(orient="records"),
        "por_distancia_costa": por_costa.to_dict(orient="records") if not por_costa.empty else [],
        "referencias": [
            "Descloitres et al. (2021) Remote Sensing 13(24), 5106. doi:10.3390/rs13245106",
            "Laval et al. (2023) Remote Sensing 15(4), 1104. doi:10.3390/rs15041104",
        ],
    }

    # --- Escritura de salidas ----------------------------------------------
    ruta_json = os.path.join(args.salida, base_nom + "_resumen.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    por_mes.to_csv(os.path.join(args.salida, base_nom + "_por_mes.csv"), index=False)
    por_tile.to_csv(os.path.join(args.salida, base_nom + "_por_tile.csv"), index=False)
    por_lugar.to_csv(os.path.join(args.salida, base_nom + "_por_lugar.csv"), index=False)
    df_escenarios.to_csv(os.path.join(args.salida, base_nom + "_escenarios_fc.csv"), index=False)
    if not por_costa.empty:
        por_costa.to_csv(os.path.join(args.salida, base_nom + "_por_distancia_costa.csv"), index=False)

    # --- Resumen en consola -------------------------------------------------
    print("\nRESUMEN ANIO {}".format(anio))
    print("-" * 70)
    print("  Poligonos detectados      : {:,}".format(glob["n_poligonos"]))
    print("  Area de presencia         : {:,.4f} km2".format(glob["area_presencia_km2"]))
    print("  Area de cobertura (FC={})  : {:,.4f} km2".format(args.fc, glob["area_cobertura_km2"]))
    print("  Biomasa humeda            : {:,.2f} ton".format(glob["biomasa_humeda_ton"]))
    print("  Area media por poligono   : {:,.4f} km2".format(area_poligono_media))
    print("  Dias con observacion      : {}".format(n_dias_obs))
    print("  Mes pico                  : {}".format(mes_pico))
    print("\nEscenarios de biomasa segun FC:")
    print(df_escenarios.to_string(index=False))
    print("-" * 70)
    print("Reportes guardados en: {}".format(args.salida))
    print("  - {}_resumen.json".format(base_nom))
    print("  - {}_por_mes.csv / _por_tile.csv / _por_lugar.csv / _escenarios_fc.csv".format(base_nom))


if __name__ == "__main__":
    main()
