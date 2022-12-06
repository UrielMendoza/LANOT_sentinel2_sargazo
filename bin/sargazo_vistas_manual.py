from os import name
import os
import sargazo_vistas
import sargazo_vistas_vertices
from glob import glob
from processing_sentinel2 import obtieneFechaVertice, createMosaicFecha, createMosaicLatest, uneCentroides
import PIL

if __name__ == "__main__":

    # DIRECTORIOS
    pathOutputVistas = '/data/output/sentinel2/vistas/sargazo/sargazo_TC/'
    pathOutputGeoTiff = '/data/output/sentinel2/l2/geotiff/'
    pathOutputWeb = '/home/sargazo/data/'
    pathOutputPeta = '/depot/sentinel2/output/'
    pathVertices = '/data/output/sentinel2/l2/geojson/'
    pathTmp = '/data/input/sentinel2/tmp/manual/'
    pathLanot = '/usr/local/share/lanot/'
    region = 's1'
    
    archivos = glob(pathOutputGeoTiff+'TC/T16QDJ/*')
    fechas = []
    for archivo in archivos:
        fechas.append(obtieneFechaVertice(archivo)) 

    fechas = list(set(fechas))
    fechas.sort()    
    # Manual
    fechas = ['20221129']
    print(fechas)
    for fecha in fechas:
        # Mosaicos
        #createMosaicLatest(fecha,'TC',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb)
        createMosaicFecha(fecha,'TC','TC_2',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,pathTmp)
        createMosaicFecha(fecha,'sargazo','sargazo_2',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,pathTmp)
        # Vistas
        #sargazo_vistas.vistasSargazo(fecha, region, pathTmp, pathOutputGeoTiff, pathVertices, pathOutputVistas, pathLanot, pathOutputPeta, pathOutputWeb)
        #os.system('python3 sargazo_vistas_vertices.py '+fecha+' s1')
        #os.system('python3 sargazo_vistas_vertices.py '+fecha+' s2')
        #uneCentroides(pathVertices+'sargazo_centroides/',fecha,pathVertices+'sargazo_centroides/s1/',pathOutputPeta,pathOutputWeb)

        # Borra Tmp
        os.system('rm -r '+pathTmp+'*.tif')
        os.system('rm -r '+pathTmp+'*json')
        os.system('rm -r '+pathTmp+'*.csv')
        os.system('rm -r '+pathTmp+'*.zip')
        os.system('rm -r '+pathTmp+'*.SAFE')
