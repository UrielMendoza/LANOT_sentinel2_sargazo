#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar mosaicos de Sentinel-2 (TC y RGB FC/sargazo).

Si los tiles NO están procesados para la fecha indicada:
    1. Descarga las imágenes L1C faltantes.
    2. Aplica corrección atmosférica (Sen2Cor) para obtener L2A.
    3. Genera los compuestos RGB (TC y FC) por tile.
Si los tiles SÍ ya están procesados:
    - Solo genera los mosaicos.

NO corre el algoritmo de detección de sargazo, NO genera máscaras ni
poligoniza, NO inserta registros de sargazo en la DB.

Uso:
    python3 reprocesa_mosaicos.py <fecha YYYYMMDD> <region>

Ejemplos:
    python3 reprocesa_mosaicos.py 20240815 sargazo_1
    python3 reprocesa_mosaicos.py 20240420 sargazo_3

@author: urielm
"""

import os
import sys
import time
import datetime
import traceback
from glob import glob
from pathlib import Path

import processing_sentinel2
import download_datasets_ds
import base


# =====================================================
# CONFIGURACIÓN DE RUTAS (del pipeline de producción)
# =====================================================

pathInputL1C      = '/data/input/sentinel2/L1C/'
pathInput         = '/data/output/sentinel2/L2A/'
pathOutput        = '/data/output/sentinel2/l2/geojson/sargazo/'
pathOutputEmpty   = '/data/output/sentinel2/l2/geojson/sargazo/'
pathOutputGeoTiff = '/data/output/sentinel2/l2/geotiff/'
pathOutputWeb     = '/data/sargazo/data/'
pathOutputPeta    = '/depot/sentinel2/output/'
pathInputPeta     = '/depot/sentinel2/input/L1C/'
pathVertices      = '/data/output/sentinel2/l2/geojson/'
pathTmp           = '/data/input/sentinel2/tmp/manual/'
pathLM            = '/home/sargazo/LANOT_sentinel2_sargazo/data/masks/'
pathSen2cor       = '/home/sargazo/'
pathLanot         = '/usr/local/share/lanot/'
pathOutputVistas  = '/data/output/sentinel2/vistas/sargazo/sargazo_TC/'
pathLog           = '/home/sargazo/logs_sentinel2_sargazo/'


def determinaRegionMosaico(region):
    """Determina el nombre del mosaico TC y sargazo según la región."""
    if region in ('sargazo_1', 'sargazo_2', 'sargazo_3'):
        regionMosaicoTC  = 'TC'
        regionMosaicoSar = 'sargazo'
    elif region in ('sargazo_4', 'sargazo_5', 'sargazo_6'):
        regionMosaicoTC  = 'TC_2'
        regionMosaicoSar = 'sargazo_2'
    else:
        raise ValueError(f"Región no reconocida: {region}")
    return regionMosaicoTC, regionMosaicoSar


def buscaTilesProcesados(fechaDia, pathInput):
    """
    Busca tiles ya procesados para la fecha (en TC/ y sargazo/).
    Retorna (fechaCompleta, set_de_tiles_procesados) o (None, set()).
    """
    tilesProcesados = set()
    fechaCompleta = None

    for compuesto in ('sargazo', 'TC'):
        base_dir = Path(pathInput + compuesto)
        if not base_dir.exists():
            continue
        archivos = list(base_dir.rglob('*' + fechaDia + '*.tif'))
        for a in archivos:
            partes = a.name.split('_')
            if len(partes) >= 5:
                tile = partes[3]          # ej T16QEJ
                if fechaCompleta is None:
                    fechaCompleta = partes[4]  # YYYYMMDDTHHMMSS
                tilesProcesados.add(tile)

    return fechaCompleta, tilesProcesados


def generaRGB_porTile(archivoL1C, fecha, tile, bandas20m):
    """
    Genera los compuestos RGB (TC y FC/sargazo) para un tile.
    Replica la lógica del paso 7 de sargazoL2A() cuando NO hay nubosidad excesiva.
    Retorna el nombre del archivo L2A.
    """
    fechaImaProc = processing_sentinel2.obtieneFechaImaProc(archivoL1C)
    anio = processing_sentinel2.obtieneAnio(archivoL1C)
    dirI = processing_sentinel2.nomDir(archivoL1C, 'L2A')

    # 1. Descomprimir L1C
    print('  - Descomprimiendo L1C...')
    processing_sentinel2.descomprime(archivoL1C, pathTmp)

    # Guardar L1C en data
    os.system('mkdir -p ' + pathInputL1C + tile + '/')

    # 2. Verificar si L2A ya existe o correr Sen2Cor
    if processing_sentinel2.verificaL2A(tile, fecha, pathInput):
        print('  - L2A ya existe, copiando...')
        archivoL2A_zip = processing_sentinel2.copiaL2A(tile, fecha, pathInput, pathTmp)
        processing_sentinel2.descomprime(
            pathTmp + archivoL2A_zip.split('/')[-1], pathTmp
        )
        l2a = glob(pathTmp + '*MSIL2A*' + fecha + '*' + tile + '*.SAFE')[0]
        dirI = processing_sentinel2.nomDir(l2a, 'L2A')
        archivol2 = pathInput + tile + '/' + dirI.split('.')[0] + '.zip'
    else:
        print('  - Corriendo Sen2Cor...')
        owd = os.getcwd()
        pathSen2corBin = pathSen2cor + 'LANOT_sentinel2_sargazo/Sen2Cor-02.12.03-Linux64/bin/'
        pathCFG = pathSen2cor + 'sen2cor/2.12/cfg/L2A_GIPP.xml'
        processing_sentinel2.sen2cor(pathSen2corBin, pathCFG, pathTmp + dirI, pathTmp, '10')

        l2a = glob(pathTmp + '*MSIL2A*' + fecha + '*' + tile + '*.SAFE')[0]
        dirI = processing_sentinel2.nomDir(l2a, 'L2A')

        # Comprime y guarda L2A
        os.system('mkdir -p ' + pathInput + tile + '/')
        os.chdir(pathTmp)
        os.system('zip -r ' + dirI.split('.')[0] + '.zip ' + dirI)
        os.system('cp ' + pathTmp + dirI.split('.')[0] + '.zip ' + pathInput + tile + '/')
        archivol2 = pathInput + tile + '/' + dirI.split('.')[0] + '.zip'
        # Envía L2A a servidores
        os.system(
            'scp ' + pathTmp + dirI.split('.')[0] + '.zip '
            'lanotadm@stratus:' + pathOutputPeta + 'L2A/' + tile + '/'
        )
        os.system(
            'scp ' + pathTmp + dirI.split('.')[0] + '.zip '
            'lanotadm@kawak:/data/output/sentinel2/L2A/' + tile + '/'
        )
        os.chdir(owd)

    # 3. Convertir bandas 20m a GeoTIFF
    print('  - Convirtiendo bandas a GeoTIFF...')
    for banda20 in bandas20m:
        dirB20 = processing_sentinel2.listaBandas(
            pathTmp + dirI, 'L2A', 'R20m', banda20
        )
        dsB20 = processing_sentinel2.aperturaDS(dirB20)
        processing_sentinel2.imgToGeoTIF(dsB20, banda20, pathTmp)

    # 4. Crear compuesto RGB FC (sargazo) y TC
    print('  - Creando compuesto RGB FC...')
    os.system('mkdir -p ' + pathOutputGeoTiff + 'sargazo/' + tile + '/')
    processing_sentinel2.RGB(
        pathTmp + bandas20m[4] + '.tif',   # B8A
        pathTmp + bandas20m[3] + '.tif',   # B05
        pathTmp + bandas20m[2] + '.tif',   # B04
        tile, anio, fecha, fechaImaProc,
        pathOutputGeoTiff, pathOutputPeta, pathTmp
    )

    print('  - Creando compuesto RGB TC...')
    os.system('mkdir -p ' + pathOutputGeoTiff + 'TC/' + tile + '/')
    processing_sentinel2.RGB_TC(
        tile, anio, fecha, fechaImaProc, 'L2A', 'R10m',
        pathTmp + dirI, pathOutputGeoTiff, pathOutputPeta, pathTmp
    )

    return archivol2


def generaMosaicos(fechaDia, region):
    """
    Flujo principal:
      - Verifica qué tiles ya están procesados para la fecha.
      - Descarga y procesa (Sen2Cor + RGB) los que falten.
      - Genera mosaicos TC y sargazo.
      - Genera vistas y une vectoriales (opcional).
    """
    iniTotal = time.time()

    try:
        fechaDt = datetime.datetime.strptime(fechaDia, '%Y%m%d')
    except ValueError:
        raise ValueError(
            f"Formato de fecha inválido: '{fechaDia}'. Use YYYYMMDD"
        )

    fechaDiaGuion = fechaDt.strftime('%Y-%m-%d')
    regionMosaicoTC, regionMosaicoSar = determinaRegionMosaico(region)

    # Asegurarse de que pathTmp existe
    os.makedirs(pathTmp, exist_ok=True)

    # Tiles esperados para la región
    tilesRegion = base.tiles[region]
    tilesRegion_set = set('T' + t if not t.startswith('T') else t for t in tilesRegion)

    print('=============================================')
    print(f'Procesando mosaicos para el dia: {fechaDia}')
    print(f'Region: {region}')
    print(f'Mosaico TC: {regionMosaicoTC} | Sargazo: {regionMosaicoSar}')
    print(f'pathTmp: {pathTmp}')
    print(f'Tiles esperados en la region: {sorted(tilesRegion_set)}')
    print('=============================================')

    # 1. Verificar qué tiles ya están procesados
    fecha, tilesProcesados = buscaTilesProcesados(fechaDia, pathOutputGeoTiff)
    print(f'\nTiles ya procesados para {fechaDia}: {sorted(tilesProcesados) if tilesProcesados else "ninguno"}')

    tilesFaltantes = tilesRegion_set - tilesProcesados
    print(f'Tiles faltantes: {sorted(tilesFaltantes) if tilesFaltantes else "ninguno"}')

    # 2. Si faltan tiles, descargar y procesar
    if tilesFaltantes:
        print('\n=============================================')
        print('DESCARGA Y PROCESAMIENTO DE TILES FALTANTES')
        print('=============================================')

        start_date = fechaDt
        end_date   = fechaDt

        # La descarga espera los tiles sin la 'T' inicial (según el script original)
        tilesFaltantes_lista = [t[1:] if t.startswith('T') else t for t in tilesFaltantes]

        # Bandas necesarias para RGB (TC y FC)
        bandas20m = ('B02', 'B03', 'B04', 'B05', 'B8A', 'B11', 'B12', 'SCL')

        try:
            print(f'\n1. Descargando imágenes Sentinel-2 para tiles: {tilesFaltantes_lista}')
            download_datasets_ds.search_and_download_datasets(
                tilesFaltantes_lista, start_date, end_date, pathTmp, unzip=False
            )
        except Exception as e:
            print('***Error en la descarga***')
            print(traceback.format_exc())
            processing_sentinel2.enviaMail(
                fechaDia, 'descarga',
                traceback.format_exc().replace("'", "")
            )
            sys.exit(1)

        # Procesar cada tile descargado
        for tileFaltante in tilesFaltantes_lista:
            tileDir = pathTmp + 'T' + tileFaltante
            if not os.path.isdir(tileDir):
                print(f'  - {tileDir} no existe (no hubo descarga para este tile)')
                continue

            archivosL1C = sorted(glob(tileDir + '/*'))
            if not archivosL1C:
                print(f'  - Sin archivos L1C en {tileDir}')
                continue

            for archivoL1C in archivosL1C:
                try:
                    fecha_arch = processing_sentinel2.obtieneFecha(archivoL1C)
                    tile_arch  = processing_sentinel2.obtieneTile(archivoL1C)
                    print(f'\n2. Procesando: {archivoL1C}')
                    print(f'   Fecha: {fecha_arch} | Tile: {tile_arch}')

                    archivol2 = generaRGB_porTile(
                        archivoL1C, fecha_arch, tile_arch, bandas20m
                    )

                    if fecha is None:
                        fecha = fecha_arch

                    # Limpiar temporales de este tile
                    os.system('rm -rf ' + pathTmp + '*.tif')
                    os.system('rm -rf ' + pathTmp + '*.SAFE')
                    os.system('rm -rf ' + pathTmp + '*.zip')

                except Exception as e:
                    print(f'***Error procesando {archivoL1C}***')
                    print(traceback.format_exc())
                    processing_sentinel2.enviaMail(
                        fecha_arch if 'fecha_arch' in dir() else fechaDia,
                        tile_arch  if 'tile_arch' in dir() else '',
                        traceback.format_exc().replace("'", "")
                    )
                    continue
    else:
        print('\nTodos los tiles ya están procesados. Solo se generarán los mosaicos.')

    # 3. Verificar que tengamos fecha resuelta
    if fecha is None:
        fecha, _ = buscaTilesProcesados(fechaDia, pathOutputGeoTiff)

    if fecha is None:
        print('\n*** No se pudo resolver el timestamp completo ***')
        print(f'Revisa que haya tiles en {pathOutputGeoTiff}')
        sys.exit(1)

    print(f'\nFecha completa para mosaicos: {fecha}')
    print(f'Tiempo hasta aquí: {round((time.time()-iniTotal)/60, 2)} min')

    # 4. Generar mosaicos
    try:
        print('\n=============================================')
        print('GENERACIÓN DE MOSAICOS')
        print('=============================================')

        print('\n3. Procesando mosaico TC...')
        processing_sentinel2.createMosaicFecha(
            fecha, 'TC', regionMosaicoTC,
            pathOutputGeoTiff, pathOutputPeta, pathOutputWeb, pathTmp
        )

        print('\n4. Procesando mosaico Sargazo...')
        processing_sentinel2.createMosaicFecha(
            fecha, 'sargazo', regionMosaicoSar,
            pathOutputGeoTiff, pathOutputPeta, pathOutputWeb, pathTmp
        )

        print('\n5. Generando vistas...')
        os.system(
            'python3 /home/sargazo/LANOT_sentinel2_sargazo/bin/'
            'sargazo_vistas_vertices.py ' + fecha + ' s1'
        )
        os.system(
            'python3 /home/sargazo/LANOT_sentinel2_sargazo/bin/'
            'sargazo_vistas_vertices.py ' + fecha + ' s2'
        )

        # Unir vectoriales si existen para la fecha
        print('\n6. Uniendo vectoriales (si existen)...')
        subdir = 's2' if (regionMosaicoTC == 'TC_2' or regionMosaicoSar == 'sargazo_2') else 's1'

        for tipo in ('sargazo_centroides', 'sargazo_segmentados', 'mascara_nubes'):
            try:
                processing_sentinel2.uneVectorial(
                    4326, tipo,
                    pathVertices + tipo + '/',
                    fechaDiaGuion,
                    pathVertices + f'{tipo}/{subdir}/',
                    pathOutputPeta, pathOutputWeb
                )
            except Exception as e:
                print(f'  - No se pudieron unir {tipo} (probablemente no existen para {fechaDia}): {e}')

        print('\n=============================================')
        print('Mosaicos generados correctamente')
        print(f'Tiempo total: {round((time.time()-iniTotal)/60, 2)} min')
        print('=============================================')

    except Exception as e:
        print('***Error en la generación de mosaicos***')
        print(traceback.format_exc())
        processing_sentinel2.enviaMail(
            fecha, 'mosaico',
            traceback.format_exc().replace("'", "")
        )

    # 5. Limpieza final
    os.system('rm -rf ' + pathTmp + '*.tif')
    os.system('rm -rf ' + pathTmp + '*.SAFE')
    os.system('rm -rf ' + pathTmp + '*.zip')
    os.system('rm -rf ' + pathTmp + '*.json')


def main():
    if len(sys.argv) < 3:
        print("Uso: python3 reprocesa_mosaicos.py <fecha YYYYMMDD> <region>")
        print("Ejemplo: python3 reprocesa_mosaicos.py 20240420 sargazo_3")
        print("Regiones: sargazo_1, sargazo_2, sargazo_3, sargazo_4, sargazo_5, sargazo_6")
        sys.exit(1)

    fechaDia = sys.argv[1]
    region   = sys.argv[2]

    generaMosaicos(fechaDia, region)


if __name__ == '__main__':
    main()