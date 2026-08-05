#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de DIAGNOSTICO de los filtros del algoritmo de sargazo.

Reproduce paso a paso la cadena de procesamiento de sargazoL2A() pero:
  - NO escribe en la base de datos
  - NO hace scp a peta/kawak/web
  - NO borra el directorio de trabajo
  - Guarda un raster (y un geojson) por CADA etapa y por CADA filtro individual,
    para poder ver en QGIS que pixeles elimina cada mascara.

Uso tipico (en el servidor):

    python3 sargazo_diagnostico_filtros.py --fecha 20260704 --tile T16QDH

Opciones utiles:
    --out DIR             Directorio de salida (default /data/input/sentinel2/tmp/diagnostico/<TILE>_<FECHA>/)
    --sin-buffer-nubes    Ejecuta como SNbuffer=False (nubes sin buffer)
    --sen2cor             Si no existe el L2A, corrige el L1C con Sen2Cor
    --verifica-filtro     Corre ademas el filtroPixel() original (lento, ~horas) y compara

@author: urielm
"""

import os
import sys
import time
import argparse
import datetime
import csv
from glob import glob

import numpy as np
import geopandas as gpd
from osgeo import gdal

import processing_sentinel2 as ps

# ---------------------------------------------------------------------------
# DIRECTORIOS (mismos que sargazo_manual.py)
# ---------------------------------------------------------------------------
pathInputL1C = '/data/input/sentinel2/L1C/'
pathInput = '/data/output/sentinel2/L2A/'
pathLM = '/home/sargazo/LANOT_sentinel2_sargazo/data/masks/'
pathSen2cor = '/home/sargazo/'
pathDiag = '/data/input/sentinel2/tmp/diagnostico/'

# Resolucion de trabajo (m) -> area por pixel en km2
PIX_M = 20
PIX_KM2 = (PIX_M * PIX_M) * 1e-6

bandas20m = ('B02', 'B03', 'B04', 'B05', 'B8A', 'B11', 'B12', 'SCL')
bandas10m = ['B08']

# Resumen acumulado de etapas
resumen = []


def log(msg):
    print(msg, flush=True)


def titulo(msg):
    log('')
    log('=' * 70)
    log(msg)
    log('=' * 70)


def registra(etapa, descripcion, pixeles, archivo=''):
    """Agrega una fila al resumen y la imprime."""
    resumen.append({
        'etapa': etapa,
        'descripcion': descripcion,
        'pixeles': int(pixeles),
        'area_km2': round(float(pixeles) * PIX_KM2, 4),
        'archivo': archivo,
    })
    log('[%s] %-45s %10d px  %10.4f km2' % (etapa, descripcion, pixeles,
                                            float(pixeles) * PIX_KM2))


def registraVector(etapa, descripcion, gdf, archivo=''):
    area = float(gdf['geometry'].area.sum()) * 1e-6 if len(gdf) else 0.0
    resumen.append({
        'etapa': etapa,
        'descripcion': descripcion,
        'pixeles': len(gdf),
        'area_km2': round(area, 4),
        'archivo': archivo,
    })
    log('[%s] %-45s %10d pol %10.4f km2' % (etapa, descripcion, len(gdf), area))


def guardaMascara(ref, arr, path):
    """Guarda un arreglo binario como GeoTIFF Byte comprimido (LZW).

    Se usa un writer propio en lugar de ps.creaTif() porque este ultimo escribe
    Float32 sin compresion: con ~20 mascaras de 5490x5490 serian varios GB.
    Los archivos que si consume el pipeline (alg_tmp_numpy.tif y
    nubesBajas_mask.tif) se siguen escribiendo con ps.creaTif().
    """
    arr = np.asarray(arr)
    ny, nx = arr.shape
    drv = gdal.GetDriverByName('GTiff')
    dst = drv.Create(path, nx, ny, 1, gdal.GDT_Byte,
                     options=['COMPRESS=LZW', 'TILED=YES'])
    dst.SetGeoTransform(ref.GetGeoTransform())
    dst.SetProjection(ref.GetProjectionRef())
    dst.GetRasterBand(1).WriteArray(arr.astype(np.uint8))
    dst.GetRasterBand(1).SetNoDataValue(0)
    dst.FlushCache()
    dst = None
    return path


# ---------------------------------------------------------------------------
# LOCALIZACION Y PREPARACION DE LA IMAGEN
# ---------------------------------------------------------------------------
def localizaL2A(tile, fechaDia, work, usaSen2cor):
    """Deja el .SAFE L2A descomprimido dentro de 'work' y regresa (dirSAFE, fecha)."""
    patron = pathInput + tile + '/*MSIL2A_' + fechaDia + 'T*' + tile + '*'
    candidatos = sorted(glob(patron))
    log('Buscando L2A: ' + patron)

    if candidatos:
        archivo = candidatos[0]
        log('L2A encontrado: ' + archivo)
        if archivo.endswith('.SAFE'):
            os.system('cp -r ' + archivo + ' ' + work)
        else:
            os.system('cp ' + archivo + ' ' + work)
            ps.descomprime(work + archivo.split('/')[-1], work)
    else:
        log('No hay L2A para esa fecha/tile.')
        patronL1C = pathInputL1C + tile + '/*MSIL1C_' + fechaDia + 'T*' + tile + '*'
        candidatosL1C = sorted(glob(patronL1C))
        log('Buscando L1C: ' + patronL1C)
        if not candidatosL1C:
            raise RuntimeError('No se encontro ni L2A ni L1C para %s %s' % (tile, fechaDia))
        if not usaSen2cor:
            raise RuntimeError('Solo hay L1C. Vuelve a correr con --sen2cor para '
                               'aplicar la correccion atmosferica.')
        archivoL1C = candidatosL1C[0]
        log('L1C encontrado: ' + archivoL1C)
        os.system('cp ' + archivoL1C + ' ' + work)
        ps.descomprime(work + archivoL1C.split('/')[-1], work)
        dirL1C = ps.nomDir(archivoL1C, 'L1C')
        log('Corrigiendo con Sen2Cor (puede tardar)...')
        pathSen2corBin = pathSen2cor + 'LANOT_sentinel2_sargazo/Sen2Cor-02.12.03-Linux64/bin/'
        pathCFG = pathSen2cor + 'sen2cor/2.12/cfg/L2A_GIPP.xml'
        ps.sen2cor(pathSen2corBin, pathCFG, work + dirL1C, work, '10')

    safes = glob(work + '*MSIL2A*' + fechaDia + 'T*' + tile + '*.SAFE')
    if not safes:
        raise RuntimeError('No quedo ningun .SAFE L2A en ' + work)
    safe = safes[0]
    fecha = ps.obtieneFecha(safe)
    log('SAFE de trabajo: ' + safe)
    log('Fecha completa de la escena: ' + fecha)
    return safe, fecha


def convierteBandas(safe, work):
    titulo('1. Convirtiendo bandas a GeoTIFF')
    for banda20 in bandas20m:
        dirB20 = ps.listaBandas(safe, 'L2A', 'R20m', banda20)
        dsB20 = ps.aperturaDS(dirB20)
        ps.imgToGeoTIF(dsB20, banda20, work)
    for banda10 in bandas10m:
        dirB10 = ps.listaBandas(safe, 'L2A', 'R10m', banda10)
        dsB10 = ps.aperturaDS(dirB10)
        ps.imgToGeoTIF(dsB10, banda10, work)
        log('Remuestreando ' + banda10 + ' a 20 m...')
        ps.remuestrea(work + banda10 + '_20.tif', dsB10, 20, 20)


# ---------------------------------------------------------------------------
# ETAPA A: UMBRALES (equivalente a sargazoBinNumpy, pero desglosado)
# ---------------------------------------------------------------------------
def etapaUmbrales(work, out):
    titulo('2. Algoritmo de umbrales (sargazoBinNumpy desglosado)')

    b11 = ps.aperturaDS(work + 'B11.tif').ReadAsArray().astype(np.int16)
    b8A = ps.aperturaDS(work + 'B8A.tif').ReadAsArray().astype(np.int16)
    b08 = ps.aperturaDS(work + 'B08_20.tif').ReadAsArray().astype(np.int16)
    b04 = ps.aperturaDS(work + 'B04.tif').ReadAsArray().astype(np.int16)

    b11 = (b11 - 1000) * 0.0001
    b8A = (b8A - 1000) * 0.0001
    b08 = (b08 - 1000) * 0.0001
    b04 = (b04 - 1000) * 0.0001

    ref = ps.aperturaDS(work + 'B04.tif')

    # Reflectancias escaladas (mismo nombre que en el pipeline).
    # Se quedan en work/ y no se duplican en out/ porque pesan ~120 MB c/u.
    ps.creaTif(ref, b11, work + 'B11_mult.tif')
    ps.creaTif(ref, b8A, work + 'B8A_mult.tif')
    ps.creaTif(ref, b08, work + 'B08_20_mult.tif')
    ps.creaTif(ref, b04, work + 'B04_mult.tif')
    log('Reflectancias escaladas en ' + work + '{B04,B8A,B11,B08_20}_mult.tif')

    # Cada condicion del umbral por separado
    condiciones = [
        ('c1_b8A_gt_0.07', b8A > 0.07),
        ('c2_b04_lt_0.10', b04 < 0.1),
        ('c3_b11_lt_0.05', b11 < 0.05),
        ('c4_b04_lt_b8A', b04 < b8A),
        ('c5_b04_lt_b08', b04 < b08),
    ]
    for nombre, cond in condiciones:
        p = out + '01_umbral_' + nombre + '.tif'
        guardaMascara(ref, cond, p)
        registra('UMBRAL', 'condicion ' + nombre, cond.sum(), p)

    sar = np.where((b8A > 0.07) & (b04 < 0.1) & (b11 < 0.05) &
                   (b04 < b8A) & (b04 < b08), 1, 0).astype(np.uint8)

    # Este es el archivo que consume el resto del pipeline
    ps.creaTif(ref, sar, work + 'alg_tmp_numpy.tif')
    p = out + '02_sargazo_umbral_bruto.tif'
    guardaMascara(ref, sar, p)
    registra('UMBRAL', 'SARGAZO BRUTO (interseccion 5 condiciones)', sar.sum(), p)

    del b11, b8A, b08, b04
    return ref, sar


# ---------------------------------------------------------------------------
# ETAPA B: ENTROPIA
# ---------------------------------------------------------------------------
def etapaEntropia(work, out, ref):
    titulo('3. Entropia sobre B12')
    ini = time.time()
    entropia = ps.entropiaNumpy(work)
    log('Entropia calculada en %.2f min' % ((time.time() - ini) / 60))
    os.system('cp ' + work + 'b12_entropia.tif ' + out + '03_entropia_b12.tif')
    return entropia


# ---------------------------------------------------------------------------
# ETAPA C: FILTRO DE PIXEL DESGLOSADO
# ---------------------------------------------------------------------------
def rasterizaComoRef(pathGeojson, ref, pathOut):
    """Rasteriza un vectorial sobre la misma malla que 'ref' (1 dentro, 0 fuera)."""
    nx, ny, xmin, ymax, xres, yres, xmax, ymin = ps.obtieneParametrosGeoTrasform(ref)
    gdal.Rasterize(pathOut, pathGeojson,
                   options=gdal.RasterizeOptions(
                       outputBounds=[xmin, ymin, xmax, ymax],
                       xRes=abs(xres), yRes=abs(yres),
                       burnValues=[1], initValues=[0],
                       outputType=gdal.GDT_Byte,
                       allTouched=False))
    return gdal.Open(pathOut).ReadAsArray()


def etapaFiltroPixel(work, out, ref, sar, entropia, nubesBajas, SNbuffer):
    titulo('4. Filtro de pixel desglosado (equivalente vectorizado de filtroPixel)')

    scl = ps.aperturaDS(work + 'SCL.tif').ReadAsArray()
    b12 = ps.aperturaDS(work + 'B12.tif').ReadAsArray().astype(np.int16)
    b12 = (b12 - 1000) * 0.0001

    sarB = sar.astype(bool)
    entropiaMin = 4.0
    sombraNube = 0.001

    # --- DETFOO: se rasteriza el poligono para replicar el point-in-polygon ---
    log('Rasterizando MSK_DETFOO_B8A_b1500.geojson sobre la malla del tile...')
    detfoo = rasterizaComoRef(pathLM + 'MSK_DETFOO_B8A_b1500.geojson', ref,
                              out + '04_mask_detfoo_b1500.tif').astype(bool)
    registra('FILTRO_PX', 'DETFOO b1500 (extension del poligono)', detfoo.sum(),
             out + '04_mask_detfoo_b1500.tif')

    mask_ent = entropia >= entropiaMin
    p = out + '05_mask_entropia_ge4.tif'
    guardaMascara(ref, mask_ent, p)
    registra('FILTRO_PX', 'entropia >= 4.0 (todo el tile)', mask_ent.sum(), p)

    # --- Filtro 1: entropia AND detfoo (el que realmente aplica el pipeline) ---
    rm_ent_detfoo = sarB & mask_ent & detfoo
    p = out + '06_ELIMINADO_entropia_y_detfoo.tif'
    guardaMascara(ref, rm_ent_detfoo, p)
    registra('FILTRO_PX', 'ELIMINADO por entropia+DETFOO', rm_ent_detfoo.sum(), p)

    # --- Filtro 2: SCL (solo se evalua si no lo elimino el filtro 1) ---
    mask_scl = np.isin(scl, [3, 8, 9, 10, 11])
    p = out + '07_mask_scl_3_8_9_10_11.tif'
    guardaMascara(ref, mask_scl, p)
    registra('FILTRO_PX', 'SCL en {3,8,9,10,11} (todo el tile)', mask_scl.sum(), p)

    rm_scl = sarB & (~rm_ent_detfoo) & mask_scl
    p = out + '08_ELIMINADO_scl.tif'
    guardaMascara(ref, rm_scl, p)
    registra('FILTRO_PX', 'ELIMINADO por SCL', rm_scl.sum(), p)

    # Desglose de SCL por clase, para saber cual clase pesa mas
    nombresSCL = {3: 'sombra_nube', 8: 'nube_prob_media',
                  9: 'nube_prob_alta', 10: 'cirrus', 11: 'nieve_hielo'}
    for clase, nom in nombresSCL.items():
        m = sarB & (~rm_ent_detfoo) & (scl == clase)
        p = out + '08_ELIMINADO_scl_%02d_%s.tif' % (clase, nom)
        guardaMascara(ref, m, p)
        registra('FILTRO_PX', '  SCL=%d (%s)' % (clase, nom), m.sum(), p)

    # --- Resultado del filtro de pixel (== nubesBajas_mask.tif) ---
    nuMask = (sarB & ~rm_ent_detfoo & ~rm_scl).astype(np.uint8)

    # --- Filtro opcional del pipeline cuando SNbuffer == False ---
    rm_nubes_bin = np.zeros_like(nuMask, dtype=bool)
    if not SNbuffer:
        nubesBin = gdal.Open(work + 'cloudMaskShadow_bin_tmp.tif').ReadAsArray()
        rm_nubes_bin = nuMask.astype(bool) & (nubesBin == 0)
        p = out + '09_ELIMINADO_nubes_sin_buffer.tif'
        guardaMascara(ref, rm_nubes_bin, p)
        registra('FILTRO_PX', 'ELIMINADO por nubes (sin buffer)', rm_nubes_bin.sum(), p)
        nuMask = (nuMask.astype(bool) & ~rm_nubes_bin).astype(np.uint8)

    # Archivo que consume poligonizacion()
    ps.creaTif(ref, nuMask, work + 'nubesBajas_mask.tif')
    p = out + '10_sargazo_post_filtroPixel.tif'
    guardaMascara(ref, nuMask, p)
    registra('FILTRO_PX', 'SOBREVIVE al filtro de pixel', nuMask.sum(), p)

    # --- Filtros DESACTIVADOS en el codigo (solo informativos) ---
    log('')
    log('--- Filtros comentados en filtroPixel (NO se aplican, solo referencia) ---')
    m = sarB & (b12 >= nubesBajas)
    p = out + '11_INFO_nubeBaja_b12_ge_%s.tif' % str(nubesBajas)
    guardaMascara(ref, m, p)
    registra('INFO', 'nube baja B12 >= %s (desactivado)' % nubesBajas, m.sum(), p)

    m = sarB & (b12 <= sombraNube)
    p = out + '12_INFO_sombraNube_b12_le_0.001.tif'
    guardaMascara(ref, m, p)
    registra('INFO', 'sombra nube B12 <= 0.001 (desactivado)', m.sum(), p)

    del scl, b12
    return nuMask


# ---------------------------------------------------------------------------
# ETAPA D: MASCARA DE NUBES (raster + vectorial con buffer)
# ---------------------------------------------------------------------------
def etapaMascaraNubes(work, out, ref, bufferNubes, SNbuffer):
    titulo('5. Mascara de nubes / sombra (buffer = %s m)' % bufferNubes)
    cuadrante = ps.obtieneCuadrante(ref)
    if SNbuffer:
        banderaNub, porcNubeOceano = ps.nubesMascara(
            cuadrante, bufferNubes, work + 'SCL.tif', pathLM, work)
    else:
        banderaNub, porcNubeOceano = ps.nubesMascaraSinBuffer(
            cuadrante, work + 'SCL.tif', pathLM, work)

    log('banderaNubes: %s   porcNubeOceano: %s' % (banderaNub, porcNubeOceano))
    if os.path.exists(work + 'cloudMaskShadow_bin_tmp.tif'):
        os.system('cp ' + work + 'cloudMaskShadow_bin_tmp.tif ' +
                  out + '13_mask_nubes_scl_bin.tif')
    if os.path.exists(work + 'cloudMaskShadow_b250_bin_rec_tmp.json'):
        os.system('cp ' + work + 'cloudMaskShadow_b250_bin_rec_tmp.json ' +
                  out + '14_mask_nubes_buffer%sm.geojson' % bufferNubes)
        # Version raster del buffer, para comparar en QGIS
        rasterizaComoRef(work + 'cloudMaskShadow_b250_bin_rec_tmp.json', ref,
                         out + '14_mask_nubes_buffer%sm.tif' % bufferNubes)
    return banderaNub, porcNubeOceano


# ---------------------------------------------------------------------------
# ETAPA E: VECTORIAL (poligonizacion + mascaras vectoriales desglosadas)
# ---------------------------------------------------------------------------
def etapaVectorial(work, out, ref, tile, anio, fecha, SNbuffer, bufferNubes):
    titulo('6. Poligonizacion y mascaras vectoriales')

    nombre, banderaSar = ps.poligonizacion(tile, anio, fecha, pathLM, work,
                                           work, work)
    if not banderaSar:
        log('No quedo sargazo despues del filtro de pixel: no hay etapa vectorial.')
        return

    df = gpd.read_file(work + 'alg_mask_filter_tmp_sar.json')
    df.to_file(out + '15_poligonos_post_filtroPixel.geojson', driver='GeoJSON')
    registraVector('VECTOR', 'poligonos tras filtro de pixel', df,
                   out + '15_poligonos_post_filtroPixel.geojson')

    # --- Mascara de tierra ---
    df_land = gpd.read_file(pathLM + 'land_2_UTM16N_20m_SPlaya_2021.geojson')
    sin_tierra = gpd.overlay(df, df_land, how='difference')
    sin_tierra.to_file(out + '16_post_mascara_tierra.geojson', driver='GeoJSON')
    registraVector('VECTOR', 'tras restar mascara de TIERRA', sin_tierra,
                   out + '16_post_mascara_tierra.geojson')

    quitado_tierra = gpd.overlay(df, df_land, how='intersection')
    if len(quitado_tierra):
        quitado_tierra.to_file(out + '17_ELIMINADO_por_tierra.geojson', driver='GeoJSON')
        rasterizaComoRef(out + '17_ELIMINADO_por_tierra.geojson', ref,
                         out + '17_ELIMINADO_por_tierra.tif')
    registraVector('VECTOR', 'ELIMINADO por mascara de TIERRA', quitado_tierra,
                   out + '17_ELIMINADO_por_tierra.geojson')

    # --- Mascara de nubes con buffer ---
    resultado = sin_tierra
    if SNbuffer:
        try:
            df_cloud = gpd.read_file(work + 'cloudMaskShadow_b250_bin_rec_tmp.json')
        except Exception:
            df_cloud = None
            log('No se pudo leer la mascara de nubes vectorial; se omite esta etapa.')

        if df_cloud is not None:
            resultado = gpd.overlay(sin_tierra, df_cloud, how='difference')
            resultado.to_file(out + '18_post_mascara_nubes.geojson', driver='GeoJSON')
            registraVector('VECTOR', 'tras restar NUBES buffer %sm' % bufferNubes,
                           resultado, out + '18_post_mascara_nubes.geojson')

            quitado_nubes = gpd.overlay(sin_tierra, df_cloud, how='intersection')
            if len(quitado_nubes):
                quitado_nubes.to_file(out + '19_ELIMINADO_por_nubes.geojson',
                                      driver='GeoJSON')
                rasterizaComoRef(out + '19_ELIMINADO_por_nubes.geojson', ref,
                                 out + '19_ELIMINADO_por_nubes.tif')
            registraVector('VECTOR', 'ELIMINADO por NUBES buffer %sm' % bufferNubes,
                           quitado_nubes, out + '19_ELIMINADO_por_nubes.geojson')

    # --- Resultado final + clasificacion de lugar ---
    if len(resultado):
        resultado['area_km2'] = round(resultado['geometry'].area * 0.000001, 4)
        resultado = ps.verificaLugar(resultado, pathLM)
        resultado.to_file(out + '20_sargazo_FINAL.geojson', driver='GeoJSON')
        rasterizaComoRef(out + '20_sargazo_FINAL.geojson', ref,
                         out + '20_sargazo_FINAL.tif')
        solo_sar = resultado.loc[(resultado['lugar'] == 'oceano') |
                                 (resultado['lugar'] == 'playa')]
        registraVector('VECTOR', 'FINAL (todo)', resultado, out + '20_sargazo_FINAL.geojson')
        registraVector('VECTOR', 'FINAL solo oceano+playa (lo que va a la DB)', solo_sar)
        descartado = resultado.loc[resultado['lugar'] == 'c_aguacont']
        registraVector('VECTOR', 'descartado por lugar = c_aguacont', descartado)
    else:
        log('No quedo ningun poligono despues de las mascaras vectoriales.')


# ---------------------------------------------------------------------------
# VERIFICACION OPCIONAL CONTRA filtroPixel() ORIGINAL
# ---------------------------------------------------------------------------
def verificaContraOriginal(work, out, ref, nubesBajas, entropia, SNbuffer, nuMask):
    titulo('7. Verificacion contra filtroPixel() original (LENTO)')
    dsSar = ps.aperturaDS(work + 'alg_tmp_numpy.tif')
    scl = ps.aperturaDS(work + 'SCL.tif')
    ini = time.time()
    orig = ps.filtroPixel(ref, dsSar, nubesBajas, entropia, scl, SNbuffer, work, pathLM)
    log('filtroPixel original: %.2f min' % ((time.time() - ini) / 60))
    orig = np.asarray(orig)
    dif = (orig.astype(np.uint8) != nuMask)
    p = out + '99_DIFERENCIA_vectorizado_vs_original.tif'
    guardaMascara(ref, dif, p)
    registra('VERIF', 'pixeles distintos vectorizado vs original', dif.sum(), p)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description='Diagnostico de los filtros del algoritmo de sargazo.')
    parser.add_argument('--fecha', default='20260704',
                        help='Fecha del dia en formato YYYYMMDD (default 20260704)')
    parser.add_argument('--tile', default='T16QDH',
                        help='Tile, con la T inicial (default T16QDH)')
    parser.add_argument('--out', default=None, help='Directorio de salida')
    parser.add_argument('--sin-buffer-nubes', dest='sinBuffer', action='store_true',
                        help='Ejecuta con SNbuffer=False')
    parser.add_argument('--sen2cor', action='store_true',
                        help='Corrige el L1C con Sen2Cor si no existe el L2A')
    parser.add_argument('--verifica-filtro', action='store_true',
                        help='Corre tambien el filtroPixel() original y compara (lento)')
    args = parser.parse_args()

    fechaDia = args.fecha.replace('-', '')
    tile = args.tile if args.tile.startswith('T') else 'T' + args.tile
    SNbuffer = not args.sinBuffer

    out = args.out or (pathDiag + tile + '_' + fechaDia + '/')
    if not out.endswith('/'):
        out += '/'
    work = out + 'work/'
    os.system('mkdir -p ' + work)

    iniTotal = time.time()
    titulo('DIAGNOSTICO DE FILTROS  |  tile %s  |  fecha %s  |  SNbuffer=%s'
           % (tile, fechaDia, SNbuffer))
    log('Salida:   ' + out)
    log('Trabajo:  ' + work)

    safe, fecha = localizaL2A(tile, fechaDia, work, args.sen2cor)
    anio = fecha[:4]

    # Porcentaje de nubes -> define nubesBajas y bufferNubes (igual que processing.py)
    porcNube = ps.obtienePorcentajeNube(safe)
    log('Porcentaje de nubes de la escena: %s' % porcNube)
    if porcNube >= 80.0:
        log('AVISO: en produccion esta escena se descartaria por exceso de nubosidad '
            '(>=80%). El diagnostico continua de todas formas.')
    if porcNube >= 30.0:
        nubesBajas = 0.02
        bufferNubes = 300
    else:
        nubesBajas = 0.04
        bufferNubes = 500
    log('nubesBajas = %s   bufferNubes = %s m' % (nubesBajas, bufferNubes))

    convierteBandas(safe, work)
    ref, sar = etapaUmbrales(work, out)
    entropia = etapaEntropia(work, out, ref)

    # La mascara raster de nubes (cloudMaskShadow_bin_tmp.tif) se necesita antes
    # del filtro de pixel cuando SNbuffer == False, igual que en el pipeline.
    banderaNub, porcNubeOceano = etapaMascaraNubes(work, out, ref, bufferNubes, SNbuffer)

    nuMask = etapaFiltroPixel(work, out, ref, sar, entropia, nubesBajas, SNbuffer)
    etapaVectorial(work, out, ref, tile, anio, fecha, SNbuffer, bufferNubes)

    if args.verifica_filtro:
        verificaContraOriginal(work, out, ref, nubesBajas, entropia, SNbuffer, nuMask)

    # ----------------------------------------------------------------------
    # RESUMEN
    # ----------------------------------------------------------------------
    titulo('RESUMEN')
    log('%-10s %-45s %10s %12s' % ('ETAPA', 'DESCRIPCION', 'CANT', 'AREA_KM2'))
    for r in resumen:
        log('%-10s %-45s %10d %12.4f' % (r['etapa'], r['descripcion'],
                                         r['pixeles'], r['area_km2']))

    pathCSV = out + 'resumen_diagnostico.csv'
    with open(pathCSV, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['etapa', 'descripcion', 'pixeles',
                                          'area_km2', 'archivo'])
        w.writeheader()
        w.writerows(resumen)

    log('')
    log('Resumen escrito en: ' + pathCSV)
    log('Rasters y geojson en: ' + out)
    log('El directorio de trabajo NO se borro: ' + work)
    log('Tiempo total: %.2f min' % ((time.time() - iniTotal) / 60))
    log('')
    log('NOTA: este script no escribio en la base de datos ni copio nada a '
        'peta/kawak/web.')


if __name__ == '__main__':
    main()
