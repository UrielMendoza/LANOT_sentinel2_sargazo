#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wen Jun 08 15:35:37 2022
@author: urielm
"""

import os
from multiprocessing import Pool
from processing_imagen import descargaImagenes, imagenL2A, mosaicoL2A


pathInputL1C = '/depot/sentinel2/input/L1C/'
pathInput = '/depot/sentinel2/output/L2A/'
pathOutput = '/depot/sentinel2/output/l2/geojson/sargazo/'
pathOutputEmpty = '/depot/sentinel2/output/l2/geojson/sargazo/'
pathOutputGeoTiff = '/depot/sentinel2/output/l2/geotiff/'
pathOutputWeb = '/home/sargazo/data/'
pathOutputPeta = '/depot/sentinel2/output/'
pathInputPeta = '/depot/sentinel2/input/L1C/'
pathVertices = '/depot/sentinel2/output/sentinel2/l2/geojson/sargazo_vertices/'
pathTmp = '/data/input/sentinel2/tmp/semi_manual/'
pathLM = '../data/masks/'
pathLog = '../../logs_sentinel2_sargazo/'
pathOutputVistas = '/depot/sentinel2/output/vistas/sargazo/sargazo_TC/'
pathSen2cor = '/home/lanotadm/'
pathLanot = '/usr/local/share/lanot/'


# 1. DESCARGA
# DESCARGA IMAGENES
print('1. Descargando imagenes...')
#descargaImagenes(pathInputPeta,dateTime='semiManual')

# 2. CORRECION ATMOSFERICA
print('2. Correcion atmosferica...')
#imagenL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathSen2cor,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,pathLanot,pathOutputVistas,dateTime='semiManual')

# 3. SARGAZO PARALELO
print('3 Procesando sargazo en paralelo...')
#os.system('export PATH=/home/lanotadm/LANOT_sentinel2_sargazo/bin:$PATH')
pathScript = '/home/lanotadm/LANOT_sentinel2_sargazo/bin/'

# Script para obtencion de sargazo por tile
script_1 = 'python3 '+pathScript+'sargazo_semiManual_tile.py'

# Regiones
prueba = ("16QDJ","16QEJ")
#sargazo_1 = ("16QDJ","16QEJ","16QDH","16QEH","16QDG","16QEG","16QDF","16QEF")
#sargazo_2 = ("16QCF","16QCE","16QDE","16QEE","16QCD","16QDD","16QED","16PCC","16PDC","16PEC")
sargazo_3 = ("16QDJ","16QEJ","16QDH","16QEH","16QDG","16QEG","16QDF","16QEF","16QCF","16QCE","16QDE","16QEE","16QCD","16QDD","16QED","16PCC","16PDC","16PEC")
#=========================================================================================================
processes = []
for i in prueba:
    processes.append(script_1+' '+i)
#=========================================================================================================

# Tupla de procesos que entraran a la ejecucion paralela
processes = tuple(processes)

def run_process(process):
    os.system('{}'.format(process))

pool = Pool(processes=len(processes))
pool.map(run_process, processes)