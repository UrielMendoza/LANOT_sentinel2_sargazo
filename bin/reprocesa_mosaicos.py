#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para generar SOLO los mosaicos (TC y sargazo)
sin ejecutar todo el pipeline de detección de sargazo.

Extraído de sargazoL2A() - solo la parte final de mosaicos.

Uso:
    python3 generar_mosaicos.py <fecha> <region>

Ejemplos:
    python3 generar_mosaicos.py 20240815T160911 sargazo_1
    python3 generar_mosaicos.py 20240815T160911 sargazo_6

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


def generaMosaicos(fecha, region):
    """
    Genera los mosaicos TC y sargazo para una fecha y región dadas.
    Replica EXACTAMENTE la lógica del bloque final de sargazoL2A().
    """
    iniTotal = time.time()

    # fechaDia en formato 'YYYY-MM-DD' para uneVectorial
    fechaDt  = datetime.datetime.strptime(fecha, '%Y%m%dT%H%M%S')
    fechaDia = fechaDt.strftime('%Y-%m-%d')

    regionMosaicoTC, regionMosaicoSar = determinaRegionMosaico(region)

    print('=============================================')
    print(f'Procesando mosaicos para fecha: {fecha}')
    print(f'Region: {region}')
    print(f'Mosaico TC: {regionMosaicoTC}')
    print(f'Mosaico Sargazo: {regionMosaicoSar}')
    print('=============================================')

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

        # ---- VISTAS (opcional, comenta si NO quieres regenerar vistas) ----
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
            fechaDia,
            pathVertices + f'sargazo_centroides/{subdir}/',
            pathOutputPeta, pathOutputWeb
        )
        # Segmentados
        processing_sentinel2.uneVectorial(
            4326, 'sargazo_segmentados',
            pathVertices + 'sargazo_segmentados/',
            fechaDia,
            pathVertices + f'sargazo_segmentados/{subdir}/',
            pathOutputPeta, pathOutputWeb
        )
        # Máscara de nubes
        processing_sentinel2.uneVectorial(
            4326, 'mascara_nubes',
            pathVertices + 'mascara_nubes/',
            fechaDia,
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
        print("Uso: python3 generar_mosaicos.py <fecha YYYYMMDDTHHMMSS> <region>")
        print("Ejemplo: python3 generar_mosaicos.py 20240815T160911 sargazo_1")
        print("Regiones: sargazo_1, sargazo_2, sargazo_3, sargazo_4, sargazo_5, sargazo_6")
        sys.exit(1)

    fecha  = sys.argv[1]
    region = sys.argv[2]

    generaMosaicos(fecha, region)


if __name__ == '__main__':
    main()