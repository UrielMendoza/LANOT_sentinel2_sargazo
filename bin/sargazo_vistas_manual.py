from os import name
import os
import sargazo_vistas
import sargazo_vistas_vertices
from glob import glob
from processing_sentinel2 import obtieneFechaVertice
import PIL

if __name__ == "__main__":

    # DIRECTORIOS
    pathOutputVistas = '/data/output/sentinel2/vistas/sargazo/sargazo_TC/'
    pathOutputGeoTiff = '/data/output/sentinel2/l2/geotiff/'
    pathOutputWeb = '/home/sargazo/data/'
    pathOutputPeta = '/depot/sentinel2/output/'
    pathVertices = '/data/output/sentinel2/l2/geojson/sargazo_vertices/'
    pathTmp = '/data/input/sentinel2/tmp/semi_manual/'
    pathLanot = '/usr/local/share/lanot/'
    region = 's1'
    
    archivos = glob(pathVertices+'*20210531*')
    fechas = []
    for archivo in archivos:
        fechas.append(obtieneFechaVertice(archivo)) 

    fechas = list(set(fechas))
    fechas.sort()
    print(fechas)

    for fecha in fechas:
        #sargazo_vistas.vistasSargazo(fecha, region, pathTmp, pathOutputGeoTiff, pathVertices, pathOutputVistas, pathLanot, pathOutputPeta, pathOutputWeb)
        os.system('python3 sargazo_vistas_vertices.py '+fecha)
