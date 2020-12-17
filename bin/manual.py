#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
import time
from processing import sargazoL2A
from os import system

if __name__ == "__main__":

 

    # DIRECTORIOS
    pathInput = '../test/L2A/'
    pathOutput = '../test/geojson/sargazo/'
    pathOutputEmpty = '../test/geojson/empty/'
    pathOutputGeoTiff = '../test/geotiff/sargazo/'
    pathTmp = '../test/tmp/automatico/'
    pathLM = '../data/masks/land_sargazo_UTM16N_20m.tif'
    pathLog = '../../logs_sentinel2_sargazo/'

    respuesta = None
    while respuesta != 4:
        print("====================================================\n")
        print("LANOT_sentinel2_sargazo\n")
        print("====================================================\n")
        print("1.Ejecutar manual\n2.Buscar procesados\n3.Cambiar directorios\n4.Salir\n")

        try: 
            respuesta = int(input("Ingrese opcion: "))
            system("clear")

            if respuesta > 4 or respuesta < 0:
                raise Exception("Ingrese opcion valida")
        except (Exception,TypeError):
            system("clear")
            pass

        if respuesta == 1:
            ini = time.time()
            sargazoL2A(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathLog,dateTime='manual')
            print("Tiempo de procesamiento: ",time.time()-ini)
        elif respuesta == 2:
            print('Funcion en construccion...')
        elif respuesta == 3:
            print('Funcion en construccion...')


