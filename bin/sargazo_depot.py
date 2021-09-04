from glob import glob
import os
import sys
from processing_sentinel2 import obtieneTile,obtieneAnio

pathInput = '/data/input/sentinel2/depot/'
pathOutput = '/data/input/sentinel2/L1C/'

archivos = glob(pathInput+'*.zip')

for archivo in archivos:

    print(archivo)
    tile = obtieneTile(archivo)
    anio = obtieneAnio(archivo)
    print(tile)
    print(anio)
    if '.zip' in archivo:
        os.system('mkdir -p '+pathOutput+tile+'/')
        os.system('mv '+archivo+' '+pathOutput+tile+'/')

