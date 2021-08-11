#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
import time
from processing import sargazoL2A

if __name__ == "__main__":

    # DIRECTORIOS
    pathInput = '/data/output/sentinel2/msi/L2A/'
    pathOutput = '/data/output/sentinel2/msi/l2/geojson/sargazo/'
    pathOutputEmpty = '/data/output/sentinel2/msi/l2/geojson/sargazo/'
    pathOutputGeoTiff = '/data/output/sentinel2/msi/l2/geotiff/'
    pathOutputPeta = '/depot/sentinel2/output/msi/'
    pathInputPeta = '/depot/sentinel2/input/L1C/'
    pathVertices = '/data/output/sentinel2/msi/l2/geojson/sargazo_vertices/'
    pathTmp = '../test/tmp/manual/'
    pathLM = '../data/masks/'
    pathLog = '../../logs_sentinel2_sargazo/'

    sargazoL2A(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathOutputPeta,pathInputPeta,pathVertices,pathLog,dateTime='semiManual')
