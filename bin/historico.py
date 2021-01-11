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
    pathInput = '/data/input/sentinel2/L2A/'
    pathOutput = '/data/output/sentinel2/l2/geojson/sargazo/'
    pathOutputEmpty = '/data/output/sentinel2/l2/geojson/empty/'
    pathOutputGeoTiff = '/data/output/sentinel2/l2/geotiff/sargazo/'
    pathTmp = '/data/input/sentinel2/tmp/historico/'
    pathLM = '../data/masks/'
    pathLog = '../../logs_sentinel2_sargazo/'

    sargazoL2Ahistorico(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathLog,dateTime='historico')

    print("Tiempo de procesamiento: ",time.time()-ini)