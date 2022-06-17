#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
from os import path
import time
from processing import sargazoL2A
from processing_imagen import imagenL2A
import sys

if __name__ == "__main__":

    # DIRECTORIOS
    pathInputL1C = '/data/input/sentinel2/L1C/'
    pathInput = '/data/output/sentinel2/L2A/'
    pathOutput = '/data/output/sentinel2/l2/geojson/sargazo/'
    pathOutputEmpty = '/data/output/sentinel2/l2/geojson/sargazo/'
    pathOutputGeoTiff = '/data/output/sentinel2/l2/geotiff/'
    pathOutputWeb = '/home/sargazo/data/'
    pathOutputPeta = '/depot/sentinel2/output/'
    pathInputPeta = '/depot/sentinel2/input/L1C/'
    pathVertices = '/data/output/sentinel2/l2/geojson/sargazo_vertices/'
    pathTmp = '/data/input/sentinel2/tmp/automatico/'
    pathLM = '/home/lanotadm/LANOT_sentinel2_sargazo/data/masks/'
    pathSen2cor = '/home/lanotadm/'
    pathLanot = '/usr/local/share/lanot/'
    pathOutputVistas = '/data/output/sentinel2/vistas/sargazo/sargazo_TC/'
    pathLog = '/home/lanotadm/logs_sentinel2_sargazo/'

imagenL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathSen2cor,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,pathLanot,pathOutputVistas,dateTime='automaticoTile')
