
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
    print("Regiones disponibles establecidas por PATH/ROW: \n1. Cancun\n2. Cancun-Tulum\n3. Sargazo1\n4. Caribe Mexicano\n5. Antillas francesas\n6. Guyanan\n7. Prueba\n8. Lupita\n")
    while True:
        resR = int(input())
        if resR == 1 or resR == 2 or resR == 3 or resR == 4 or resR == 5 or resR == 6 or resR == 7 or resR == 8:
            break
    if resR == 1:
        region = "Cancun"
    elif resR == 2:
        region = "Cancun_Tulum"
    elif resR == 3:
        region = "sargazo1"
    elif resR == 4:
        region = "Mexican_Caribbean"
    elif resR == 5:
        region = "French_Antilles"
    elif resR == 6:
        region = "Guyane"
    elif resR == 7:
        region = "Prueba"
    elif resR == 8:
        region = "Lupita3"
    # Opcion PathRow
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
        if nubesBajas >= 500 and nubesBajas <= 2000:
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
    # agrego b02 y b03
    bandas20m = ('B02','B03','B04','B05','B8A','B11','B07','SCL')
    bandas10m = ['B08']
    tiles = base.tiles[region]
 
    # DESCARGA
    #print('Sentinel-2\nInicio:',start_date-datetime.timedelta(days=2),'\nTermino:',end_date-datetime.timedelta(days=2))
    print('Sentinel-2\nInicio:',start_date,'\nTermino:',end_date)
    # reste dod dias para prueba
    #download_datasets.search_and_download_datasets(tiles, start_date - datetime.timedelta(days=2), end_date - datetime.timedelta(days=2), pathTmp, unzip=False)
    #download_datasets.search_and_download_datasets(tiles, start_date, end_date, pathTmp, unzip=False)
    tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')

    # ALGORITMO
    for tileDir in tilesDirs:
        
        archivos = processing_sentinel2.listaArchivos(tileDir+'/*')
        
        for archivo in archivos:
           
            print('Procesando: '+archivo)

            # COMPRUEBA LOG
            if not processing_sentinel2.verificaLog(pathLog+nomLog,archivo):                  
#                try:
                    # INICIA PROCESO
                    print('1. Descomprimiendo...')
                    compresion = processing_sentinel2.tipoCompresion(archivo)
                    processing_sentinel2.descomprime(archivo,compresion,pathTmp)

                    fecha = processing_sentinel2.obtieneFecha(archivo)
                    tile = processing_sentinel2.obtieneTile(archivo)
                    anio = processing_sentinel2.obtieneAnio(archivo)
                    dirI = processing_sentinel2.nomDir(archivo,'L2A')
                    print("fecha y tile"+fecha+' '+tile)

                    # CORRECCION ATMOSFERICA
                    print('2. Correción atmosferica...')
                    pathSen2core_8 = '../Sen2Cor-02.09.00-Linux64/bin/'
                    pathCFG_8 = '../../sen2cor/2.9/cfg/L2A_GIPP.xml'
                    print(dirI)
                    print(pathTmp)
                    processing_sentinel2.sen2core(pathSen2core_8,pathCFG_8,pathTmp+dirI,pathTmp,'10')
                    l2a = glob(pathTmp+'*MSIL2A*'+fecha+'*'+tile+'*')[0]
                    dirI = processing_sentinel2.nomDir(l2a,'L2A')

                    
                    #os.system('mkdir -p '+pathInput+tile+'/'+anio)
                    #os.system('zip -r '+pathTmp+dirI'.zip '+pathTmp+dirI)
                    #os.system('mv '+pathTmp+dirI'.zip '+pathInput+tile+'/'+anio)
                    print(l2a)
                    print(dirI)

                    #print(fecha)
                    #print(dirI)
                    #print('Procesando bandas...')
                    
                    print('3. Convirtiendo a GeoTIFF...')
                    for banda20 in bandas20m:
                        dirB20 = processing_sentinel2.listaBandas(pathTmp+dirI,'L2A','R20m',banda20)
                        dsB20 = processing_sentinel2.aperturaDS(dirB20)
                        processing_sentinel2.imgToGeoTIF(dsB20,banda20,pathTmp)

                    for banda10 in bandas10m:
                        print(banda10)
                        dirB10 = processing_sentinel2.listaBandas(pathTmp+dirI,'L2A','R10m',banda10)
                        dsB10 = processing_sentinel2.aperturaDS(dirB10)
                        processing_sentinel2.imgToGeoTIF(dsB10,banda10,pathTmp)
                        print('2.1. Remuestreando banda '+banda10+' a 20m...')
                        processing_sentinel2.remuestrea(pathTmp+banda10+'_20.tif',dsB10,20,20)

                    ref = processing_sentinel2.aperturaDS(pathTmp+bandas20m[0]+'.tif')
                    cuadrante = processing_sentinel2.obtieneCuadrante(ref)
                    
                    print('4. Aplicando algoritmo de deteccion de sargazo...')
                    print('4.1 Procesando mascara tierra...')
                    #processing_sentinel2.tierraMascara(cuadrante,pathLM+landMask,pathTmp)
                    print('4.1 Procesando mascara agua...')
                    #processing_sentinel2.aguaMascara(cuadrante,pathTmp+bandas20m[-1]+'.tif',pathTmp)
                    print('4.2 Procesando mascara nubes altas...')
                    banderaNub = processing_sentinel2.nubesMascara(cuadrante,pathTmp+bandas20m[-1]+'.tif',pathTmp)
                    print('4.3 Procesando sargazo sin filtro...')
                    #processing_sentinel2.sargazoBin(banderaNub,'L2A',pathTmp,pathTmp)
                    processing_sentinel2.sargazoBinNumpy(pathTmp)
                    dsSar = processing_sentinel2.aperturaDS(pathTmp+'alg_mask_tmp_numpy.tif')
                    print('4.4 Procesando sargazo con filtro...')
                    nuMask = processing_sentinel2.pixelNubesBajas(ref,dsSar,nubesBajas)
                    processing_sentinel2.creaTif(ref,nuMask,pathTmp+'nubesBajas_mask.tif')

                    # POLIGONIZACION
                    print('4.5 Procesando poligonizacion...')
                    archivoProc,banderaSar,totalSar = processing_sentinel2.poligonizacion(tile,anio,fecha,bufferLM,pathTmp,pathOutput,pathOutputEmpty)
                    print('4.6 Aplicando mascara de tierra vectorial...')

                    if banderaSar == True:
                        archivoProc = processing_sentinel2.tierraMascaraVectorial(tile,anio,fecha,bufferLM,pathLM,pathTmp,pathOutput)
                        banderaSar_log = 'si'
                    else:
                        banderaSar_log = 'no'

                     # LOG
                    print('4.7 Aniadiendo log...') 
                    fechaLog = processing_sentinel2.obtieneFechaLog()
                    if bufferLM == '':
                        processing_sentinel2.log(pathLog+nomLog,archivo,archivoProc,fechaLog,banderaSar_log,totalSar)
                    elif bufferLM == 'b2km':
                        processing_sentinel2.log(pathLog+nomLog,archivo,archivoProc,fechaLog,banderaSar_log,totalSar)
                    elif bufferLM == 'b5km':
                        processing_sentinel2.log(pathLog+nomLog,archivo,archivoProc,fechaLog,banderaSar_log,totalSar)

                    # COMPUESTO RGB
                    print('5. Creando compuesto RGB...')
                    print('5.1 Creando compuesto RGB FC...')
                    os.system('mkdir -p '+pathOutputGeoTiff+'sargazo/'+tile+'/'+anio)                
                    processing_sentinel2.RGB(pathTmp+bandas20m[4]+'.tif',pathTmp+bandas20m[3]+'.tif',pathTmp+bandas20m[2]+'.tif',tile,anio,fecha,pathOutputGeoTiff)
                    print('5.2 Creando compuesto RGB TC...')
                    os.system('mkdir -p '+pathOutputGeoTiff+'TC/'+tile+'/'+anio)
                    processing_sentinel2.RGB_TC(tile,anio,fecha,'L2A','R20m',pathTmp+dirI,pathOutputGeoTiff)

                    # LOG
                    print('5.3 Añadiendo log...')
                    fechaLog = processing_sentinel2.obtieneFechaLog()
                    processing_sentinel2.log(pathLog+'proc_L2A_sargazoGeoTiff.txt',archivo,archivoProc,fechaLog,banderaSar_log,totalSar)

#                except IndexError:
                    #print('Hay un error en la imagen: ', archivo)
                    #pass

#                finally:
                # BORRA BASURA
                    os.system('rm -r '+pathTmp+'*.tif')
                    os.system('rm -r '+pathTmp+'*.geojson')
                    os.system('rm -r '+pathTmp+'*.json')
                    os.system('rm -r '+pathTmp+'*.SAFE')
                
            else:
                print('Archivo: '+archivo+' ya fue procesado a L2A')

    # BORRA DIR DESCARGA
    #os.system('rm -r '+pathTmp+'*')




