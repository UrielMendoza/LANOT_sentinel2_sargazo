#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wen Jun 08 15:35:37 2022
@author: urielm
"""

import os
from multiprocessing import Pool
from processing_imagen import descargaImagenes

pathTmp = '/data/input/sentinel2/tmp/automatico/'

# 1. DESCARGA
# DESCARGA IMAGENES
print('3. Descargando imagenes...')
descargaImagenes(pathTmp,dateTime='manual')

# 2. SARGAZO PARALELO
#os.system('export PATH=/home/lanotadm/LANOT_sentinel2_sargazo/bin:$PATH')
pathScript = '/home/lanotadm/LANOT_sentinel2_sargazo/bin/'

# Script para obtencion de sargazo por tile
script_1 = 'python3 '+pathScript+'sargazo_automatico_tile.py'

# Regiones
prueba = ("16QDJ","16QEJ")
#sargazo_1 = ("16QDJ","16QEJ","16QDH","16QEH","16QDG","16QEG","16QDF","16QEF")
#sargazo_2 = ("16QCF","16QCE","16QDE","16QEE","16QCD","16QDD","16QED","16PCC","16PDC","16PEC")
sargazo_3 = ("16QDJ","16QEJ","16QDH","16QEH","16QDG","16QEG","16QDF","16QEF","16QCF","16QCE","16QDE","16QEE","16QCD","16QDD","16QED","16PCC","16PDC","16PEC")
#=========================================================================================================
processes = []
for i in sargazo_3:
    processes.append(script_1+' '+i)
#=========================================================================================================

# Tupla de procesos que entraran a la ejecucion paralela
processes = tuple(processes)

def run_process(process):
    os.system('{}'.format(process))

pool = Pool(processes=len(processes))
pool.map(run_process, processes)