#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
estadisticas_municipios_sargazo.py

Paso 2 de 2. Toma el GeoJSON enriquecido que produce consulta_municipios_sargazo.py
(con columnas municipio, banda_costa, dist_costa_m, area_km2, fechadia, ...) y
calcula, para un anio (default 2026):

  1) DIA DE MAYOR ARRIBAZON por municipio: el dia con mayor area de sargazo, con su
     area y biomasa, desglosado tambien por banda de distancia a la costa.
  2) PROMEDIO MENSUAL por municipio: para cada mes, area total / numero de dias con
     observacion en ese mes (promedio diario), y su biomasa equivalente.
  3) TOTAL MENSUAL por municipio (area y biomasa).
  4) Desgloses por banda de costa (0 m playa / 0-10 m / 10-100 m / 100 m-1 km /
     1-10 km / >10 km) por municipio.

Biomasa: misma estimacion que el reporte anual ->
    area_cobertura = area * FC ; biomasa_humeda_ton = area_cobertura_m2 * densidad / 1000
con FC=1.0 y densidad=3.4 kg/m2 (humedo), ambos configurables.

Genera CSV y un JSON resumen en la carpeta de salida, listos para graficar despues.

Uso:
    python3 estadisticas_municipios_sargazo.py --entrada data/2026/sargazo_municipios_2026.geojson

@author: urielm
"""
import os
import json
import argparse
import datetime

import numpy as np
import pandas as pd
import geopandas as gpd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Orden canonico de las bandas de costa (debe coincidir con el script de consulta).
ORDEN_BANDAS = ["0 m (playa)", "0-10 m", "10-100 m", "100 m-1 km", "1-10 km", ">10 km"]
MESES_ES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}


def parse_args():
    p = argparse.ArgumentParser(
        description="Estadisticas de sargazo por municipio, mes y banda de costa.")
    p.add_argument("--entrada", required=True, help="GeoJSON enriquecido (paso 1).")
    p.add_argument("--anio", type=int, default=None, help="Anio (se infiere si se omite).")
    p.add_argument("--salida", default=None, help="Carpeta de salida (default junto a la entrada).")
    p.add_argument("--fc", type=float, default=1.0, help="Fraccion de cobertura (default 1.0).")
    p.add_argument("--densidad", type=float, default=3.4,
                   help="Densidad de biomasa humeda kg/m2 (default 3.4).")
    return p.parse_args()


def biomasa_ton(area_km2, fc, densidad):
    """area(km2) -> biomasa humeda (ton)."""
    return area_km2 * 1e6 * fc * densidad / 1000.0


def carga(entrada, fc, densidad):
    print("Leyendo {} ...".format(entrada))
    gdf = gpd.read_file(entrada)
    df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
    df["area_km2"] = pd.to_numeric(df["area_km2"], errors="coerce").fillna(0.0)
    df["fechadia"] = pd.to_datetime(df["fechadia"], errors="coerce")
    df = df.dropna(subset=["fechadia"])
    df["anio"] = df["fechadia"].dt.year
    df["mes"] = df["fechadia"].dt.month
    df["dia"] = df["fechadia"].dt.date.astype(str)
    if "municipio" not in df.columns:
        raise SystemExit("La entrada no tiene columna 'municipio'. Corre primero el paso 1.")
    df["municipio"] = df["municipio"].fillna("Sin asignar")
    if "banda_costa" not in df.columns:
        df["banda_costa"] = "Sin banda"
    df["biomasa_ton"] = biomasa_ton(df["area_km2"], fc, densidad)
    print("  registros: {:,} | municipios: {} | rango: {} a {}".format(
        len(df), df["municipio"].nunique(),
        df["fechadia"].min().date(), df["fechadia"].max().date()))
    return df


def _orden_bandas(serie):
    cats = [b for b in ORDEN_BANDAS if b in set(serie)]
    cats += [b for b in serie.unique() if b not in cats]
    return cats


def tabla_dia_municipio(df):
    """Area y biomasa por (municipio, dia)."""
    g = df.groupby(["municipio", "dia"], as_index=False).agg(
        n_poligonos=("area_km2", "size"),
        area_km2=("area_km2", "sum"),
        biomasa_ton=("biomasa_ton", "sum"))
    return g.sort_values(["municipio", "area_km2"], ascending=[True, False])


def dia_mayor_arribazon(df):
    """Para cada municipio, el dia de mayor area, con desglose por banda."""
    por_dia = tabla_dia_municipio(df)
    idx = por_dia.groupby("municipio")["area_km2"].idxmax()
    pico = por_dia.loc[idx].reset_index(drop=True)
    pico = pico.rename(columns={"dia": "dia_pico", "n_poligonos": "n_poligonos_pico",
                                "area_km2": "area_km2_pico",
                                "biomasa_ton": "biomasa_ton_pico"})
    # Desglose por banda en el dia pico de cada municipio.
    filas = []
    for _, r in pico.iterrows():
        sub = df[(df["municipio"] == r["municipio"]) & (df["dia"] == r["dia_pico"])]
        for banda, s in sub.groupby("banda_costa"):
            filas.append({"municipio": r["municipio"], "dia_pico": r["dia_pico"],
                          "banda_costa": banda, "n_poligonos": len(s),
                          "area_km2": s["area_km2"].sum(),
                          "biomasa_ton": s["biomasa_ton"].sum()})
    pico_banda = pd.DataFrame(filas)
    return pico.sort_values("area_km2_pico", ascending=False), pico_banda


def total_mensual_municipio(df):
    """Area/biomasa total y promedio diario por (municipio, mes)."""
    # Dias con observacion por (municipio, mes): dias en que el municipio tuvo deteccion.
    dias_obs = (df.groupby(["municipio", "mes"])["dia"].nunique()
                .rename("dias_obs").reset_index())
    tot = df.groupby(["municipio", "mes"], as_index=False).agg(
        n_poligonos=("area_km2", "size"),
        area_km2_total=("area_km2", "sum"),
        biomasa_ton_total=("biomasa_ton", "sum"))
    out = tot.merge(dias_obs, on=["municipio", "mes"], how="left")
    out["area_km2_prom_dia"] = (out["area_km2_total"] / out["dias_obs"]).round(6)
    out["biomasa_ton_prom_dia"] = (out["biomasa_ton_total"] / out["dias_obs"]).round(3)
    out["mes_nom"] = out["mes"].map(MESES_ES)
    out = out.sort_values(["municipio", "mes"])
    cols = ["municipio", "mes", "mes_nom", "dias_obs", "n_poligonos",
            "area_km2_total", "biomasa_ton_total",
            "area_km2_prom_dia", "biomasa_ton_prom_dia"]
    return out[cols]


def por_banda_municipio(df):
    g = df.groupby(["municipio", "banda_costa"], as_index=False).agg(
        n_poligonos=("area_km2", "size"),
        area_km2=("area_km2", "sum"),
        biomasa_ton=("biomasa_ton", "sum"))
    cats = _orden_bandas(g["banda_costa"])
    g["banda_costa"] = pd.Categorical(g["banda_costa"], categories=cats, ordered=True)
    return g.sort_values(["municipio", "banda_costa"])


def totales_municipio(df):
    g = df.groupby("municipio", as_index=False).agg(
        n_poligonos=("area_km2", "size"),
        area_km2=("area_km2", "sum"),
        biomasa_ton=("biomasa_ton", "sum"),
        dias_obs=("dia", "nunique"))
    g["area_km2_prom_dia"] = (g["area_km2"] / g["dias_obs"]).round(6)
    g["biomasa_ton_prom_dia"] = (g["biomasa_ton"] / g["dias_obs"]).round(3)
    return g.sort_values("area_km2", ascending=False)


def _redondea(df, cols, n=4):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].round(n)
    return df


def main():
    args = parse_args()
    salida = args.salida or os.path.dirname(os.path.abspath(args.entrada))
    os.makedirs(salida, exist_ok=True)

    df = carga(args.entrada, args.fc, args.densidad)
    anio = args.anio or int(df["anio"].mode().iloc[0])
    pref = os.path.join(salida, "muni_sargazo_{}".format(anio))

    print("=" * 70)
    print("Estadisticas por municipio - anio {}  (FC={}, densidad={} kg/m2)".format(
        anio, args.fc, args.densidad))
    print("=" * 70)

    tot_muni = _redondea(totales_municipio(df), ["area_km2", "biomasa_ton"])
    pico, pico_banda = dia_mayor_arribazon(df)
    pico = _redondea(pico, ["area_km2_pico", "biomasa_ton_pico"])
    pico_banda = _redondea(pico_banda, ["area_km2", "biomasa_ton"])
    mensual = _redondea(total_mensual_municipio(df),
                        ["area_km2_total", "biomasa_ton_total",
                         "area_km2_prom_dia", "biomasa_ton_prom_dia"])
    banda = _redondea(por_banda_municipio(df), ["area_km2", "biomasa_ton"])

    # Dia de mayor arribazon a nivel region (todos los municipios juntos).
    por_dia_region = (df.groupby("dia", as_index=False)
                      .agg(n_poligonos=("area_km2", "size"),
                           area_km2=("area_km2", "sum"),
                           biomasa_ton=("biomasa_ton", "sum"))
                      .sort_values("area_km2", ascending=False))
    dia_top_region = por_dia_region.iloc[0].to_dict()

    # Dias de mayor arribazon sobre el universo completo de poligonos del paso 1
    # (antes del filtro municipal). Se les agrega biomasa con los mismos FC y
    # densidad. Dos universos:
    #   - 'total': toda la region monitoreada (sin recorte espacial)
    #   - 'zee'  : recortado a la ZEE mexicana (solo aguas de Mexico)
    def _lee_serie_top(sufijo, aviso):
        ruta = os.path.join(salida, "sargazo_{}_serie_diaria_{}.csv".format(sufijo, anio))
        if not os.path.isfile(ruta):
            if aviso:
                print("  [aviso] no se encontro {} ({})".format(os.path.basename(ruta), aviso))
            return None
        s = pd.read_csv(ruta)
        s["biomasa_ton"] = biomasa_ton(s["area_km2"], args.fc, args.densidad).round(2)
        s.sort_values("dia").to_csv(ruta, index=False)  # reescribe con biomasa
        t = s.sort_values("area_km2", ascending=False).iloc[0]
        return {"dia": str(t["dia"]), "area_km2": round(float(t["area_km2"]), 4),
                "biomasa_ton": round(float(t["biomasa_ton"]), 2),
                "n_poligonos": int(t["n_poligonos"])}

    total_top = _lee_serie_top("total", "corre el paso 1 actualizado")
    zee_top = _lee_serie_top("zee", "corre el paso 1 con --zee para el maximo de la ZEE")

    # --- Escritura CSV ---
    tot_muni.to_csv(pref + "_totales_municipio.csv", index=False)
    pico.to_csv(pref + "_dia_mayor_arribazon.csv", index=False)
    pico_banda.to_csv(pref + "_dia_mayor_arribazon_por_banda.csv", index=False)
    mensual.to_csv(pref + "_mensual_municipio.csv", index=False)
    banda.to_csv(pref + "_por_banda_municipio.csv", index=False)
    por_dia_region.to_csv(pref + "_serie_diaria_region.csv", index=False)

    resumen = {
        "anio": anio,
        "archivo_entrada": os.path.abspath(args.entrada),
        "fecha_calculo": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "parametros": {"fc": args.fc, "densidad_kg_m2": args.densidad,
                       "bandas_costa": ORDEN_BANDAS},
        "totales": {
            "n_poligonos": int(len(df)),
            "area_km2": round(float(df["area_km2"].sum()), 4),
            "biomasa_ton": round(float(df["biomasa_ton"].sum()), 2),
            "n_municipios": int(df["municipio"].nunique()),
            "dia_mayor_arribazon_costero": {
                "dia": dia_top_region["dia"],
                "area_km2": round(float(dia_top_region["area_km2"]), 4),
                "biomasa_ton": round(float(dia_top_region["biomasa_ton"]), 2),
                "n_poligonos": int(dia_top_region["n_poligonos"]),
            },
            "dia_mayor_arribazon_zee": zee_top,
            "dia_mayor_arribazon_region_total": total_top,
        },
        "totales_municipio": tot_muni.to_dict(orient="records"),
        "dia_mayor_arribazon": pico.to_dict(orient="records"),
        "mensual_municipio": mensual.to_dict(orient="records"),
        "por_banda_municipio": banda.astype({"banda_costa": str}).to_dict(orient="records"),
        "referencias": [
            "Descloitres et al. (2021) Remote Sensing 13(24), 5106. doi:10.3390/rs13245106",
            "Laval et al. (2023) Remote Sensing 15(4), 1104. doi:10.3390/rs15041104",
        ],
    }
    with open(pref + "_resumen.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    # --- Consola ---
    print("\nDia de mayor arribazon, por universo:")
    if total_top:
        print("  Toda la region monitoreada : {}  ->  {:.3f} km2 | {:,.0f} ton".format(
            total_top["dia"], total_top["area_km2"], total_top["biomasa_ton"]))
    if zee_top:
        print("  ZEE mexicana (Caribe)      : {}  ->  {:.3f} km2 | {:,.0f} ton".format(
            zee_top["dia"], zee_top["area_km2"], zee_top["biomasa_ton"]))
    print("  Costero (municipios, <=50km): {}  ->  {:.3f} km2 | {:,.0f} ton".format(
        dia_top_region["dia"], dia_top_region["area_km2"], dia_top_region["biomasa_ton"]))
    print("\nDia de mayor arribazon por municipio:")
    print(pico[["municipio", "dia_pico", "area_km2_pico", "biomasa_ton_pico"]]
          .to_string(index=False))
    print("\nTotales por municipio:")
    print(tot_muni[["municipio", "area_km2", "biomasa_ton", "dias_obs"]].to_string(index=False))
    print("-" * 70)
    print("Archivos generados en: {}".format(salida))
    for s in ["_totales_municipio", "_dia_mayor_arribazon",
              "_dia_mayor_arribazon_por_banda", "_mensual_municipio",
              "_por_banda_municipio", "_serie_diaria_region", "_resumen.json"]:
        print("  - muni_sargazo_{}{}".format(anio, s if s.endswith("json") else s + ".csv"))
    if total_top:
        print("  - sargazo_total_serie_diaria_{}.csv (toda la region monitoreada)".format(anio))
    if zee_top:
        print("  - sargazo_zee_serie_diaria_{}.csv (ZEE mexicana Caribe)".format(anio))


if __name__ == "__main__":
    main()
