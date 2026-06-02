#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
figuras_anual_sargazo.py

Genera las figuras (graficas + mapas) para el reporte anual de sargazo a partir
de las estadisticas producidas por estadisticas_anual_sargazo.py y del GeoJSON
de poligonos LIMPIO.

Estilo cientifico con seaborn/matplotlib. Pensado para correr en local (no en el
servidor). Entorno sugerido: conda 'sargazo_planet'
(requiere: seaborn, matplotlib, geopandas, numpy, pandas, shapely).

    conda run -n sargazo_planet python figuras_anual_sargazo.py

Por defecto trabaja sobre:
    data/2025/estadisticas_sargazo_2025_resumen.json   (estadisticas)
    data/2025/sargazo_region1_2025_limpio_zeem.geojson (poligonos limpios)
y escribe las figuras en data/2025/figuras/.

Uso:
    python figuras_anual_sargazo.py
    python figuras_anual_sargazo.py --resumen <ruta.json> --geojson <ruta.geojson> --outdir <carpeta>
    python figuras_anual_sargazo.py --sin-mapas      # solo graficas de estadisticas

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
from matplotlib.patches import Rectangle
import seaborn as sns

import geopandas as gpd


# ------------------------------------------------------------------------------
# Configuracion de rutas por defecto (relativas a la raiz del repo)
# ------------------------------------------------------------------------------
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_RESUMEN = os.path.join(RAIZ, "data", "2025", "estadisticas_sargazo_2025_resumen.json")
DEF_GEOJSON = os.path.join(RAIZ, "data", "2025", "sargazo_region1_2025_limpio_zeem.geojson")
DEF_OUTDIR = os.path.join(RAIZ, "data", "2025", "figuras")

# Capas de contexto (limites)
# ZEE de Mexico provista por el usuario (fuente INEGI).
DEF_ZEE = os.path.join(RAIZ, "data", "2025", "zona_economica_esclusiva_mexicana.geojson")
DEF_PAISES = os.path.join(RAIZ, "data", "limites", "ne_50m_admin_0_countries.geojson")

# Color institucional / de sargazo
COL_SARGAZO = "#2a7f3e"
COL_BIOMASA = "#b5651d"
COL_ZEE = "#08306b"      # linea de la Zona Economica Exclusiva
COL_TIERRA = "#7c7c7c"   # relleno de tierra (gris oscuro continental)
COL_TIERRA_BORDE = "#4d4d4d"
COL_OCEANO = "#ffffff"   # fondo (sin relleno de tierra)
CMAP_DENS = "jet"        # paleta jet (azul->cian->verde->amarillo->rojo)

# No rellenar el shapefile de paises; en los mapas solo se dibuja la linea de la ZEE.
DIBUJAR_TIERRA = False

# Region de analisis (para titulos)
REGION = "ZEEM Caribe Mexicano"
DPI = 220

MESES_ES = {
    "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr", "05": "May", "06": "Jun",
    "07": "Jul", "08": "Ago", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic",
}

# Cache de capas de contexto (se cargan una sola vez)
_CTX = {"zee": None, "paises": None, "cargado": False}


def parse_args():
    p = argparse.ArgumentParser(description="Figuras del reporte anual de sargazo.")
    p.add_argument("--resumen", default=DEF_RESUMEN, help="JSON de estadisticas.")
    p.add_argument("--geojson", default=DEF_GEOJSON, help="GeoJSON de poligonos limpios.")
    p.add_argument("--outdir", default=DEF_OUTDIR, help="Carpeta de salida de figuras.")
    p.add_argument("--sin-mapas", action="store_true",
                   help="No genera los mapas (omite leer el GeoJSON pesado).")
    p.add_argument("--hex-gridsize", type=int, default=140,
                   help="Resolucion del hexbin de los mapas (default 140).")
    p.add_argument("--zee", default=DEF_ZEE,
                   help="GeoJSON de la Zona Economica Exclusiva de Mexico.")
    p.add_argument("--paises", default=DEF_PAISES,
                   help="GeoJSON de limites de paises (Natural Earth).")
    return p.parse_args()


def estilo():
    sns.set_theme(style="whitegrid", context="talk", font_scale=0.9)
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "axes.titleweight": "bold",
        "axes.edgecolor": "#444444",
        "axes.linewidth": 0.8,
        "font.family": "DejaVu Sans",
    })


def _mes_label(mes_str):
    # 'YYYY-MM' -> 'Mmm'
    return MESES_ES.get(mes_str.split("-")[-1], mes_str)


def _guarda(fig, outdir, nombre):
    ruta = os.path.join(outdir, nombre)
    fig.savefig(ruta)
    plt.close(fig)
    print("  [ok] {}".format(nombre))
    return ruta


# ------------------------------------------------------------------------------
# GRAFICAS A PARTIR DE LAS ESTADISTICAS
# ------------------------------------------------------------------------------
def fig_serie_mensual(res, outdir):
    df = pd.DataFrame(res["por_mes"]).copy()
    df["mlab"] = df["mes"].map(_mes_label)
    df = df.sort_values("mes")

    fig, ax1 = plt.subplots(figsize=(11, 6))
    sns.barplot(data=df, x="mlab", y="area_presencia_km2", color=COL_SARGAZO,
                alpha=0.85, ax=ax1, edgecolor="white", linewidth=0.6)
    ax1.set_ylabel("Área de sargazo (km$^2$)", color=COL_SARGAZO)
    ax1.tick_params(axis="y", labelcolor=COL_SARGAZO)
    ax1.set_xlabel("Mes")

    ax2 = ax1.twinx()
    ax2.plot(range(len(df)), df["biomasa_humeda_ton"] / 1000.0, color=COL_BIOMASA,
             marker="o", lw=2.5, label="Biomasa")
    ax2.set_ylabel("Biomasa húmeda (miles de ton)", color=COL_BIOMASA)
    ax2.tick_params(axis="y", labelcolor=COL_BIOMASA)
    ax2.grid(False)

    ax1.set_title("Sargazo mensual – {} ({})\nárea detectada y biomasa estimada".format(
        REGION, res["anio"]))
    fig.tight_layout()
    return _guarda(fig, outdir, "01_serie_mensual_area_biomasa.png")


def fig_poligonos_mes(res, outdir):
    df = pd.DataFrame(res["por_mes"]).copy()
    df["mlab"] = df["mes"].map(_mes_label)
    df = df.sort_values("mes")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sns.barplot(data=df, x="mlab", y="n_poligonos", color="#3b6ea5", ax=ax,
                edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Mes")
    ax.set_ylabel("Número de polígonos detectados")
    ax.set_title("Número de detecciones de sargazo por mes – {} ({})".format(REGION, res["anio"]))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    fig.tight_layout()
    return _guarda(fig, outdir, "02_poligonos_por_mes.png")


def fig_por_tile(res, outdir):
    df = pd.DataFrame(res["por_tile"]).copy()
    df = df.sort_values("area_presencia_km2", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 9))
    sns.barplot(data=df, y="tile", x="area_presencia_km2", color=COL_SARGAZO,
                ax=ax, edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Área de sargazo (km$^2$)")
    ax.set_ylabel("Tile (MGRS)")
    ax.set_title("Área de sargazo por tile Sentinel-2 – {} ({})".format(REGION, res["anio"]))
    for i, v in enumerate(df["area_presencia_km2"]):
        ax.text(v, i, " {:.1f}".format(v), va="center", fontsize=9)
    fig.tight_layout()
    return _guarda(fig, outdir, "03_area_por_tile.png")


def fig_por_lugar(res, outdir):
    df = pd.DataFrame(res["por_lugar"]).copy()
    nombres = {"oceano": "Océano", "playa": "Playa", "c_aguacont": "Cuerpo de agua cont."}
    df["lugar_lbl"] = df["lugar"].map(lambda x: nombres.get(x, x))
    df = df.sort_values("area_presencia_km2", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    sns.barplot(data=df, y="lugar_lbl", x="area_presencia_km2", color="#1f7a8c",
                ax=ax, edgecolor="white", linewidth=0.6)
    ax.set_xscale("log")
    ax.set_xlabel("Área de sargazo (km$^2$, escala log)")
    ax.set_ylabel("")
    ax.set_title("Distribución del sargazo por ubicación – {} ({})".format(REGION, res["anio"]))
    for i, (v, n) in enumerate(zip(df["area_presencia_km2"], df["n_poligonos"])):
        ax.text(v, i, "  {:.2f} km$^2$  ({:,} pol.)".format(v, n), va="center", fontsize=9)
    fig.tight_layout()
    return _guarda(fig, outdir, "04_area_por_lugar.png")


def fig_distancia_costa(res, outdir):
    if not res.get("por_distancia_costa"):
        return None
    df = pd.DataFrame(res["por_distancia_costa"]).copy()
    orden = ["0-1 km", "1-5 km", "5-20 km", ">20 km"]
    df["dist_costa"] = pd.Categorical(df["dist_costa"], categories=orden, ordered=True)
    df = df.sort_values("dist_costa")
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    sns.barplot(data=df, x="dist_costa", y="area_presencia_km2",
                hue="dist_costa", palette="crest", legend=False, ax=ax,
                edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Distancia a la costa")
    ax.set_ylabel("Área de sargazo (km$^2$)")
    ax.set_title("Sargazo según distancia a la costa – {} ({})".format(REGION, res["anio"]))
    total = df["area_presencia_km2"].sum()
    for i, v in enumerate(df["area_presencia_km2"]):
        ax.text(i, v, "{:.0f}%".format(100 * v / total), ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    return _guarda(fig, outdir, "05_distancia_costa.png")


def fig_escenarios_fc(res, outdir):
    df = pd.DataFrame(res["escenarios_fc"]).copy()
    df = df.sort_values("fc")
    df["fc_lbl"] = df["fc"].map(lambda x: "FC = {:.2f}".format(x))
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    colors = [COL_BIOMASA if s else "#cbb79c" for s in df["es_seleccionado"]]
    ax.bar(df["fc_lbl"], df["biomasa_humeda_ton"] / 1000.0, color=colors,
           edgecolor="white", linewidth=0.6)
    ax.set_ylabel("Biomasa húmeda (miles de ton)")
    ax.set_xlabel("Escenario de fracción de cobertura (FC)")
    ax.set_title("Biomasa estimada según el factor FC – {} ({})".format(REGION, res["anio"]))
    for i, v in enumerate(df["biomasa_humeda_ton"] / 1000.0):
        ax.text(i, v, "{:,.0f}k".format(v), ha="center", va="bottom", fontsize=10)
    ax.margins(y=0.15)
    ax.text(0.02, 0.97, "Barra resaltada = FC usado en el reporte",
            transform=ax.transAxes, ha="left", va="top", fontsize=9, style="italic")
    fig.tight_layout()
    return _guarda(fig, outdir, "06_escenarios_fc.png")


def fig_acumulada(res, outdir):
    df = pd.DataFrame(res["por_mes"]).copy().sort_values("mes")
    df["mlab"] = df["mes"].map(_mes_label)
    df["acum"] = df["area_presencia_km2"].cumsum()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.fill_between(range(len(df)), df["acum"], color=COL_SARGAZO, alpha=0.30)
    ax.plot(range(len(df)), df["acum"], color=COL_SARGAZO, marker="o", lw=2.5)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["mlab"])
    ax.set_xlabel("Mes")
    ax.set_ylabel("Área acumulada (km$^2$)")
    ax.set_title("Área de sargazo acumulada en el año – {} ({})".format(REGION, res["anio"]))
    fig.tight_layout()
    return _guarda(fig, outdir, "07_area_acumulada.png")


# ------------------------------------------------------------------------------
# VERSIONES DE BIOMASA (mismas categorias que las de area)
# ------------------------------------------------------------------------------
def fig_biomasa_tile(res, outdir):
    df = pd.DataFrame(res["por_tile"]).copy()
    df = df.sort_values("biomasa_humeda_ton", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 9))
    sns.barplot(data=df, y="tile", x="biomasa_humeda_ton", color=COL_BIOMASA,
                ax=ax, edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Biomasa húmeda (ton)")
    ax.set_ylabel("Tile (MGRS)")
    ax.set_title("Biomasa de sargazo por tile Sentinel-2 – {} ({})".format(REGION, res["anio"]))
    for i, v in enumerate(df["biomasa_humeda_ton"]):
        ax.text(v, i, " {:,.0f}".format(v), va="center", fontsize=9)
    fig.tight_layout()
    return _guarda(fig, outdir, "11_biomasa_por_tile.png")


def fig_biomasa_lugar(res, outdir):
    df = pd.DataFrame(res["por_lugar"]).copy()
    nombres = {"oceano": "Océano", "playa": "Playa", "c_aguacont": "Cuerpo de agua cont."}
    df["lugar_lbl"] = df["lugar"].map(lambda x: nombres.get(x, x))
    df = df.sort_values("biomasa_humeda_ton", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    sns.barplot(data=df, y="lugar_lbl", x="biomasa_humeda_ton", color=COL_BIOMASA,
                ax=ax, edgecolor="white", linewidth=0.6)
    ax.set_xscale("log")
    ax.set_xlabel("Biomasa húmeda (ton, escala log)")
    ax.set_ylabel("")
    ax.set_title("Distribución de biomasa por ubicación – {} ({})".format(REGION, res["anio"]))
    for i, v in enumerate(df["biomasa_humeda_ton"]):
        ax.text(v, i, "  {:,.0f} ton".format(v), va="center", fontsize=9)
    fig.tight_layout()
    return _guarda(fig, outdir, "12_biomasa_por_lugar.png")


def fig_biomasa_distancia(res, outdir):
    if not res.get("por_distancia_costa"):
        return None
    df = pd.DataFrame(res["por_distancia_costa"]).copy()
    orden = ["0-1 km", "1-5 km", "5-20 km", ">20 km"]
    df["dist_costa"] = pd.Categorical(df["dist_costa"], categories=orden, ordered=True)
    df = df.sort_values("dist_costa")
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    sns.barplot(data=df, x="dist_costa", y="biomasa_humeda_ton",
                hue="dist_costa", palette="flare", legend=False, ax=ax,
                edgecolor="white", linewidth=0.6)
    ax.set_xlabel("Distancia a la costa")
    ax.set_ylabel("Biomasa húmeda (ton)")
    ax.set_title("Biomasa de sargazo según distancia a la costa – {} ({})".format(
        REGION, res["anio"]))
    total = df["biomasa_humeda_ton"].sum()
    for i, v in enumerate(df["biomasa_humeda_ton"]):
        ax.text(i, v, "{:.0f}%".format(100 * v / total), ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    return _guarda(fig, outdir, "13_biomasa_distancia_costa.png")


def fig_biomasa_acumulada(res, outdir):
    df = pd.DataFrame(res["por_mes"]).copy().sort_values("mes")
    df["mlab"] = df["mes"].map(_mes_label)
    df["acum"] = df["biomasa_humeda_ton"].cumsum() / 1000.0
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.fill_between(range(len(df)), df["acum"], color=COL_BIOMASA, alpha=0.30)
    ax.plot(range(len(df)), df["acum"], color=COL_BIOMASA, marker="o", lw=2.5)
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["mlab"])
    ax.set_xlabel("Mes")
    ax.set_ylabel("Biomasa húmeda acumulada (miles de ton)")
    ax.set_title("Biomasa de sargazo acumulada en el año – {} ({})".format(REGION, res["anio"]))
    fig.tight_layout()
    return _guarda(fig, outdir, "14_biomasa_acumulada.png")


# ------------------------------------------------------------------------------
# FIGURAS QUE REQUIEREN EL GEOJSON DE POLIGONOS
# ------------------------------------------------------------------------------
def carga_geojson(ruta):
    print("Leyendo GeoJSON de poligonos (puede tardar)...")
    gdf = gpd.read_file(ruta)
    print("  poligonos: {:,}".format(len(gdf)))
    if "area_km2" in gdf.columns:
        gdf["area_km2"] = pd.to_numeric(gdf["area_km2"], errors="coerce")
    # Centroides en lon/lat (suprime el warning de CRS geografico).
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cent = gdf.geometry.representative_point()
    gdf["lon"] = cent.x.values
    gdf["lat"] = cent.y.values
    if "fechadia" in gdf.columns:
        gdf["fecha_dt"] = pd.to_datetime(gdf["fechadia"], errors="coerce")
        gdf["mes_n"] = gdf["fecha_dt"].dt.month
    return gdf


def fig_hist_tamano(gdf, anio, outdir):
    a = gdf["area_km2"].dropna()
    a = a[a > 0]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    sns.histplot(a * 1e6, bins=60, log_scale=(True, False), color=COL_SARGAZO,
                 edgecolor="white", ax=ax)
    ax.set_xlabel("Área del polígono (m$^2$, escala log)")
    ax.set_ylabel("Número de polígonos")
    ax.set_title("Distribución del tamaño de los polígonos de sargazo – {} ({})".format(REGION, anio))
    med = float(np.median(a * 1e6))
    ax.axvline(med, color=COL_BIOMASA, ls="--", lw=2)
    ax.text(med, ax.get_ylim()[1] * 0.9, "  mediana = {:.0f} m$^2$".format(med),
            color=COL_BIOMASA, fontsize=10)
    fig.tight_layout()
    return _guarda(fig, outdir, "08_distribucion_tamano_poligonos.png")


def _aspecto(ax, lat_media):
    ax.set_aspect(1.0 / np.cos(np.deg2rad(lat_media)))


def _barra_escala(ax, km=50, ubic=(0.06, 0.06)):
    """Barra de escala grafica sencilla. Llamar despues de fijar xlim/ylim."""
    lon0, lon1 = ax.get_xlim()
    lat0, lat1 = ax.get_ylim()
    lat_med = (lat0 + lat1) / 2.0
    grados = km / (111.320 * np.cos(np.deg2rad(lat_med)))  # km -> grados de lon
    x0 = lon0 + (lon1 - lon0) * ubic[0]
    y0 = lat0 + (lat1 - lat0) * ubic[1]
    h = (lat1 - lat0) * 0.008
    ax.plot([x0, x0 + grados], [y0, y0], color="black", lw=3,
            solid_capstyle="butt", zorder=22)
    for xx in (x0, x0 + grados):
        ax.plot([xx, xx], [y0, y0 + h], color="black", lw=1.4, zorder=22)
    ax.text(x0 + grados / 2.0, y0 + h * 1.6, "{} km".format(km),
            ha="center", va="bottom", fontsize=9, zorder=22,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))


def _flecha_norte(ax, x=0.94, y=0.93, largo=0.075):
    """Flecha de norte sencilla en coordenadas de eje."""
    ax.annotate("N", xy=(x, y), xytext=(x, y - largo),
                xycoords="axes fraction", textcoords="axes fraction",
                ha="center", va="bottom", fontsize=13, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=2.2),
                zorder=25,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))


def carga_contexto(zee_path, paises_path):
    """Carga (una vez) las capas de ZEE de Mexico y limites de paises."""
    if _CTX["cargado"]:
        return
    _CTX["cargado"] = True
    try:
        if os.path.isfile(zee_path):
            _CTX["zee"] = gpd.read_file(zee_path).to_crs(4326)
            print("  contexto: ZEE de Mexico cargada")
        else:
            print("  contexto: no se encontro la ZEE ({})".format(zee_path))
    except Exception as e:  # noqa
        print("  [aviso] no se pudo cargar la ZEE: {}".format(e))
    try:
        if os.path.isfile(paises_path):
            _CTX["paises"] = gpd.read_file(paises_path).to_crs(4326)
            print("  contexto: limites de paises cargados")
        else:
            print("  contexto: no se encontraron limites de paises ({})".format(paises_path))
    except Exception as e:  # noqa
        print("  [aviso] no se pudo cargar paises: {}".format(e))


def _dibuja_contexto(ax, extent, con_zee=True, lw_pais=0.4, lw_zee=1.3, zee_label=None):
    """Dibuja tierra (paises) y la linea de la ZEE recortadas al extent dado.
    extent = (lon_min, lon_max, lat_min, lat_max)."""
    lon_min, lon_max, lat_min, lat_max = extent
    if DIBUJAR_TIERRA and _CTX["paises"] is not None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _CTX["paises"].cx[lon_min:lon_max, lat_min:lat_max].plot(
                    ax=ax, color=COL_TIERRA, edgecolor=COL_TIERRA_BORDE,
                    linewidth=lw_pais, zorder=1)
        except Exception:  # noqa
            pass
    if con_zee and _CTX["zee"] is not None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _CTX["zee"].boundary.plot(ax=ax, color=COL_ZEE, linewidth=lw_zee,
                                          zorder=5, label=zee_label)
        except Exception:  # noqa
            pass


def _inset_ubicacion(fig, rect, extent, area_bbox, titulo):
    """Minimapa de ubicacion. rect=[x,y,w,h] en coords de figura;
    extent=(lon0,lon1,lat0,lat1) del minimapa; area_bbox=(lon0,lon1,lat0,lat1)
    de la zona de analisis a resaltar."""
    axin = fig.add_axes(rect)
    axin.set_facecolor(COL_OCEANO)
    _dibuja_contexto(axin, extent, con_zee=True, lw_pais=0.3, lw_zee=0.8)
    lon0, lon1, lat0, lat1 = extent
    axin.set_xlim(lon0, lon1)
    axin.set_ylim(lat0, lat1)
    axin.set_aspect(1.0 / np.cos(np.deg2rad((lat0 + lat1) / 2)))
    # Recuadro del area de analisis
    a0, a1, b0, b1 = area_bbox
    axin.add_patch(Rectangle((a0, b0), a1 - a0, b1 - b0, fill=True,
                             facecolor="#e8483c", edgecolor="#b3160c",
                             alpha=0.85, lw=1.0, zorder=10))
    axin.set_xticks([])
    axin.set_yticks([])
    for s in axin.spines.values():
        s.set_edgecolor("#444444")
        s.set_linewidth(1.0)
    axin.set_title(titulo, fontsize=9, fontweight="bold", pad=3)
    return axin


def fig_mapa_densidad(gdf, anio, outdir, gridsize):
    lon, lat = gdf["lon"].values, gdf["lat"].values
    area = gdf["area_km2"].fillna(0).values
    lat_media = float(np.nanmean(lat))
    lon_min, lon_max = float(np.nanmin(lon)), float(np.nanmax(lon))
    lat_min, lat_max = float(np.nanmin(lat)), float(np.nanmax(lat))
    mlon = (lon_max - lon_min) * 0.06 + 0.1
    mlat = (lat_max - lat_min) * 0.04 + 0.1
    area_bbox = (lon_min, lon_max, lat_min, lat_max)

    fig, ax = plt.subplots(figsize=(10.5, 11))
    ax.set_facecolor(COL_OCEANO)
    _dibuja_contexto(ax, (lon_min - 1, lon_max + 1, lat_min - 1, lat_max + 1),
                     con_zee=True, lw_zee=1.6, zee_label="Zona Económica Exclusiva")
    hb = ax.hexbin(lon, lat, C=area, reduce_C_function=np.sum, gridsize=gridsize,
                   cmap=CMAP_DENS, mincnt=1, norm=LogNorm(), linewidths=0.0, zorder=3)
    cb = fig.colorbar(hb, ax=ax, shrink=0.6, pad=0.02)
    cb.set_label("Área de sargazo por celda (km$^2$)")
    _aspecto(ax, lat_media)
    ax.set_xlim(lon_min - mlon, lon_max + mlon)
    ax.set_ylim(lat_min - mlat, lat_max + mlat)
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.set_title("Mapa de densidad de sargazo – {} ({})".format(REGION, anio))
    ax.grid(True, ls=":", lw=0.5, alpha=0.4)
    if _CTX["zee"] is not None:
        from matplotlib.lines import Line2D
        ax.legend(handles=[Line2D([0], [0], color=COL_ZEE, lw=1.8,
                                  label="ZEEM (Caribe)")],
                  loc="upper left", fontsize=9, framealpha=0.9)
    _barra_escala(ax, km=50)
    _flecha_norte(ax)
    ax.text(0.01, 0.012,
            "ZEEM: Zona Económica Exclusiva de México (sector Caribe) | "
            "Sentinel-2 MSI | proyección geográfica (WGS84)",
            transform=ax.transAxes, fontsize=7.5, style="italic", va="bottom",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))

    fig.tight_layout()
    return _guarda(fig, outdir, "09_mapa_densidad_anual.png")


def fig_mapa_estacional(gdf, anio, outdir, gridsize):
    if "mes_n" not in gdf.columns or gdf["mes_n"].isna().all():
        return None
    trimestres = [
        ("Ene-Mar", [1, 2, 3]),
        ("Abr-Jun", [4, 5, 6]),
        ("Jul-Sep", [7, 8, 9]),
        ("Oct-Dic", [10, 11, 12]),
    ]
    lat_media = float(np.nanmean(gdf["lat"]))
    lon_min, lon_max = gdf["lon"].min(), gdf["lon"].max()
    lat_min, lat_max = gdf["lat"].min(), gdf["lat"].max()

    ext = (lon_min - 0.2, lon_max + 0.2, lat_min - 0.2, lat_max + 0.2)
    fig, axes = plt.subplots(1, 4, figsize=(18, 8), sharex=True, sharey=True)
    vmax = None
    hbs = []
    for ax, (nom, meses) in zip(axes, trimestres):
        sub = gdf[gdf["mes_n"].isin(meses)]
        ax.set_facecolor(COL_OCEANO)
        _dibuja_contexto(ax, (lon_min - 1, lon_max + 1, lat_min - 1, lat_max + 1),
                         con_zee=True, lw_pais=0.3, lw_zee=1.0)
        if len(sub):
            hb = ax.hexbin(sub["lon"], sub["lat"], C=sub["area_km2"].fillna(0),
                           reduce_C_function=np.sum, gridsize=gridsize,
                           cmap=CMAP_DENS, mincnt=1, norm=LogNorm(),
                           extent=(lon_min, lon_max, lat_min, lat_max),
                           linewidths=0.0, zorder=3)
            hbs.append(hb)
        _aspecto(ax, lat_media)
        ax.set_xlim(ext[0], ext[1])
        ax.set_ylim(ext[2], ext[3])
        a_km2 = float(sub["area_km2"].sum()) if len(sub) else 0.0
        ax.set_title("{}\n{:.1f} km$^2$".format(nom, a_km2), fontsize=13)
        ax.set_xlabel("Longitud")
        ax.grid(True, ls=":", lw=0.4, alpha=0.4)
    axes[0].set_ylabel("Latitud")
    _barra_escala(axes[0], km=50)
    _flecha_norte(axes[-1])
    # Escala de color comun
    if hbs:
        vmax = max(h.get_array().max() for h in hbs)
        vmin = min(h.get_array().min() for h in hbs if h.get_array().size)
        for h in hbs:
            h.set_norm(LogNorm(vmin=max(vmin, 1e-6), vmax=vmax))
        cb = fig.colorbar(hbs[-1], ax=axes, shrink=0.55, pad=0.01)
        cb.set_label("Área de sargazo por celda (km$^2$)")
    fig.suptitle("Evolución estacional del sargazo – {} ({})".format(REGION, anio),
                 fontsize=18, fontweight="bold")
    return _guarda(fig, outdir, "10_mapa_estacional.png")


# ------------------------------------------------------------------------------
def main():
    args = parse_args()
    estilo()
    os.makedirs(args.outdir, exist_ok=True)

    with open(args.resumen, "r", encoding="utf-8") as f:
        res = json.load(f)
    anio = res.get("anio", "")

    print("=" * 70)
    print("Figuras del reporte anual de sargazo {}".format(anio))
    print("  Resumen : {}".format(args.resumen))
    print("  GeoJSON : {}".format("(omitido)" if args.sin_mapas else args.geojson))
    print("  Salida  : {}".format(args.outdir))
    print("=" * 70)

    generadas = []
    print("\n>> Graficas de estadisticas")
    for fn in (fig_serie_mensual, fig_poligonos_mes, fig_por_tile, fig_por_lugar,
               fig_distancia_costa, fig_escenarios_fc, fig_acumulada,
               fig_biomasa_tile, fig_biomasa_lugar, fig_biomasa_distancia,
               fig_biomasa_acumulada):
        try:
            r = fn(res, args.outdir)
            if r:
                generadas.append(r)
        except Exception as e:  # noqa
            print("  [ERROR] {}: {}".format(fn.__name__, e))

    if not args.sin_mapas:
        print("\n>> Figuras con el GeoJSON (distribucion y mapas)")
        try:
            carga_contexto(args.zee, args.paises)
            gdf = carga_geojson(args.geojson)
            for fn in (fig_hist_tamano,):
                try:
                    generadas.append(fn(gdf, anio, args.outdir))
                except Exception as e:  # noqa
                    print("  [ERROR] {}: {}".format(fn.__name__, e))
            for fn in (fig_mapa_densidad, fig_mapa_estacional):
                try:
                    r = fn(gdf, anio, args.outdir, args.hex_gridsize)
                    if r:
                        generadas.append(r)
                except Exception as e:  # noqa
                    print("  [ERROR] {}: {}".format(fn.__name__, e))
        except Exception as e:  # noqa
            print("  [ERROR] al leer el GeoJSON: {}".format(e))

    print("\n" + "-" * 70)
    print("Figuras generadas: {}".format(len(generadas)))
    print("Carpeta: {}".format(args.outdir))


if __name__ == "__main__":
    main()
