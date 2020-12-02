from glob import glob
import os
import sys
from processing_sentinel2 import obtieneTile,obtieneArchivoZip,obtieneAnio

pathInput = '/data/input/sentinel2/depot/'+sys.argv[1]+'/'
print(pathInput)
pathOutput = '/data/input/sentinel2/L1C/'
dirPrin = glob(pathInput+'*')

for i in dirPrin:
	subDir = glob(i+'/*')
	for archivo in subDir:
		print(archivo)
		tile = obtieneTile(archivo)
		anio = obtieneAnio(archivo)
		print(tile)
		print(anio)
		if '.zip' in archivo:
		    os.system('mkdir -p '+pathOutput+tile+'/'+anio)
		    os.system('cp '+archivo+' '+pathOutput+tile+'/'+anio)
		elif '.SAFE' in archivo:
                    archivoZip = obtieneArchivoZip(archivo)
                    os.system('mkdir -p '+pathOutput+tile+'/'+anio)
                    os.system('cd '+'/'.join(archivo.split('/')[:-1])+';zip -r '+archivoZip+' '+archivo.split('/')[-1]+';mv '+archivoZip+' '+pathOutput+tile+'/'+anio)

