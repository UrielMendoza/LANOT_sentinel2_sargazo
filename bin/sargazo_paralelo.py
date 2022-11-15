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
print('1. Descargando imagenes...')
descargaImagenes(pathTmp,dateTime='automatico')

# 2. SARGAZO PARALELO
print('2 Procesando sargazo en paralelo...')
#os.system('export PATH=/home/lanotadm/LANOT_sentinel2_sargazo/bin:$PATH')
pathScript = '/home/lanotadm/LANOT_sentinel2_sargazo/bin/'

# Script para obtencion de sargazo por tile
script_1 = 'python3 '+pathScript+'sargazo_automatico_tile.py'

# Regiones
prueba = ("16QDJ","16QEJ")
#sargazo_1 = ("16QDJ","16QEJ","16QDH","16QEH","16QDG","16QEG","16QDF","16QEF")
#sargazo_2 = ("16QCF","16QCE","16QDE","16QEE","16QCD","16QDD","16QED","16PCC","16PDC","16PEC")
#sargazo_3 = ("16QDJ","16QEJ","16QDH","16QEH","16QDG","16QEG","16QDF","16QEF","16QCF","16QCE","16QDE","16QEE","16QCD","16QDD","16QED","16PCC","16PDC","16PEC")
sargazo_6 = ("20QME","20QNE","20QPE","20QQE","20QRE","20QMD","20QND","20QPD","20QQD","20QRD","20PMC","20PNC","20PPC","20PQC","20PRC","20PMB","20PNB","T20PPB","20PQB","20PRB","20PMA","20PNA","20PPA","20PQA","20PRA","20PPV","20PPU","20PPT","20PPS","20PQV","20PQU","20PQT","20PQS","20PRV","20PRU","20PRT","20PRS","21QTV","21QTU","21PTT","21PTS","21PTR","21PTQ","21PTP","21PTN","21PTM","21PUQ","21PUP","21PUN","21PUM")
#=========================================================================================================
processes = []
cont = 0
for i in sargazo_6:
    processes.append('sleep '+str(cont)+' && '+script_1+' '+i)
    cont += 3
#=========================================================================================================

# Tupla de procesos que entraran a la ejecucion paralela
processes = tuple(processes)

def run_process(process):
    os.system('{}'.format(process))

pool = Pool(processes=len(processes))
pool.map(run_process, processes)