#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
import time
from processing import sargazoL2A
from processing_imagen import imagenL2A, descargaImagenes, mosaicoL2A
from os import system

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
    pathVertices = '/data/output/sentinel2/l2/geojson/'
    pathTmp = '/data/input/sentinel2/tmp/manual/'
    pathLM = '/home/lanotadm/LANOT_sentinel2_sargazo/data/masks/'
    pathSen2cor = '/home/lanotadm/'
    pathLanot = '/usr/local/share/lanot/'
    pathOutputVistas = '/data/output/sentinel2/vistas/sargazo/sargazo_TC/'
    pathLog = '/home/lanotadm/logs_sentinel2_sargazo/'

    respuesta = None
    while respuesta != 4:
        #system("clear")
        print("====================================================\n")
        print("LANOT_sentinel2_sargazo\n")
        print("====================================================\n")
        print("1.Ejecutar manual\n2.Buscar procesados\n3.Cambiar directorios\n4.Salir\n")

        try: 
            respuesta = int(input("Ingrese opcion: "))
            #system("clear")

            if respuesta > 4 or respuesta < 0:
                raise Exception("Ingrese opcion valida")
        except (Exception,TypeError):
            #system("clear")
            pass

        if respuesta == 1:
            #ini = time.time()
            #descargaImagenes(pathTmp,dateTime='manual')
            #imagenL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathSen2cor,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,pathLanot,pathOutputVistas,dateTime='manual')
            #mosaicoL2A(pathTmp,pathInputL1C,pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,dateTime='automaticoTile')
            sargazoL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathSen2cor,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,pathLanot,pathOutputVistas,dateTime='manual')
            #print("Tiempo de procesamiento: ",round((time.time()-ini)/60,2))
            break
        elif respuesta == 2:
            print('Funcion en construccion...')
        elif respuesta == 3:
            print('Funcion en construccion...')


