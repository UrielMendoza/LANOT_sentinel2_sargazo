#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
figuras_municipios_sargazo.py

Genera las figuras (graficas + mapas) del reporte de sargazo POR MUNICIPIO a
partir de los archivos que produce estadisticas_municipios_sargazo.py y del
GeoJSON enriquecido de consulta_municipios_sargazo.py.

Mismo estilo cientifico que figuras_anual_sargazo.py (del cual reutiliza los
helpers de mapa: linea de ZEE, barra de escala, flecha de norte, paleta jet).
Pensado para correr en LOCAL. Entorno sugerido: conda 'sargazo_planet'.

    conda run -n sargazo_planet python figuras_municipios_sargazo.py --anio 2026

Entradas por defecto (carpeta data/<anio>/):
    muni_sargazo_<anio>_resumen.json
    muni_sargazo_<anio>_totales_municipio.csv
    muni_sargazo_<anio>_dia_mayor_arribazon.csv
    muni_sargazo_<anio>_dia_mayor_arribazon_por_banda.csv
    muni_sargazo_<anio>_mensual_municipio.csv
    muni_sargazo_<anio>_por_banda_municipio.csv
    muni_sargazo_<anio>_serie_diaria_region.csv
    sargazo_municipios_<anio>.geojson           (poligonos enriquecidos)
    data/limites/municipios_QR.geojson          (limites municipales)

@author: urielm
"""
import os
import json
import argparse
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.colors import LogNorm
import seaborn as sns
import geopandas as gpd

# Reutiliza estilo y helpers de mapa del script anual.
import figuras_anual_sargazo as fa

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REGION = "Caribe Mexicano (Quintana Roo)"
DPI = 220

# Colores y orden de bandas (consistente con consulta/estadisticas).
ORDEN_BANDAS = ["0 m (playa)", "0-10 m", "10-100 m", "100 m-1 km", "1-10 km", ">10 km"]
PAL_BANDAS = {
    "0 m (playa)": "#8c510a", "0-10 m": "#d8b365", "10-100 m": "#f6e8c3",
    "100 m-1 km": "#c7eae5", "1-10 km": "#5ab4ac", ">10 km": "#01665e",
}
COL_AREA = fa.COL_SARGAZO
COL_BIO = fa.COL_BIOMASA


def parse_args():
    p = argparse.ArgumentParser(description="Figuras del reporte de sargazo por municipio.")
    p.add_argument("--anio", type=int, default=2026, help="Anio (default 2026).")
    p.add_argument("--datadir", default=None, help="Carpeta con los CSV/JSON (default data/<anio>).")
    p.add_argument("--geojson", default=None, help="GeoJSON enriquecido de poligonos.")
    p.add_argument("--municipios", default=fa.os.path.join(RAIZ, "data", "limites", "municipios_QR.geojson"),
                   help="GeoJSON de limites municipales.")
    p.add_argument("--outdir", default=None, help="Carpeta de salida (default <datadir>/figuras).")
    p.add_argument("--sin-mapas", action="store_true", help="Omite los mapas (no lee geojson pesado).")
    p.add_argument("--hex-gridsize", type=int, default=170, help="Resolucion del hexbin.")
    p.add_argument("--zee", default=fa.DEF_ZEE, help="GeoJSON de la ZEE de Mexico.")
    p.add_argument("--paises", default=fa.DEF_PAISES, help="GeoJSON de paises (Natural Earth).")
    return p.parse_args()


def _csv(datadir, anio, suf):
    return os.path.join(datadir, "muni_sargazo_{}_{}.csv".format(anio, suf))


def _orden_muni(df, col_val):
    """Devuelve municipios ordenados por una metrica (desc)."""
    return (df.groupby("municipio")[col_val].sum()
            .sort_values(ascending=False).index.tolist())


# ------------------------------------------------------------------------------
# GRAFICAS
# ------------------------------------------------------------------------------
def fig_ranking_total(tot, anio, outdir):
    df = tot.sort_values("area_km2", ascending=True)
    fig, ax1 = plt.subplots(figsize=(11, 7))
    y = np.arange(len(df))
    ax1.barh(y - 0.2, df["area_km2"], height=0.4, color=COL_AREA, label="Área (km²)")
    ax1.set_yticks(y)
    ax1.set_yticklabels(df["municipio"])
    ax1.set_xlabel("Área de sargazo (km$^2$)", color=COL_AREA)
    ax1.tick_params(axis="x", labelcolor=COL_AREA)
    for i, v in enumerate(df["area_km2"]):
        ax1.text(v, y[i] - 0.2, " {:.1f}".format(v), va="center", fontsize=8, color=COL_AREA)

    ax2 = ax1.twiny()
    ax2.barh(y + 0.2, df["biomasa_ton"], height=0.4, color=COL_BIO, label="Biomasa (ton)")
    ax2.set_xlabel("Biomasa húmeda (ton)", color=COL_BIO)
    ax2.tick_params(axis="x", labelcolor=COL_BIO)
    ax2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    ax1.set_title("Sargazo total por municipio – {} ({})\nárea detectada y biomasa estimada".format(
        REGION, anio))
    fig.tight_layout()
    return fa._guarda(fig, outdir, "01_ranking_municipios_area_biomasa.png")


def fig_dia_arribazon(pico, anio, outdir):
    df = pico.sort_values("area_km2_pico", ascending=True)
    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(df["municipio"], df["area_km2_pico"], color=COL_AREA,
                   edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Área de sargazo en el día de mayor arribazón (km$^2$)")
    ax.set_title("Día de mayor arribazón por municipio – {} ({})".format(REGION, anio))
    for i, (v, d) in enumerate(zip(df["area_km2_pico"], df["dia_pico"])):
        ax.text(v, i, "  {:.2f} km²  ({})".format(v, d), va="center", fontsize=8)
    ax.margins(x=0.18)
    fig.tight_layout()
    return fa._guarda(fig, outdir, "02_dia_mayor_arribazon_municipio.png")


def fig_serie_diaria(serie, resumen, anio, outdir):
    df = serie.copy()
    df["dia_dt"] = pd.to_datetime(df["dia"], errors="coerce")
    df = df.sort_values("dia_dt")
    fig, ax1 = plt.subplots(figsize=(12, 5.8))
    ax1.fill_between(df["dia_dt"], df["area_km2"], color=COL_AREA, alpha=0.25)
    ax1.plot(df["dia_dt"], df["area_km2"], color=COL_AREA, lw=1.8, marker="o", ms=3)
    ax1.set_ylabel("Área de sargazo (km$^2$)", color=COL_AREA)
    ax1.tick_params(axis="y", labelcolor=COL_AREA)
    ax1.set_xlabel("Fecha")
    # Marca el dia pico regional.
    top = resumen["totales"]["dia_mayor_arribazon_region"]
    dpt = pd.to_datetime(top["dia"])
    ax1.axvline(dpt, color=COL_BIO, ls="--", lw=1.8)
    ax1.text(dpt, ax1.get_ylim()[1] * 0.92,
             "  máx: {} ({:.1f} km²)".format(top["dia"], top["area_km2"]),
             color=COL_BIO, fontsize=9)
    ax1.set_title("Serie diaria de sargazo – {} ({})".format(REGION, anio))
    fig.tight_layout()
    return fa._guarda(fig, outdir, "03_serie_diaria_region.png")


def fig_serie_diaria_zee(datadir, resumen, anio, outdir):
    """Serie diaria de sargazo en TODA la ZEE Caribe, marcando el dia de mayor
    arribazon. Si existe, superpone la serie costera (municipios) para comparar."""
    zee_csv = os.path.join(datadir, "sargazo_zee_serie_diaria_{}.csv".format(anio))
    if not os.path.isfile(zee_csv):
        print("  [aviso] no hay serie diaria de la ZEE; omito figura ZEE")
        return None
    z = pd.read_csv(zee_csv)
    z["dia_dt"] = pd.to_datetime(z["dia"], errors="coerce")
    z = z.sort_values("dia_dt")
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.fill_between(z["dia_dt"], z["area_km2"], color="#1f6f8b", alpha=0.25)
    ax.plot(z["dia_dt"], z["area_km2"], color="#1f6f8b", lw=1.8, marker="o", ms=3,
            label="Toda la ZEE (Caribe)")
    # Serie costera (municipios) para comparar.
    sc = os.path.join(datadir, "muni_sargazo_{}_serie_diaria_region.csv".format(anio))
    if os.path.isfile(sc):
        s = pd.read_csv(sc)
        s["dia_dt"] = pd.to_datetime(s["dia"], errors="coerce")
        s = s.sort_values("dia_dt")
        ax.plot(s["dia_dt"], s["area_km2"], color=COL_AREA, lw=1.5, ls="--",
                marker="s", ms=2.5, label="Costero (municipios)")
    top = resumen["totales"].get("dia_mayor_arribazon_zee")
    if top:
        dpt = pd.to_datetime(top["dia"])
        ax.axvline(dpt, color=COL_BIO, ls="--", lw=1.8)
        ax.text(dpt, ax.get_ylim()[1] * 0.92,
                "  máx ZEE: {} ({:.1f} km²)".format(top["dia"], top["area_km2"]),
                color=COL_BIO, fontsize=9)
    ax.set_ylabel("Área de sargazo (km$^2$)")
    ax.set_xlabel("Fecha")
    ax.set_title("Serie diaria de sargazo en la ZEE del Caribe Mexicano ({})".format(anio))
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    return fa._guarda(fig, outdir, "13_serie_diaria_zee.png")


def fig_heatmap_mensual(mensual, anio, outdir, valor, titulo, etiqueta, nombre):
    df = mensual.copy()
    orden = _orden_muni(df, valor)
    piv = df.pivot_table(index="municipio", columns="mes", values=valor, aggfunc="sum")
    piv = piv.reindex(orden)
    piv.columns = [fa.MESES_ES.get("{:02d}".format(c), c) for c in piv.columns]
    fig, ax = plt.subplots(figsize=(12, 6.5))
    sns.heatmap(piv, cmap="YlOrRd", annot=True, fmt=".1f", linewidths=0.5,
                linecolor="white", cbar_kws={"label": etiqueta}, ax=ax)
    ax.set_xlabel("Mes")
    ax.set_ylabel("")
    ax.set_title(titulo.format(REGION, anio))
    fig.tight_layout()
    return fa._guarda(fig, outdir, nombre)


def fig_banda_municipio(banda, anio, outdir, valor, etiqueta, nombre, titulo):
    df = banda.copy()
    df["banda_costa"] = pd.Categorical(df["banda_costa"], categories=ORDEN_BANDAS, ordered=True)
    orden = _orden_muni(df, valor)
    piv = (df.pivot_table(index="municipio", columns="banda_costa", values=valor,
                          aggfunc="sum", observed=False)
           .reindex(orden))
    piv = piv[[b for b in ORDEN_BANDAS if b in piv.columns]]
    fig, ax = plt.subplots(figsize=(12, 7))
    bottom = np.zeros(len(piv))
    for b in piv.columns:
        ax.barh(piv.index, piv[b].values, left=bottom, label=b,
                color=PAL_BANDAS.get(b, "#999999"), edgecolor="white", linewidth=0.4)
        bottom += np.nan_to_num(piv[b].values)
    ax.set_xlabel(etiqueta)
    ax.set_title(titulo.format(REGION, anio))
    ax.legend(title="Distancia a la costa", fontsize=8, title_fontsize=9,
              loc="lower right", framealpha=0.9)
    ax.invert_yaxis()
    fig.tight_layout()
    return fa._guarda(fig, outdir, nombre)


def fig_banda_region(banda, anio, outdir):
    df = banda.groupby("banda_costa", as_index=False).agg(
        area_km2=("area_km2", "sum"), biomasa_ton=("biomasa_ton", "sum"))
    df["banda_costa"] = pd.Categorical(df["banda_costa"], categories=ORDEN_BANDAS, ordered=True)
    df = df.sort_values("banda_costa")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    cols = [PAL_BANDAS.get(b, "#999999") for b in df["banda_costa"]]
    ax.bar(df["banda_costa"].astype(str), df["area_km2"], color=cols,
           edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Distancia a la costa")
    ax.set_ylabel("Área de sargazo (km$^2$)")
    ax.set_title("Sargazo por banda de distancia a la costa – {} ({})".format(REGION, anio))
    total = df["area_km2"].sum()
    for i, v in enumerate(df["area_km2"]):
        ax.text(i, v, "{:.0f}%".format(100 * v / total), ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    return fa._guarda(fig, outdir, "08_sargazo_por_banda_region.png")


# ------------------------------------------------------------------------------
# MAPAS
# ------------------------------------------------------------------------------
def _municipios_centroides(muni):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        c = muni.geometry.representative_point()
    return c


def fig_mapa_coropletico(muni, tot, anio, outdir, valor, etiqueta, nombre, titulo):
    m = muni.merge(tot, left_on="NOMGEO", right_on="municipio", how="left")
    fig, ax = plt.subplots(figsize=(10, 11))
    ax.set_facecolor(fa.COL_OCEANO)
    m.plot(column=valor, cmap="YlOrRd", legend=True, ax=ax,
           edgecolor="#555555", linewidth=0.6, missing_kwds={"color": "#eeeeee"},
           legend_kwds={"label": etiqueta, "shrink": 0.5})
    if fa._CTX["zee"] is not None:
        fa._CTX["zee"].boundary.plot(ax=ax, color=fa.COL_ZEE, lw=1.3, zorder=5)
    # Etiquetas de municipio
    cent = _municipios_centroides(m)
    for x, y, nom in zip(cent.x, cent.y, m["NOMGEO"]):
        ax.text(x, y, nom, fontsize=6.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.6))
    minx, miny, maxx, maxy = m.total_bounds
    ax.set_xlim(minx - 0.1, maxx + 0.5)
    ax.set_ylim(miny - 0.1, maxy + 0.1)
    fa._aspecto(ax, (miny + maxy) / 2)
    ax.set_xlabel("Longitud"); ax.set_ylabel("Latitud")
    ax.set_title(titulo.format(REGION, anio))
    fa._barra_escala(ax, km=50)
    fa._flecha_norte(ax)
    fig.tight_layout()
    return fa._guarda(fig, outdir, nombre)


def fig_mapa_densidad(gdf, muni, anio, outdir, gridsize):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cent = gdf.geometry.representative_point()
    lon, lat = cent.x.values, cent.y.values
    area = pd.to_numeric(gdf["area_km2"], errors="coerce").fillna(0).values
    lon_min, lon_max = float(np.min(lon)), float(np.max(lon))
    lat_min, lat_max = float(np.min(lat)), float(np.max(lat))

    fig, ax = plt.subplots(figsize=(10, 11))
    ax.set_facecolor(fa.COL_OCEANO)
    muni.boundary.plot(ax=ax, color="#666666", lw=0.5, zorder=2)
    hb = ax.hexbin(lon, lat, C=area, reduce_C_function=np.sum, gridsize=gridsize,
                   cmap=fa.CMAP_DENS, mincnt=1, norm=LogNorm(), linewidths=0.0, zorder=3)
    cb = fig.colorbar(hb, ax=ax, shrink=0.55, pad=0.02)
    cb.set_label("Área de sargazo por celda (km$^2$)")
    if fa._CTX["zee"] is not None:
        fa._CTX["zee"].boundary.plot(ax=ax, color=fa.COL_ZEE, lw=1.3, zorder=5)
    ax.set_xlim(lon_min - 0.15, lon_max + 0.4)
    ax.set_ylim(lat_min - 0.15, lat_max + 0.15)
    fa._aspecto(ax, (lat_min + lat_max) / 2)
    ax.set_xlabel("Longitud"); ax.set_ylabel("Latitud")
    ax.set_title("Mapa de densidad de sargazo – {} ({})".format(REGION, anio))
    ax.grid(True, ls=":", lw=0.5, alpha=0.4)
    fa._barra_escala(ax, km=50)
    fa._flecha_norte(ax)
    fig.tight_layout()
    return fa._guarda(fig, outdir, "11_mapa_densidad_municipios.png")


# ------------------------------------------------------------------------------
def main():
    args = parse_args()
    datadir = args.datadir or os.path.join(RAIZ, "data", str(args.anio))
    outdir = args.outdir or os.path.join(datadir, "figuras")
    os.makedirs(outdir, exist_ok=True)
    fa.estilo()

    print("=" * 70)
    print("Figuras por municipio de sargazo {}".format(args.anio))
    print("  Datos  : {}".format(datadir))
    print("  Salida : {}".format(outdir))
    print("=" * 70)

    with open(os.path.join(datadir, "muni_sargazo_{}_resumen.json".format(args.anio)),
              encoding="utf-8") as f:
        resumen = json.load(f)
    tot = pd.read_csv(_csv(datadir, args.anio, "totales_municipio"))
    pico = pd.read_csv(_csv(datadir, args.anio, "dia_mayor_arribazon"))
    mensual = pd.read_csv(_csv(datadir, args.anio, "mensual_municipio"))
    banda = pd.read_csv(_csv(datadir, args.anio, "por_banda_municipio"))
    serie = pd.read_csv(_csv(datadir, args.anio, "serie_diaria_region"))

    print("\n>> Graficas")
    fig_ranking_total(tot, args.anio, outdir)
    fig_dia_arribazon(pico, args.anio, outdir)
    fig_serie_diaria(serie, resumen, args.anio, outdir)
    fig_serie_diaria_zee(datadir, resumen, args.anio, outdir)
    fig_heatmap_mensual(mensual, args.anio, outdir, "area_km2_total",
                        "Área mensual de sargazo por municipio – {} ({})",
                        "Área (km²)", "04_mensual_area_municipio.png")
    fig_heatmap_mensual(mensual, args.anio, outdir, "biomasa_ton_total",
                        "Biomasa mensual de sargazo por municipio – {} ({})",
                        "Biomasa (ton)", "05_mensual_biomasa_municipio.png")
    fig_heatmap_mensual(mensual, args.anio, outdir, "area_km2_prom_dia",
                        "Promedio diario mensual de sargazo por municipio – {} ({})",
                        "Área promedio diaria (km²)", "06_mensual_promedio_municipio.png")
    fig_banda_municipio(banda, args.anio, outdir, "area_km2",
                        "Área de sargazo (km$^2$)", "07_banda_area_municipio.png",
                        "Sargazo por banda de costa y municipio – {} ({})")
    fig_banda_region(banda, args.anio, outdir)
    fig_banda_municipio(banda, args.anio, outdir, "biomasa_ton",
                        "Biomasa húmeda (ton)", "09_banda_biomasa_municipio.png",
                        "Biomasa por banda de costa y municipio – {} ({})")

    if not args.sin_mapas:
        print("\n>> Mapas")
        fa.carga_contexto(args.zee, args.paises)
        muni = gpd.read_file(args.municipios).to_crs(4326)
        fig_mapa_coropletico(muni, tot, args.anio, outdir, "area_km2",
                             "Área de sargazo (km²)", "10_mapa_area_municipio.png",
                             "Área total de sargazo por municipio – {} ({})")
        fig_mapa_coropletico(muni, tot, args.anio, outdir, "biomasa_ton",
                             "Biomasa húmeda (ton)", "12_mapa_biomasa_municipio.png",
                             "Biomasa total de sargazo por municipio – {} ({})")
        geojson = args.geojson or os.path.join(datadir, "sargazo_municipios_{}.geojson".format(args.anio))
        if os.path.isfile(geojson):
            print("Leyendo GeoJSON de poligonos...")
            gdf = gpd.read_file(geojson).to_crs(4326)
            print("  poligonos: {:,}".format(len(gdf)))
            fig_mapa_densidad(gdf, muni, args.anio, outdir, args.hex_gridsize)
        else:
            print("  [aviso] no se encontro {} (omito mapa de densidad)".format(geojson))

    print("-" * 70)
    print("Figuras generadas en: {}".format(outdir))


if __name__ == "__main__":
    main()
