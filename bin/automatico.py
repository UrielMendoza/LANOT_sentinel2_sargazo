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
    pathInput = '../test/L2A/'
    pathOutput = '../test/sargazo/geojson/'
    pathOutputEmpty = '../test/sargazo/empty/'
    pathTmp = '../test/tmp/'
    pathLM = '../data/masks/land_sargazo_UTM16N_20m.tif'
    pathLog = '../../logs_sentinel2_sargazo/proc_L2A_sargazo.txt'

    sargazoL2A(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathLog,dateTime='automatico')

    print("Tiempo de procesamiento: ",time.time()-ini)