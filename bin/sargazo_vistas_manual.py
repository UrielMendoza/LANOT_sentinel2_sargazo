from os import name
import sargazo_vistas
from glob import glob
from processing_sentinel2 import obtieneFechaVertice

if __name__ == "__main__":

    # DIRECTORIOS
    pathOutputVistas = '/data/output/sentinel2/vistas/sargazo/sargazo_TC/'
    pathOutputGeoTiff = '/data/output/sentinel2/l2/geotiff/'
    pathOutputWeb = '/home/sargazo/data/vistas/sargazo_TC'
    pathOutputPeta = '/depot/sentinel2/output/vistas/sargazo_TC/'
    pathVertices = '/data/output/sentinel2/l2/geojson/sargazo_vertices/'
    pathTmp = '/data/input/sentinel2/tmp/semi_manual/'
    pathLanot = '/usr/local/share/lanot/'
    region = 's1'
    
    archivos = glob(pathVertices+'*')
    fechas = []
    for archivo in archivos:
        fechas.append(obtieneFechaVertice(archivo)) 

    fechas = list(set(fechas))
    print(fechas)
    fechas.sort()

    for fecha in fechas:
        sargazo_vistas.vistasSargazo(fecha, region, pathTmp, pathOutputGeoTiff, pathVertices, pathOutputVistas, pathLanot, pathOutputPeta, pathOutputWeb)