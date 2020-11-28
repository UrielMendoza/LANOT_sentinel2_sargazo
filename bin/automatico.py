#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
import time
from processing_automatico import sargazoL2A

if __name__ == "__main__":

    ini = time.time()

    # DIRECTORIOS
    pathInput = '/home/urielm/sargazo_lage/1.0/test/L2A/'
    pathOutput = '/home/urielm/sargazo_lage/1.0/test/sargazo/geojson/'
    pathOutputEmpty = '/home/urielm/sargazo_lage/1.0/test/sargazo/empty/'
    pathTmp = '/home/urielm/sargazo_lage/1.0/test/tmp/'
    pathLM = '/home/urielm/sargazo_lage/1.0/data/masks/sargazo1_UTM16N_20m.tif'
    pathLog = '/home/urielm/sargazo_lage/1.0/logs/proc_L2A_sargazo.txt'

    sargazoL2A(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathLog,dateTime='automatico')

    print("Tiempo de procesamiento: ",time.time()-ini)