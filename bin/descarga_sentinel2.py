
#!/usr/bin/env python3 -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""

import os
import time
import datetime
import processing_sentinel2
import download_datasets
import base
import sys
from glob import glob
import traceback

def semiManual():
    start_date = None
    end_date = None
    region = "sargazo_1"
    landMask = "land_sargazo_UTM16N_20m_1.tif"
    #nubesBajas = 900
    return start_date,end_date,region,landMask

def automatico():
    start_date = datetime.datetime.now()
    end_date = datetime.datetime.now()
    region = "sargazo_1"
    landMask = "land_sargazo_UTM16N_20m_1.tif"
    #nubesBajas = 900
    return start_date,end_date,region,landMask

def manual():
    print("=================")
    print("Descarga Sentinel-2")
    print("=================\n")
    #try:
    print("=================\n")
    print("FECHAS")
    print("Seleccione tipo de fechas: \n1. Por dia\n2. Por intervalo de dias\n")
    while True:
        resF = int(input())
        if resF == 1 or resF:
            break
    if resF == 1:
        print("Fecha de dia")   
        anio1 = input("Anio: ")
        mes1 = input("Mes: ")
        dia1 = input("Dia: ")        
        anio2 = anio1
        mes2 = mes1
        dia2 = dia1            
        start_date = datetime.datetime.strptime(anio1+mes1+dia1,"%Y%m%d")
        end_date = datetime.datetime.strptime(anio2+mes2+dia2,"%Y%m%d")
    elif resF == 2:
        print("Intervalo de dias")
        print("Inicio")   
        anio1 = input("Anio: ")
        mes1 = input("Mes: ")
        dia1 = input("Dia: ")        
        print("Termino")
        anio2 = input("Anio: ")
        mes2 = input("Mes: ")
        dia2 = input("Dia: ")            
        start_date = datetime.datetime.strptime(anio1+mes1+dia1,"%Y%m%d")
        end_date = datetime.datetime.strptime(anio2+mes2+dia2,"%Y%m%d")
    # Catalogo de dias 
    print("=================\n")
    print("REGION")
    print("Regiones disponibles establecidas por PATH/ROW: \n1. sargazo_1\n2. Cancun\n3. Cancun-Tulum\n4. Caribe Mexicano\n5. Antillas francesas\n6. Guyane\n7. Mascara Tierra\n8.prueba\n9. sargazo_2\n10. sargazo_3\n")
    while True:
        resR = int(input())
        if resR == 1 or resR == 2 or resR == 3 or resR == 4 or resR == 5 or resR == 6 or resR == 7 or resR == 8 or resR == 9 or resR == 10:
            break
    if resR == 1:
        region = "sargazo_1"
    elif resR == 2:
        region = "cancun"
    elif resR == 3:
        region = "cancun_tulum"
    elif resR == 4:
        region = "mexican_caribbean"
    elif resR == 5:
        region = "french_antilles"
    elif resR == 6:
        region = "guyane"
    elif resR == 7:
        region = "mascara_tierra"
    elif resR == 8:
        region = "prueba"
    elif resR == 9:
        region = "sargazo_2"
    elif resR == 10:
        region = "sargazo_3"
    # Opcion PathRow
    print("=================\n")
    print("PARAMETROS")
    print("Distancia de Buffer mascara de tierra: \n1. 0km\n2. 2km\n3. 5km\n")
    while True:
        resLM = int(input())
        if resLM == 1 or resLM == 2 or resLM == 3:
            break
    if resLM == 1:
        landMask = "land_sargazo_UTM16N_20m_1.tif"
    elif resLM == 2:
        landMask = "land_sargazo_UTM16N_20m_b2km.tif"
    elif resLM == 3:
        landMask = "land_sargazo_UTM16N_20m_b5km.tif"

    #print("Valor de filtro de nubes bajas banda 4")
    #while True:
    #    nubesBajas = int(input("Valor (sugerido 900): "))
    #    if nubesBajas >= 500 and nubesBajas <= 2000:
    #        break
        #if 2015 > int(anio1) > 2020 or 2015 > int(anio2) > 2020 or 1 > int(mes1) > 12 or 1 > int(mes2) > 12:
         #   raise Exception("Fecha no valida")
    #except:
    #    print("Ingrese fecha valida")

    return start_date,end_date,region,landMask

def sargazoL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,dateTime):

    iniTotal = time.time()
    owd = os.getcwd()

    # MANUAL Y AUTOMATICO
    if dateTime == 'automatico':
        start_date,end_date,region,landMask = automatico()

    elif dateTime == 'manual':
        start_date,end_date,region,landMask = manual()

    elif dateTime == 'semiManual':
        start_date,end_date,region,landMask = semiManual()

    # OBTIENE NOMBRE DEL LOG
    bufferLM = processing_sentinel2.obtieneBufferLM(landMask)
    if bufferLM == '':
        nomLog = 'L2A_sargazo.csv'
    elif bufferLM == 'b2km_':
        nomLog = 'L2A_sargazo_b2km.csv'
    elif bufferLM == 'b5km_':
        nomLog = 'L2A_sargazo_b5km.csv'

    # REFERENCIAS BANDAS Y TILES
    # agrego b02 y b03
    bandas20m = ('B02','B03','B04','B05','B8A','B11','B12','SCL')
    bandas10m = ['B08']
    tiles = base.tiles[region]
    print(tiles)
    
    if dateTime != 'semiManual':
        try:
            # DESCARGA
            print('1. Descargando...')
            print('Sentinel-2\nInicio:',start_date,'\nTermino:',end_date)
            #download_datasets.search_and_download_datasets(tiles, start_date, end_date, pathInputL1C, unzip=False)

            # Reste dias para prueba
            #print('Sentinel-2\nInicio:',start_date-datetime.timedelta(days=2),'\nTermino:',end_date-datetime.timedelta(days=2))
            daysDelta = 1
            download_datasets.search_and_download_datasets(tiles, start_date - datetime.timedelta(days=daysDelta), end_date - datetime.timedelta(days=daysDelta), pathInputL1C, unzip=False)
        except Exception as e:
            print('***Error en la descarga***')
            processing_sentinel2.agregaErrorSargazoDB('','',start_date.strftime('%Y%m%dT%H%M%S'),'',traceback.format_exc().replace("'",""))
            processing_sentinel2.enviaMail(start_date.strftime('%Y%m%d')+'-'+end_date.strftime('%Y%m%d'),'descarga',traceback.format_exc().replace("'",""))
        #    pass
        #             
    print("Tiempo de procesamiento total: ",round((time.time()-iniTotal)/60,2))


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
    pathVertices = '/depot/sentinel2/output/sentinel2/l2/geojson/sargazo_vertices/'
    pathTmp = '/data/input/sentinel2/tmp/manual/'
    pathLM = '../data/masks/'
    pathLog = '../../logs_sentinel2_sargazo/'
    pathOutputVistas = '/depot/sentinel2/output/vistas/sargazo/sargazo_TC/'

    sargazoL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,dateTime='manual')



