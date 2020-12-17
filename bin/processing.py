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

	return start_date,end_date

def manual():
    print("====================================================\n")
    print("Ejecucion manual")
    print("Fecha inicial")
    anio1 = input("Año: ")
    mes1 = input("Mes: ")
    dia1 = input("Dia: ")
    print("Fecha final")
    anio2 = input("Año: ")
    mes2 = input("Mes: ")
    dia2 = input("Dia: ")
    print("====================================================\n")
    start_date = datatime.dateTime.strptime(anio1+mes1+dia1,"%a%m%d")
    end_date = datatime.dateTime.strptime(anio2+mes2+dia2,"%a%m%d")

    return start_date,end_date

def sargazoL2A(pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathLog,dateTime):

    # REFERENCIAS BANDAS Y TILES
    bandas = ('B04','B05','B8A','B11','B07','SCL')
    tiles = base.tiles["sargazo1"]

    # MANUAL Y AUTOMATICO
    if dateTime == 'automatico':
        start_date,end_date = automatico()
    elif dateTime == 'manual':
        start_date,end_date = manual()
    
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
            try:
                print('Procesando: '+archivo)

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
                processing_sentinel2.tierraMascara(cuadrante,pathLM,pathTmp)
                print('3.2 Procesando mascara nubes altas...')
                banderaNub = processing_sentinel2.nubesMascara(cuadrante,pathTmp+bandas[-1]+'.tif',pathTmp)
                print('3.3 Procesando sargazo sin filtro...')
                processing_sentinel2.sargazoBin(banderaNub,'L2A',pathTmp,pathTmp)
                dsSar = processing_sentinel2.aperturaDS(pathTmp+'alg_mask_tmp.tif')
                print('3.4 Procesando sargazo con filtro...')
                nuMask = processing_sentinel2.pixelNubesBajas(ref,dsSar)
                processing_sentinel2.creaTif(ref,nuMask,pathTmp+'nubesBajas_mask.tif')

                # POLIGONIZACION
                print('3.5 Procesando poligonizacion...')            
                archivoProc = processing_sentinel2.poligonizacion(tile,anio,fecha,pathTmp,pathOutput,pathOutputEmpty)

                # LOG
                print('3.6 Añadiendo log...') 
                fechaLog = processing_sentinel2.obtieneFechaLog()
                processing_sentinel2.log(pathLog+'proc_L2A_sargazo.txt',archivo,archivoProc,fechaLog)

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

    # BORRA DIR DESCARGA
    os.system('rm -r '+pathTmp+'*')




