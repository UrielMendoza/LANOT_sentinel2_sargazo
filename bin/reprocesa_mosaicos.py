#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para generar SOLO los mosaicos (TC y sargazo)
sin ejecutar todo el pipeline de detección de sargazo.

Extraído de sargazoL2A() - solo la parte final de mosaicos.

Uso:
    python3 generar_mosaicos.py <fecha YYYYMMDD> <region>

Ejemplos:
    python3 generar_mosaicos.py 20240815 sargazo_1
    python3 generar_mosaicos.py 20240815 sargazo_6

@author: urielm
"""

import os
import sys
import time
import datetime
import traceback
from glob import glob

import processing_sentinel2


# =====================================================
# CONFIGURACIÓN DE RUTAS
# =====================================================
# Ajusta estas rutas según tu entorno (tomadas del script original)

pathTmp          = '/data/tmp/sentinel2/'
pathOutputGeoTiff = '/data/output/sentinel2/l2/geotiff/'
pathOutputPeta   = '/peta/sentinel2/'          # ajustar si aplica
pathOutputWeb    = '/var/www/html/sargazo/'    # ajustar si aplica
pathVertices     = '/data/output/sentinel2/l2/geojson/'
pathLM           = '/data/input/sentinel2/landMask/'
pathLanot        = '/home/sargazo/LANOT_sentinel2_sargazo/'
pathOutputVistas = '/data/output/sentinel2/l2/vistas/'


def determinaRegionMosaico(region):
    """
    Determina el nombre del mosaico TC y sargazo según la región.
    Misma lógica que en el script original.
    """
    if region in ('sargazo_1', 'sargazo_2', 'sargazo_3'):
        regionMosaicoTC  = 'TC'
        regionMosaicoSar = 'sargazo'
    elif region in ('sargazo_4', 'sargazo_5', 'sargazo_6'):
        regionMosaicoTC  = 'TC_2'
        regionMosaicoSar = 'sargazo_2'
    else:
        raise ValueError(f"Región no reconocida: {region}")
    return regionMosaicoTC, regionMosaicoSar


def obtieneFechaCompleta(fechaDia, compuesto, pathInput):
    """
    A partir de una fecha YYYYMMDD, busca el timestamp completo
    (YYYYMMDDTHHMMSS) de los tiles ya procesados para esa fecha.

    Busca dentro de pathInput/<compuesto>/<tile>/*YYYYMMDD*.tif
    y extrae el timestamp del primer archivo encontrado.

    Lanza FileNotFoundError si no encuentra nada.
    """
    # Busca recursivamente cualquier .tif que contenga la fecha en su nombre
    patron = os.path.join(pathInput, compuesto, '**', f'*{fechaDia}*.tif')
    archivos = glob(patron, recursive=True)

    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron tiles procesados para {fechaDia} "
            f"en {pathInput}{compuesto}/"
        )

    # El nombre de archivo tiene formato:
    # S2_MSI_SAR_T16QEJ_20240815T160911_20240815T212806.tif
    # Extraemos el 5º elemento (índice 4) = fecha de adquisición completa
    nombre = os.path.basename(archivos[0])
    partes = nombre.split('_')
    fechaCompleta = partes[4]  # YYYYMMDDTHHMMSS

    # Verifica que coincida con el día solicitado
    if not fechaCompleta.startswith(fechaDia):
        raise ValueError(
            f"El archivo encontrado ({nombre}) no corresponde a {fechaDia}"
        )

    print(f'Fecha completa detectada: {fechaCompleta} '
          f'(de {len(archivos)} archivo(s) encontrado(s))')
    return fechaCompleta


def generaMosaicos(fechaDia, region):
    """
    Genera los mosaicos TC y sargazo para una fecha (YYYYMMDD) y región dadas.
    Resuelve internamente el timestamp completo buscando los tiles ya procesados.
    """
    iniTotal = time.time()

    # Valida el formato de la fecha
    try:
        fechaDt = datetime.datetime.strptime(fechaDia, '%Y%m%d')
    except ValueError:
        raise ValueError(
            f"Formato de fecha inválido: '{fechaDia}'. Use YYYYMMDD (ej: 20240815)"
        )

    fechaDiaGuion = fechaDt.strftime('%Y-%m-%d')

    regionMosaicoTC, regionMosaicoSar = determinaRegionMosaico(region)

    print('=============================================')
    print(f'Procesando mosaicos para el dia: {fechaDia}')
    print(f'Region: {region}')
    print(f'Mosaico TC: {regionMosaicoTC}')
    print(f'Mosaico Sargazo: {regionMosaicoSar}')
    print('=============================================')

    # Resuelve el timestamp completo a partir de los tiles existentes.
    # Se busca en la carpeta de sargazo porque createMosaicFecha usa el mismo
    # fecha para ambos compuestos.
    try:
        fecha = obtieneFechaCompleta(fechaDia, 'sargazo', pathOutputGeoTiff)
    except FileNotFoundError:
        # Si no hay sargazo, intenta con TC
        print('No se encontraron tiles en sargazo/, buscando en TC/...')
        fecha = obtieneFechaCompleta(fechaDia, 'TC', pathOutputGeoTiff)

    try:
        # ---- MOSAICO TC ----
        print('1. Procesando mosaico TC...')
        processing_sentinel2.createMosaicFecha(
            fecha,
            'TC',
            regionMosaicoTC,
            pathOutputGeoTiff,
            pathOutputPeta,
            pathOutputWeb,
            pathTmp
        )

        # ---- MOSAICO SARGAZO ----
        print('2. Procesando mosaico Sargazo...')
        processing_sentinel2.createMosaicFecha(
            fecha,
            'sargazo',
            regionMosaicoSar,
            pathOutputGeoTiff,
            pathOutputPeta,
            pathOutputWeb,
            pathTmp
        )

        # ---- VISTAS ----
        print('3. Generando vistas...')
        os.system(
            'python3 /home/sargazo/LANOT_sentinel2_sargazo/bin/'
            'sargazo_vistas_vertices.py ' + fecha + ' s1'
        )
        os.system(
            'python3 /home/sargazo/LANOT_sentinel2_sargazo/bin/'
            'sargazo_vistas_vertices.py ' + fecha + ' s2'
        )

        # ---- UNIÓN DE VECTORIALES (centroides, segmentados, mascara_nubes) ----
        print('4. Uniendo vectoriales (centroides, segmentados, mascara_nubes)...')
        if regionMosaicoTC == 'TC_2' or regionMosaicoSar == 'sargazo_2':
            subdir = 's2'
        else:
            subdir = 's1'

        # Centroides
        processing_sentinel2.uneVectorial(
            4326, 'sargazo_centroides',
            pathVertices + 'sargazo_centroides/',
            fechaDiaGuion,
            pathVertices + f'sargazo_centroides/{subdir}/',
            pathOutputPeta, pathOutputWeb
        )
        # Segmentados
        processing_sentinel2.uneVectorial(
            4326, 'sargazo_segmentados',
            pathVertices + 'sargazo_segmentados/',
            fechaDiaGuion,
            pathVertices + f'sargazo_segmentados/{subdir}/',
            pathOutputPeta, pathOutputWeb
        )
        # Máscara de nubes
        processing_sentinel2.uneVectorial(
            4326, 'mascara_nubes',
            pathVertices + 'mascara_nubes/',
            fechaDiaGuion,
            pathVertices + f'mascara_nubes/{subdir}/',
            pathOutputPeta, pathOutputWeb
        )

        print('=============================================')
        print(f'Mosaicos generados correctamente')
        print(f'Tiempo total: {round((time.time()-iniTotal)/60, 2)} min')
        print('=============================================')

    except Exception as e:
        print('***Error en la generación de mosaicos***')
        print(traceback.format_exc())
        processing_sentinel2.agregaErrorSargazoDB(
            '', '', fecha, '',
            traceback.format_exc().replace("'", "")
        )
        processing_sentinel2.enviaMail(
            fecha, 'mosaico',
            traceback.format_exc().replace("'", "")
        )


def main():
    if len(sys.argv) < 3:
        print("Uso: python3 generar_mosaicos.py <fecha YYYYMMDD> <region>")
        print("Ejemplo: python3 generar_mosaicos.py 20240815 sargazo_1")
        print("Regiones: sargazo_1, sargazo_2, sargazo_3, sargazo_4, sargazo_5, sargazo_6")
        sys.exit(1)

    fechaDia = sys.argv[1]
    region   = sys.argv[2]

    generaMosaicos(fechaDia, region)


if __name__ == '__main__':
    main()