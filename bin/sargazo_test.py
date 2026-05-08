#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba local del procesamiento de sargazo.
Tile: 16QDH  |  Fecha: 2026-04-10

Usa la estructura de carpetas creada por install.sh (test/ y data/masks/).
No requiere base de datos ni acceso al servidor: las operaciones de DB,
email y SCP se omiten con stubs locales.

Ejecucion:
    cd bin/
    python3 sargazo_test.py
"""

import os
import time
import datetime
from glob import glob
import traceback

import processing_sentinel2
import download_datasets_ds

# ---------------------------------------------------------------
# CONFIGURACION FIJA
# ---------------------------------------------------------------
TILE       = '16QDH'
FECHA_STR  = '20260410'
start_date = datetime.datetime.strptime(FECHA_STR, '%Y%m%d')
end_date   = datetime.datetime.strptime(FECHA_STR, '%Y%m%d')
SNbuffer   = True

# ---------------------------------------------------------------
# RUTAS LOCALES
# Relativas a la raiz del repo (un nivel arriba de bin/)
# Deben coincidir con lo que crea install.sh
# ---------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOME_DIR = os.path.expanduser('~')

pathTmp           = os.path.join(BASE_DIR, 'test', 'tmp', 'manual')    + os.sep
pathInputL1C      = os.path.join(BASE_DIR, 'test', 'L1C')               + os.sep
pathInput         = os.path.join(BASE_DIR, 'test', 'L2A')               + os.sep
pathOutput        = os.path.join(BASE_DIR, 'test', 'geojson', 'sargazo')+ os.sep
pathOutputEmpty   = os.path.join(BASE_DIR, 'test', 'geojson', 'sargazo')+ os.sep
pathOutputGeoTiff = os.path.join(BASE_DIR, 'test', 'geotiff')           + os.sep
pathOutputWeb     = os.path.join(BASE_DIR, 'test', 'web')               + os.sep
pathOutputPeta    = os.path.join(BASE_DIR, 'test', 'peta')              + os.sep
pathInputPeta     = os.path.join(BASE_DIR, 'test', 'peta', 'L1C')       + os.sep
pathVertices      = os.path.join(BASE_DIR, 'test', 'geojson')           + os.sep
pathLM            = os.path.join(BASE_DIR, 'data', 'masks')             + os.sep

# Sen2Cor instalado por install.sh en el home del usuario
pathSen2corBin = os.path.join(HOME_DIR, 'Sen2Cor-02.12.03-Linux64', 'bin') + os.sep
pathCFG        = os.path.join(HOME_DIR, 'sen2cor', '2.12', 'cfg', 'L2A_GIPP.xml')

# ---------------------------------------------------------------
# CREA DIRECTORIOS NECESARIOS
# ---------------------------------------------------------------
for d in [
    pathTmp, pathInputL1C, pathInput, pathOutput,
    pathOutputGeoTiff, pathOutputWeb, pathOutputPeta, pathInputPeta,
    pathVertices,
    os.path.join(pathVertices, 'sargazo_vertices'),
    os.path.join(pathVertices, 'sargazo_centroides'),
    os.path.join(pathVertices, 'sargazo_segmentados'),
    os.path.join(pathVertices, 'mascara_nubes'),
    os.path.join(pathOutputGeoTiff, 'sargazo', TILE),
    os.path.join(pathOutputGeoTiff, 'TC', TILE),
]:
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------
# STUBS: reemplazan llamadas a DB, email y servidor
# ---------------------------------------------------------------
def stub_verificaSargazoDB(tile, fecha):
    return 0

def stub_borraSargazoDB(*args, **kwargs):
    print('[TEST] borraSargazoDB omitida')

def stub_agregaSargazoDB(*args, **kwargs):
    print('[TEST] agregaSargazoDB omitida')

def stub_agregaNoSargazoDB(*args, **kwargs):
    print('[TEST] agregaNoSargazoDB omitida')

def stub_agregaErrorSargazoDB(*args, **kwargs):
    print('[TEST] agregaErrorSargazoDB omitida')

def stub_enviaMail(*args, **kwargs):
    print('[TEST] enviaMail omitida')

# ---------------------------------------------------------------
# PROCESAMIENTO PRINCIPAL
# ---------------------------------------------------------------
if __name__ == '__main__':

    iniTotal = time.time()
    owd = os.getcwd()

    tiles            = [TILE]
    bandas20m        = ('B02', 'B03', 'B04', 'B05', 'B8A', 'B11', 'B12', 'SCL')
    bandas10m        = ['B08']
    regionMosaicoTC  = 'TC'
    regionMosaicoSar = 'sargazo'

    print('====================================================')
    print('LANOT_sentinel2_sargazo  [MODO TEST]')
    print(f'Tile: {TILE}  |  Fecha: {start_date.strftime("%Y-%m-%d")}')
    print('====================================================')

    # 1. DESCARGA
    print('\n1. Descargando...')
    try:
        download_datasets_ds.search_and_download_datasets(
            tiles, start_date, end_date, pathTmp, unzip=False)
    except Exception:
        print('***Error en la descarga***')
        stub_agregaErrorSargazoDB('', '', start_date.strftime('%Y%m%dT%H%M%S'), '',
                                  traceback.format_exc())
        raise

    # 2. LISTA ARCHIVOS DESCARGADOS
    try:
        tilesDirs  = processing_sentinel2.listaArchivos(pathTmp + '*')
        numImagenes = len(tilesDirs)
        print('Tiles a procesar:', tilesDirs)
    except Exception:
        print('***Error listando archivos***')
        raise

    print(f'\nTiempo 1: {round((time.time()-iniTotal)/60, 2)} min')

    # 3. ALGORITMO POR IMAGEN
    fecha      = ''
    archivol1c = ''
    archivol2  = ''

    for tileDir in tilesDirs:
        try:
            archivos = processing_sentinel2.listaArchivos(tileDir + '/*')
            archivos.sort()
            print('Archivos a procesar:', archivos)
        except Exception:
            print('***Error listando archivos del tile***')
            stub_agregaErrorSargazoDB('', '', start_date.strftime('%Y%m%dT%H%M%S'), '',
                                      traceback.format_exc())
            continue

        for archivo in archivos:
            try:
                iniTProc     = time.time()
                print('\nProcesando:', archivo)
                fecha        = processing_sentinel2.obtieneFecha(archivo)
                fechaDia     = fecha.split('T')[0]
                fechaImaProc = processing_sentinel2.obtieneFechaImaProc(archivo)
                tile         = processing_sentinel2.obtieneTile(archivo)
                anio         = processing_sentinel2.obtieneAnio(archivo)
                dirI         = processing_sentinel2.nomDir(archivo, 'L2A')
                print(f'Fecha: {fecha}  Tile: {tile}')
                stub_borraSargazoDB(fechaDia, tile, 1)
            except Exception:
                print('***Error obteniendo metadatos***')
                stub_agregaErrorSargazoDB(archivo, '', fecha, tile, traceback.format_exc())
                continue

            if stub_verificaSargazoDB(tile, fecha) == 0:
                try:
                    print('2. Descomprimiendo...')
                    processing_sentinel2.descomprime(archivo, pathTmp)
                    archivol1c = pathInputL1C + tile + '/' + archivo
                    os.makedirs(pathInputL1C + tile + '/', exist_ok=True)
                except Exception:
                    print('***Error descomprimiendo***')
                    stub_agregaErrorSargazoDB(archivol1c, '', fecha, tile, traceback.format_exc())
                    continue

                try:
                    print('3. Correccion atmosferica...')
                    if processing_sentinel2.verificaL2A(tile, fecha, pathInput):
                        print('Ya fue corregido anteriormente, copiando...')
                        archivoL2A = processing_sentinel2.copiaL2A(tile, fecha, pathInput, pathTmp)
                        processing_sentinel2.descomprime(
                            pathTmp + archivoL2A.split('/')[-1], pathTmp)
                        l2a  = glob(pathTmp + '*MSIL2A*' + fecha + '*' + tile + '*.SAFE')[0]
                        dirI = processing_sentinel2.nomDir(l2a, 'L2A')
                        archivol2 = pathInput + tile + '/' + dirI.split('.')[0] + '.zip'
                    else:
                        print('Procesando con Sen2Cor...')
                        processing_sentinel2.sen2cor(
                            pathSen2corBin, pathCFG, pathTmp + dirI, pathTmp, '10')
                        l2a  = glob(pathTmp + '*MSIL2A*' + fecha + '*' + tile + '*.SAFE')[0]
                        dirI = processing_sentinel2.nomDir(l2a, 'L2A')
                        os.makedirs(pathInput + tile + '/', exist_ok=True)
                        os.chdir(pathTmp)
                        os.system('zip -r ' + dirI.split('.')[0] + '.zip ' + dirI)
                        os.system('cp ' + pathTmp + dirI.split('.')[0] + '.zip '
                                  + pathInput + tile + '/')
                        archivol2 = pathInput + tile + '/' + dirI.split('.')[0] + '.zip'
                        os.chdir(owd)
                except Exception:
                    print('***Error en correccion atmosferica***')
                    stub_agregaErrorSargazoDB(archivol1c, '', fecha, tile, traceback.format_exc())
                    print(traceback.format_exc())
                    continue

                print(f'Tiempo 2: {round((time.time()-iniTotal)/60, 2)} min')

                try:
                    os.chdir(owd)

                    # PORCENTAJE NUBES
                    print('3.2 Porcentaje de nubes...')
                    porcNube = processing_sentinel2.obtienePorcentajeNube(pathTmp + dirI)
                    print(f'Porcentaje de nubes: {porcNube}')

                    if porcNube >= 80.0:
                        print('Imagen con exceso de nubosidad, no se procesara.')
                        for banda20 in bandas20m:
                            dirB20 = processing_sentinel2.listaBandas(
                                pathTmp + dirI, 'L2A', 'R20m', banda20)
                            dsB20  = processing_sentinel2.aperturaDS(dirB20)
                            processing_sentinel2.imgToGeoTIF(dsB20, banda20, pathTmp)
                        processing_sentinel2.RGB(
                            pathTmp+bandas20m[4]+'.tif', pathTmp+bandas20m[3]+'.tif',
                            pathTmp+bandas20m[2]+'.tif',
                            tile, anio, fecha, fechaImaProc,
                            pathOutputGeoTiff, pathOutputPeta, pathTmp)
                        processing_sentinel2.RGB_TC(
                            tile, anio, fecha, fechaImaProc, 'L2A', 'R10m',
                            pathTmp + dirI, pathOutputGeoTiff, pathOutputPeta, pathTmp)
                        ref       = processing_sentinel2.aperturaDS(pathTmp + bandas20m[-2] + '.tif')
                        cuadrante = processing_sentinel2.obtieneCuadrante(ref)
                        banderaNub, porcNubeOceano = processing_sentinel2.nubesMascaraSinBuffer(
                            cuadrante, pathTmp + bandas20m[-1] + '.tif', pathLM, pathTmp)
                        processing_sentinel2.guardaMascaraNube(
                            tile, fecha, fechaImaProc, pathTmp, pathOutputPeta,
                            pathVertices + 'mascara_nubes/')
                        stub_agregaNoSargazoDB(archivol2, '', fecha, tile, 'no_p', '0',
                                               str(porcNube), str(porcNube),
                                               str(round((time.time()-iniTProc)/60, 2)))
                        os.system('rm -r ' + pathTmp + '*.tif')
                        os.system('rm -r ' + pathTmp + '*.zip')
                        os.system('rm -r ' + pathTmp + '*.SAFE')
                        break

                    elif porcNube >= 30.0:
                        nubesBajas  = 0.02
                        bufferNubes = 300
                    else:
                        nubesBajas  = 0.04
                        bufferNubes = 500

                    print(f'nubesBajas={nubesBajas}  bufferNubes={bufferNubes}')
                    print(f'Tiempo 3: {round((time.time()-iniTotal)/60, 2)} min')

                    # BANDAS A GEOTIFF
                    print('4. Convirtiendo bandas a GeoTIFF...')
                    for banda20 in bandas20m:
                        dirB20 = processing_sentinel2.listaBandas(
                            pathTmp + dirI, 'L2A', 'R20m', banda20)
                        dsB20  = processing_sentinel2.aperturaDS(dirB20)
                        processing_sentinel2.imgToGeoTIF(dsB20, banda20, pathTmp)
                    for banda10 in bandas10m:
                        dirB10 = processing_sentinel2.listaBandas(
                            pathTmp + dirI, 'L2A', 'R10m', banda10)
                        dsB10  = processing_sentinel2.aperturaDS(dirB10)
                        processing_sentinel2.imgToGeoTIF(dsB10, banda10, pathTmp)
                        processing_sentinel2.remuestrea(
                            pathTmp + banda10 + '_20.tif', dsB10, 20, 20)

                    ref       = processing_sentinel2.aperturaDS(pathTmp + bandas20m[-2] + '.tif')
                    scl       = processing_sentinel2.aperturaDS(pathTmp + bandas20m[-1] + '.tif')
                    cuadrante = processing_sentinel2.obtieneCuadrante(ref)

                    print(f'Tiempo 4: {round((time.time()-iniTotal)/60, 2)} min')

                    # MASCARA NUBES
                    print('5.3 Mascara de nubes con buffer...')
                    banderaNub, porcNubeOceano = processing_sentinel2.nubesMascara(
                        cuadrante, bufferNubes, pathTmp + bandas20m[-1] + '.tif', pathLM, pathTmp)
                    print(f'Nubes: {porcNube}  Nubes oceanico: {porcNubeOceano}')

                    # ALGORITMO SARGAZO
                    print('5.5 Algoritmo sargazo (numpy)...')
                    processing_sentinel2.sargazoBinNumpy(pathTmp)
                    dsSar    = processing_sentinel2.aperturaDS(pathTmp + 'alg_tmp_numpy.tif')
                    print(f'Tiempo 5: {round((time.time()-iniTotal)/60, 2)} min')

                    print('5.6 Entropia...')
                    entropia = processing_sentinel2.entropiaNumpy(pathTmp)
                    print(f'Tiempo 6: {round((time.time()-iniTotal)/60, 2)} min')

                    print('5.7 Filtro de pixeles...')
                    nuMask = processing_sentinel2.filtroPixel(
                        ref, dsSar, nubesBajas, entropia, scl, SNbuffer, pathTmp, pathLM)
                    processing_sentinel2.creaTif(ref, nuMask, pathTmp + 'nubesBajas_mask.tif')
                    del nuMask

                    print('5.8 Guardando mascara de nubes...')
                    processing_sentinel2.guardaMascaraNube(
                        tile, fecha, fechaImaProc, pathTmp, pathOutputPeta,
                        pathVertices + 'mascara_nubes/')
                    print(f'Tiempo 7: {round((time.time()-iniTotal)/60, 2)} min')

                    # POLIGONIZACION
                    print('6. Poligonizacion...')
                    archivoProc, banderaSar = processing_sentinel2.poligonizacion(
                        tile, anio, fecha, pathLM, pathTmp, pathOutput, pathOutputEmpty)
                    print(f'Tiempo 8: {round((time.time()-iniTotal)/60, 2)} min')

                    if banderaSar:
                        print('6.2 Mascaras vectoriales...')
                        banderaSar, totalSarMask, archivoProc = \
                            processing_sentinel2.mascarasVectoriales(
                                1, tile, anio, fecha, fechaImaProc, SNbuffer,
                                pathLM, pathTmp, pathOutput, pathOutputEmpty, pathOutputPeta)
                        banderaSar_log = 'si'
                        totalSar       = totalSarMask
                    else:
                        banderaSar_log = 'no'
                        totalSar       = '0'

                    # RGB
                    print('7. Compuesto RGB FC...')
                    processing_sentinel2.RGB(
                        pathTmp+bandas20m[4]+'.tif', pathTmp+bandas20m[3]+'.tif',
                        pathTmp+bandas20m[2]+'.tif',
                        tile, anio, fecha, fechaImaProc,
                        pathOutputGeoTiff, pathOutputPeta, pathTmp)
                    print('7.2 Compuesto RGB TC...')
                    processing_sentinel2.RGB_TC(
                        tile, anio, fecha, fechaImaProc, 'L2A', 'R10m',
                        pathTmp + dirI, pathOutputGeoTiff, pathOutputPeta, pathTmp)

                    print(f'Tiempo 10: {round((time.time()-iniTotal)/60, 2)} min')

                    # RESULTADOS LOCALES (sin DB)
                    print('8. Guardando resultados locales...')
                    tproc = round((time.time()-iniTProc)/60, 2)
                    if banderaSar:
                        processing_sentinel2.obtieneVertices(
                            archivoProc,
                            pathVertices + 'sargazo_vertices/', pathOutputPeta, pathOutputWeb)
                        processing_sentinel2.obtieneCentroides(
                            archivoProc,
                            pathVertices + 'sargazo_centroides/', pathOutputPeta, pathOutputWeb, pathLM)
                        processing_sentinel2.obtieneSegmentado(
                            archivoProc,
                            pathVertices + 'sargazo_segmentados/', pathOutputPeta, pathOutputWeb, pathLM)
                        archivoCSV, crs = processing_sentinel2.creaCSV(archivoProc, pathTmp)
                        stub_agregaSargazoDB(crs, archivol2, archivoProc, fecha, tile,
                                             banderaSar_log, totalSar,
                                             str(porcNube), str(porcNubeOceano),
                                             str(tproc), archivoCSV, 1)
                    else:
                        stub_agregaNoSargazoDB(archivol2, archivoProc, fecha, tile,
                                               banderaSar_log, totalSar,
                                               str(porcNube), str(porcNubeOceano), str(tproc))

                except Exception:
                    print('***Error en el procesamiento***')
                    stub_agregaErrorSargazoDB(archivol1c, archivol2, fecha, tile,
                                              traceback.format_exc())
                    print(traceback.format_exc())
                    continue

                finally:
                    os.chdir(owd)
                    os.system('rm -r ' + pathTmp + '*.tif')
                    os.system('rm -r ' + pathTmp + '*json')
                    os.system('rm -r ' + pathTmp + '*.csv')
                    os.system('rm -r ' + pathTmp + '*.zip')
                    os.system('rm -r ' + pathTmp + '*.SAFE')

            else:
                print(f'Archivo {archivo} ya fue procesado, omitiendo.')

    # MOSAICO
    try:
        if numImagenes != 0 and fecha:
            print('\n9. Procesando mosaico...')
            processing_sentinel2.createMosaicFecha(
                fecha, 'TC', regionMosaicoTC,
                pathOutputGeoTiff, pathOutputPeta, pathOutputWeb, pathTmp)
            processing_sentinel2.createMosaicFecha(
                fecha, 'sargazo', regionMosaicoSar,
                pathOutputGeoTiff, pathOutputPeta, pathOutputWeb, pathTmp)
    except Exception:
        print('***Error en el mosaico***')
        print(traceback.format_exc())

    print(f'\nTiempo total: {round((time.time()-iniTotal)/60, 2)} min')
    print('====================================================')
    print('Procesamiento completo. Resultados en test/')
    print('====================================================')
