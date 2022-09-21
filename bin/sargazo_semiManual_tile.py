#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
from os import path
import time
from processing import sargazoL2A
import sys

if __name__ == "__main__":

    # DIRECTORIOS
    pathInputL1C = '/depot/sentinel2/input/L1C/'
    pathInput = '/depot/sentinel2/output/L2A/'
    pathOutput = '/depot/sentinel2/output/l2/geojson/sargazo/'
    pathOutputEmpty = '/depot/sentinel2/output/l2/geojson/sargazo/'
    pathOutputGeoTiff = '/depot/sentinel2/output/l2/geotiff/'
    pathOutputWeb = '/home/sargazo/data/'
    pathOutputPeta = '/depot/sentinel2/output/'
    pathInputPeta = '/depot/sentinel2/input/L1C/'
    pathVertices = '/depot/sentinel2/output/l2/geojson/'
    pathTmp = '/data/input/sentinel2/tmp/semi_manual/'
    pathLM = '../data/masks/'
    pathLog = '../../logs_sentinel2_sargazo/'
    pathOutputVistas = '/depot/sentinel2/output/vistas/sargazo/sargazo_TC/'
    pathSen2cor = '/home/lanotadm/'
    pathLanot = '/usr/local/share/lanot/'

    sargazoL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathSen2cor,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,pathLanot,pathOutputVistas,dateTime='semiManualTile')
