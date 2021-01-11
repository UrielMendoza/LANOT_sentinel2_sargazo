#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 11 23:52:19 2021

@author: urielm
"""
import time
from processing_historico import sargazoL2Ahistorico

if __name__ == "__main__":

    ini = time.time()

    # DIRECTORIOS
    pathInput = '../test/L2A/'
    pathOutput = '../test/geojson/sargazo/'
    pathOutputEmpty = '../test/geojson/empty/'
    pathOutputGeoTiff = '../test/geotiff/sargazo/'
    pathTmp = '../test/tmp/automatico/'
    pathLM = '../data/masks/'
    pathLog = '../../logs_sentinel2_sargazo/'

    sargazoL2Ahistorico(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathLog,dateTime='historico')

    print("Tiempo de procesamiento: ",time.time()-ini)