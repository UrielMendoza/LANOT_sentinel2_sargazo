#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

def automatico():
    start_date = datetime.datetime.now()
    end_date = datetime.datetime.now()
    region = "sargazo1"
    landMask = "land_sargazo_UTM16N_20m_b2km.tif"
    nubesBajas = 900
    return start_date,end_date,landMask,nubesBajas

def manual():
    print("=================")
    print("Ejecucion manual")
    print("=================\n")
    #try:
    print("FECHAS")
    print("Inicio")   
    anio1 = input("Año: ")
    mes1 = input("Mes: ")
    dia1 = input("Dia: ")        
    print("Termino")
    anio2 = input("Año: ")
    mes2 = input("Mes: ")
    dia2 = input("Dia: ")            
    start_date = datetime.datetime.strptime(anio1+mes1+dia1,"%Y%m%d")
    end_date = datetime.datetime.strptime(anio2+mes2+dia2,"%Y%m%d")

    print("=================\n")
    print("REGION")
    print("Regiones disponibles establecidas por PATH/ROW: \n1. Cancun\n2. Cancun-Tulum\n3. Sargazo1\n4. Caribe Mexicano\n5. Antillas francesas\n6. Guyana\n")
    while True:
        resR = int(input())
        if resR == 1 or resR == 2 or resR == 3 or resR == 4 or resR == 5 or resR == 6:
            break
    if resR == 1:
        region = "Cancun"
    elif resR == 2:
        region = "Cancun-Tulum"
    elif resR == 3:
        region = "sargazo1"
    elif resR == 4:
        region = "Mexican_Caribbean"
    elif resR == 5:
        region = "French_Antilles"
    elif resR == 6:
        region = "Guyane"

    print("=================\n")
    print("PARAMETROS")
    print("Distancia de Buffer mascara de tierra: \n1. 0km\n2. 2km\n3. 5km\n")
    while True:
        resLM = int(input())
        if resLM == 1 or resLM == 2 or resLM == 3:
            break
    if resLM == 1:
        landMask = "land_sargazo_UTM16N_20m.tif"
    elif resLM == 2:
        landMask = "land_sargazo_UTM16N_20m_b2km.tif"
    elif resLM == 3:
        landMask = "land_sargazo_UTM16N_20m_b5km.tif"

    print("Valor de filtro de nubes bajas banda 4")
    while True:
        nubesBajas = int(input("Valor (sugerido 900): "))
        if nubesBajas >= 900 and nubesBajas <= 1000:
            break
        #if 2015 > int(anio1) > 2020 or 2015 > int(anio2) > 2020 or 1 > int(mes1) > 12 or 1 > int(mes2) > 12:
         #   raise Exception("Fecha no valida")
    #except:
    #    print("Ingrese fecha valida")

    return start_date,end_date,region,landMask,nubesBajas

def sargazoL2A(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathLog,dateTime):

    # MANUAL Y AUTOMATICO
    if dateTime == 'automatico':
        start_date,end_date,region,landMask,nubesBajas = automatico()

    elif dateTime == 'manual':
        start_date,end_date,region,landMask,nubesBajas = manual()

    # OBTIENE NOMBRE DEL LOG
    bufferLM = processing_sentinel2.obtieneBufferLM(landMask)
    if bufferLM == '':
        nomLog = 'proc_L2A_sargazo.txt'
    elif bufferLM == 'b2km':
        nomLog = 'proc_L2A_sargazo_b2km.txt'
    elif bufferLM == 'b5km':
        nomLog = 'proc_L2A_sargazo_b5km.txt'

    # REFERENCIAS BANDAS Y TILES
    bandas = ('B04','B05','B8A','B11','B07','SCL')
    tiles = base.tiles[region]
 
    # DESCARGA
    #print('Sentinel-2\nInicio:',start_date-datetime.timedelta(days=2),'\nTermino:',end_date-datetime.timedelta(days=2))
    print('Sentinel-2\nInicio:',start_date,'\nTermino:',end_date)
    # reste dod dias para prueba
    #download_datasets.search_and_download_datasets(tiles, start_date - datetime.timedelta(days=2), end_date - datetime.timedelta(days=2), pathTmp, unzip=False)
    download_datasets.search_and_download_datasets(tiles, start_date, end_date, pathTmp, unzip=False)
    tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')

    # ALGORITMO
    for tileDir in tilesDirs:
        
        archivos = processing_sentinel2.listaArchivos(tileDir+'/*')
        
        for archivo in archivos:
           
            print('Procesando: '+archivo)

            # COMPRUEBA LOG
            if not processing_sentinel2.verificaLog(pathLog+'proc_L2A_sargazo.txt',archivo):                  
                try:
                    # INICIA PROCESO
                    print('1. Descomprimiendo...')
                    compresion = processing_sentinel2.tipoCompresion(archivo)
                    processing_sentinel2.descomprime(archivo,compresion,pathTmp)

                    fecha = processing_sentinel2.obtieneFecha(archivo)
                    tile = processing_sentinel2.obtieneTile(archivo)
                    anio = processing_sentinel2.obtieneAnio(archivo)
                    dirI = processing_sentinel2.nomDir(archivo,'L2A')
                    
                    os.system('mkdir -p '+pathInput+tile+'/'+anio)
                    os.system('mv '+archivo+' '+pathInput+tile+'/'+anio)

                    #print(fecha)
                    #print(dirI)
                    #print('Procesando bandas...')
                    
                    print('2. Convirtiendo a GeoTIFF...')
                    for banda in bandas:
                        dirB = processing_sentinel2.listaBandas(pathTmp+dirI,'L2A',banda)
                        dsB = processing_sentinel2.aperturaDS(dirB)
                        processing_sentinel2.imgToGeoTIF(dsB,banda,pathTmp)
                    
                    ref = processing_sentinel2.aperturaDS(pathTmp+bandas[0]+'.tif')
                    cuadrante = processing_sentinel2.obtieneCuadrante(ref)
                    
                    print('3. Aplicando algoritmo de deteccion de sargazo...')
                    print('3.1 Procesando mascara tierra...')
                    processing_sentinel2.tierraMascara(cuadrante,pathLM+landMask,pathTmp)
                    print('3.2 Procesando mascara nubes altas...')
                    banderaNub = processing_sentinel2.nubesMascara(cuadrante,pathTmp+bandas[-1]+'.tif',pathTmp)
                    print('3.3 Procesando sargazo sin filtro...')
                    processing_sentinel2.sargazoBin(banderaNub,'L2A',pathTmp,pathTmp)
                    dsSar = processing_sentinel2.aperturaDS(pathTmp+'alg_mask_tmp.tif')
                    print('3.4 Procesando sargazo con filtro...')
                    nuMask = processing_sentinel2.pixelNubesBajas(ref,dsSar,nubesBajas)
                    processing_sentinel2.creaTif(ref,nuMask,pathTmp+'nubesBajas_mask.tif')

                    # POLIGONIZACION
                    print('3.5 Procesando poligonizacion...')            
                    archivoProc = processing_sentinel2.poligonizacion(tile,anio,fecha,bufferLM,pathTmp,pathOutput,pathOutputEmpty)

                    # LOG
                    print('3.6 Añadiendo log...') 
                    fechaLog = processing_sentinel2.obtieneFechaLog()
                    if bufferLM == '':
                        processing_sentinel2.log(pathLog+nomLog,archivo,archivoProc,fechaLog)
                    elif bufferLM == 'b2km':
                        processing_sentinel2.log(pathLog+nomLog,archivo,archivoProc,fechaLog)
                    elif bufferLM == 'b5km':
                        processing_sentinel2.log(pathLog+nomLog,archivo,archivoProc,fechaLog)

                    # COMPUESTO RGB
                    print('4. Creando compuesto RGB...')
                    os.system('mkdir -p '+pathOutputGeoTiff+tile+'/'+anio)                
                    processing_sentinel2.RGB(pathTmp+bandas[2]+'.tif',pathTmp+bandas[1]+'.tif',pathTmp+bandas[0]+'.tif',tile,anio,fecha,pathOutputGeoTiff)

                    # LOG
                    print('4.1 Añadiendo log...')
                    fechaLog = processing_sentinel2.obtieneFechaLog()
                    processing_sentinel2.log(pathLog+'proc_L2A_sargazoGeoTiff.txt',archivo,archivoProc,fechaLog)

                except IndexError:
                    print('Hay un error en la imagen: ', archivo)
                    pass

                finally:
                # BORRA BASURA
                    os.system('rm -r '+pathTmp+'*.tif')
                    os.system('rm -r '+pathTmp+'*.geojson')
                    os.system('rm -r '+pathTmp+'*.json')
                    os.system('rm -r '+pathTmp+'*.SAFE')
                
            else:
                print('Archivo: '+archivo+' ya fue procesado a L2A')

    # BORRA DIR DESCARGA
    os.system('rm -r '+pathTmp+'*')




