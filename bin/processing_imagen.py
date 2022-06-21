
#!/usr/bin/env python3 -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""

import os
import time
import datetime
import sys
from glob import glob
import traceback

import processing_sentinel2
import download_datasets
import base
import sargazo_vistas

def semiManual():
    start_date = None
    end_date = None
    region = "prueba"
    SNbuffer = True
    #landMask = "land_sargazo_UTM16N_20m_1.tif"
    #nubesBajas = 900
    return start_date,end_date,region,SNbuffer

def automaticoTile():
    # Se le resta un dia, porque el servidor en UTC
    daysDelta = 1
    start_date = datetime.datetime.now() - datetime.timedelta(days=daysDelta)
    end_date = datetime.datetime.now()  - datetime.timedelta(days=daysDelta)
    #region = "sargazo_1"
    SNbuffer = True
    #landMask = "land_sargazo_UTM16N_20m_1.tif"
    #nubesBajas = 900
    return start_date,end_date,SNbuffer

def automatico():
    # Se le resta un dia, porque el servidor en UTC
    daysDelta = 1
    start_date = datetime.datetime.now() - datetime.timedelta(days=daysDelta)
    end_date = datetime.datetime.now()  - datetime.timedelta(days=daysDelta)
    region = "sargazo_1"
    SNbuffer = True
    #landMask = "land_sargazo_UTM16N_20m_1.tif"
    #nubesBajas = 900
    return start_date,end_date,region,SNbuffer

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
    print("Regiones disponibles establecidas por PATH/ROW: \n1. sargazo_1\n2. Cancun\n3. Cancun-Tulum\n4. Caribe Mexicano\n5. Antillas francesas\n6. Guyane\n7. Mascara Tierra\n8. sargazo_2\n9. sargazo_3\n10. Prueba")
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
        region = "sargazo_2"
    elif resR == 9:
        region = "sargazo_3"
    elif resR == 10:
        region = "prueba"
    # Opcion PathRow
    #print("=================\n")
    #print("PARAMETROS")
    #print("Distancia de Buffer mascara de tierra: \n1. 0km\n2. 2km\n3. 5km\n")
    #while True:
    #    resLM = int(input())
    #    if resLM == 1 or resLM == 2 or resLM == 3:
    #        break
    #if resLM == 1:
    #    landMask = "land_sargazo_UTM16N_20m_1.tif"
    #elif resLM == 2:
    #    landMask = "land_sargazo_UTM16N_20m_b2km.tif"
    #elif resLM == 3:
    #    landMask = "land_sargazo_UTM16N_20m_b5km.tif"

    #print("Valor de filtro de nubes bajas banda 4")
    #while True:
    #    nubesBajas = int(input("Valor (sugerido 900): "))
    #    if nubesBajas >= 500 and nubesBajas <= 2000:
    #        break
        #if 2015 > int(anio1) > 2020 or 2015 > int(anio2) > 2020 or 1 > int(mes1) > 12 or 1 > int(mes2) > 12:
         #   raise Exception("Fecha no valida")
    #except:
    #    print("Ingrese fecha valida")

    print("=================\n")
    print("Buffer de nubes")
    print("Con buffer de nubes: \n1. Si\n2. No\n")
    while True:
        resBN = int(input())
        if resBN == 1 or resBN == 2:
            break
    if resBN == 1:
        SNbuffer = True
    elif resBN == 2:
        SNbuffer = False

    return start_date,end_date,region,SNbuffer

def mosaicoL2A(pathTmp,pathInputL1C,pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,dateTime):
    fecha = processing_sentinel2.leeLogFecha(pathTmp)
    # MOSAICOS
    # Fechas y buffer
    if dateTime == 'automaticoTile':
        start_date,end_date,SNbuffer = automaticoTile()
    if dateTime == 'automatico':
        start_date,end_date,region,SNbuffer = automatico()
    elif dateTime == 'manual':
        start_date,end_date,region,SNbuffer = manual()
    elif dateTime == 'semiManual':
        start_date,end_date,region,SNbuffer = semiManual()
    # Numero de imagenes
    try:
        if dateTime == 'automaticoTile':
            tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')
        elif dateTime == 'automatico':
            tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')
        elif dateTime == 'manual':
            tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')
        elif dateTime == 'semiManual':
            tilesDirs = processing_sentinel2.listaArchivos(pathInputL1C+'*')
        numImagenes = len(tilesDirs)
        print(tilesDirs)

    except Exception as e:
        print('***Error en listar archivos***')
        processing_sentinel2.agregaErrorSargazoDB('','',start_date.strftime('%Y%m%dT%H%M%S'),'',traceback.format_exc().replace("'",""))
        processing_sentinel2.enviaMail(start_date.strftime('%Y%m%d')+'-'+end_date.strftime('%Y%m%d'),'lista',traceback.format_exc().replace("'",""))
    try:
        if (dateTime == 'automatico' or dateTime == 'automaticoTile') and numImagenes != 0:
            print('9. Procesando mosaico ...')
            # MOSAICO TC
            processing_sentinel2.createMosaicLatest(fecha,'TC',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb)
            # MOSAICO SARGAZO
            processing_sentinel2.createMosaicLatest(fecha,'sargazo',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb)
            # MOSAICO TC
            processing_sentinel2.createMosaicFecha(fecha,'TC',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,pathTmp)
            # MOSAICO SARGAZO
            processing_sentinel2.createMosaicFecha(fecha,'sargazo',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,pathTmp)
            # GENERA VISTA
            #sargazo_vistas.vistasSargazo(fecha, 's1', pathTmp, pathOutputGeoTiff, pathVertices, pathOutputVistas, pathLanot, pathOutputPeta, pathOutputWeb)
            os.system('python3 /home/lanotadm/LANOT_sentinel2_sargazo/bin/sargazo_vistas_vertices.py '+fecha)

        elif (dateTime == 'manual') and numImagenes != 0:
            print('9. Procesando mosaico ...')
            # MOSAICO TC
            processing_sentinel2.createMosaicFecha(fecha,'TC',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,pathTmp)
            # MOSAICO SARGAZO
            processing_sentinel2.createMosaicFecha(fecha,'sargazo',pathOutputGeoTiff,pathOutputPeta,pathOutputWeb,pathTmp)
            # GENERA VISTA
            #sargazo_vistas.vistasSargazo(fecha, 's1', pathTmp, pathOutputGeoTiff, pathVertices, pathOutputVistas, pathLanot, pathOutputPeta, pathOutputWeb)
            #os.system('python3 /home/lanotadm/LANOT_sentinel2_sargazo/bin/sargazo_vistas_vertices.py '+fecha)            

    except Exception as e:
        print('***Error en el mosaico***')
        #pass
        processing_sentinel2.agregaErrorSargazoDB('','',fecha,'',traceback.format_exc().replace("'",""))
        processing_sentinel2.enviaMail(fecha,'mosaico',traceback.format_exc().replace("'",""))

def imagenL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathSen2cor,pathOutputEmpty,pathOutputGeoTiff,pathOutputWeb,pathOutputPeta,pathInputPeta,pathVertices,pathLog,pathLanot,pathOutputVistas,dateTime):

    iniTotal = time.time()
    owd = os.getcwd()

    # MANUAL Y AUTOMATICO
    # Borra el tmp
    if dateTime == 'automatico' or dateTime == 'manual':
        #os.system('rm -r '+pathTmp+'*')
        print('No borra tmp')
    # Fechas y buffer
    if dateTime == 'automaticoTile':
            tiles = sys.argv[1] 
            os.system('mkdir '+pathTmp+tiles)
            pathTmp = pathTmp + tiles +'/'
            start_date,end_date,SNbuffer = automaticoTile()
    if dateTime == 'automatico':
        start_date,end_date,region,SNbuffer = automatico()

    elif dateTime == 'manual':
        start_date,end_date,region,SNbuffer = manual()

    elif dateTime == 'semiManual':
        start_date,end_date,region,SNbuffer = semiManual()

    bandas20m = ('B02','B03','B04','B05','B8A','B11','B12','SCL')
    bandas10m = ['B08']
    if dateTime != 'automaticoTile':
        tiles = base.tiles[region]
    else:
        tiles = tiles.split()
    print(tiles)
    
    if dateTime != 'semiManual':
        try:
            # DESCARGA
            print('1. Descargando...')
            print('Sentinel-2\nInicio:',start_date,'\nTermino:',end_date)
            download_datasets.search_and_download_datasets(tiles, start_date, end_date, pathTmp, unzip=False)

            # Reste dias para prueba
            #print('Sentinel-2\nInicio:',start_date-datetime.timedelta(days=2),'\nTermino:',end_date-datetime.timedelta(days=2))
            #daysDelta = 3
            #download_datasets.search_and_download_datasets(tiles, start_date - datetime.timedelta(days=daysDelta), end_date - datetime.timedelta(days=daysDelta), pathInputL1C, unzip=False)
        except Exception as e:
            print('***Error en la descarga***')
            processing_sentinel2.agregaErrorSargazoDB('','',start_date.strftime('%Y%m%dT%H%M%S'),'',traceback.format_exc().replace("'",""))
            processing_sentinel2.enviaMail(start_date.strftime('%Y%m%d')+'-'+end_date.strftime('%Y%m%d'),'descarga',traceback.format_exc().replace("'",""))
        #    pass
    
    try:
        if dateTime == 'automaticoTile':
            tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')
        elif dateTime == 'automatico':
            tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')
        elif dateTime == 'manual':
            tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*')
        elif dateTime == 'semiManual':
            tilesDirs = processing_sentinel2.listaArchivos(pathInputL1C+'*')
        numImagenes = len(tilesDirs)
        print(tilesDirs)

    except Exception as e:
        print('***Error en listar archivos***')
        processing_sentinel2.agregaErrorSargazoDB('','',start_date.strftime('%Y%m%dT%H%M%S'),'',traceback.format_exc().replace("'",""))
        processing_sentinel2.enviaMail(start_date.strftime('%Y%m%d')+'-'+end_date.strftime('%Y%m%d'),'lista',traceback.format_exc().replace("'",""))

    # ALGORITMO
    for tileDir in tilesDirs:        
        try:
            if dateTime == 'semiManual':
                anioProc = '20220521'
                archivos = processing_sentinel2.listaArchivos(tileDir+'/*'+anioProc+'*')
            else:
                archivos = processing_sentinel2.listaArchivos(tileDir+'/*')
            archivos.sort()
            
        except Exception as e:
            print('***Error en listar archivos***')
            processing_sentinel2.agregaErrorSargazoDB('','',start_date.strftime('%Y%m%dT%H%M%S'),'',traceback.format_exc().replace("'",""))
            processing_sentinel2.enviaMail(start_date.strftime('%Y%m%d')+'-'+end_date.strftime('%Y%m%d'),'lista',traceback.format_exc().replace("'",""))
        
        for archivo in archivos:            
            try:
                iniTProc = time.time()
                print('Procesando: '+archivo)
                fecha = processing_sentinel2.obtieneFecha(archivo)
                fechaImaProc = processing_sentinel2.obtieneFechaImaProc(archivo)
                tile = processing_sentinel2.obtieneTile(archivo)
                anio = processing_sentinel2.obtieneAnio(archivo)
                dirI = processing_sentinel2.nomDir(archivo,'L2A')
                print("Fecha: "+fecha)
                print("Tile: "+tile)   
            except Exception as e:
                print('***Error en obtener datos***')
                processing_sentinel2.agregaErrorSargazoDB(archivo,'',fecha,tile,traceback.format_exc().replace("'",""))
                processing_sentinel2.enviaMail(fecha,tile,traceback.format_exc().replace("'",""))
                continue

            # COMPRUEBA LOG Y TILES
            #if not processing_sentinel2.verificaLog(pathLog+nomLog,archivo):
            if (processing_sentinel2.verificaSargazoDB(tile,fecha) == 0) and not(tile[1:] in tiles == True):                   
                try:
                    #====================
                    # INICIA PROCESO
                    # ===================
                    print('2. Descomprimiendo...')
                    #compresion = processing_sentinel2.tipoCompresion(archivo)
                    processing_sentinel2.descomprime(archivo,pathTmp)

                    # MANDA A PETA y DATA L1C
                    print('2.1 Moviendo L1C a data y peta...')
                    archivol1c = pathInputL1C+tile+'/'+archivo
                    os.system('mkdir -p '+pathInputL1C+tile+'/')
                    os.system('cp '+archivo+' '+pathInputL1C+tile+'/')
                    # MANDA A PETA
                    os.system('scp '+archivo+' lanotadm@stratus:'+pathInputPeta+tile+'/')                   
                except Exception as e:
                    print('***Error en el procesamiento***')
                    #pass
                    processing_sentinel2.agregaErrorSargazoDB(archivol1c,'',fecha,tile,traceback.format_exc().replace("'",""))
                    processing_sentinel2.enviaMail(fecha,tile,traceback.format_exc().replace("'",""))
                    continue
                try:
                    # CORRECCION ATMOSFERICA
                    print('3. Correción atmosferica...')
                    if processing_sentinel2.verificaL2A(tile,fecha,pathInput) == True:
                        # COPIA DE DATA
                        print('=============================================')
                        print('Ya fue corregido anteriormente')
                        print('=============================================')
                        archivoL2A = processing_sentinel2.copiaL2A(tile,fecha,pathInput,pathTmp)
                        processing_sentinel2.descomprime(pathTmp+archivoL2A.split('/')[-1],pathTmp)
                        l2a = glob(pathTmp+'*MSIL2A*'+fecha+'*'+tile+'*.SAFE')[0]
                        dirI = processing_sentinel2.nomDir(l2a,'L2A')
                        archivol2 = pathInput+tile+'/'+dirI.split('.')[0]+'.zip'
                        print(l2a)
                        print(dirI)
                    else:
                        # SEN2COR
                        print('No ha sido corregido atmosfericamente, porcesando con Se2Cor...')
                        pathSen2corBin = pathSen2cor + 'LANOT_sentinel2_sargazo/Sen2Cor-02.10.01-Linux64/bin/'
                        pathCFG = pathSen2cor + 'sen2cor/2.10/cfg/L2A_GIPP.xml'
                        processing_sentinel2.sen2cor(pathSen2corBin,pathCFG,pathTmp+dirI,pathTmp,'10')
                        # COMPRIME Y MUEVE EL L2 CORREGIDO
                        print('3.1 Moviendo L2A a data y peta...')
                        #print(pathTmp)
                        l2a = glob(pathTmp+'*MSIL2A*'+fecha+'*'+tile+'*.SAFE')[0]
                        dirI = processing_sentinel2.nomDir(l2a,'L2A')
                        print(l2a)
                        print(dirI)
                        # MANDA A DATA
                        os.system('mkdir -p '+pathInput+tile+'/')
                        os.chdir(pathTmp)
                        os.system('zip -r '+dirI.split('.')[0]+'.zip '+dirI)
                        os.system('cp '+pathTmp+dirI.split('.')[0]+'.zip '+pathInput+tile+'/')
                        archivol2 = pathInput+tile+'/'+dirI.split('.')[0]+'.zip'
                        # MANDA A PETA
                        os.system('scp '+pathTmp+dirI.split('.')[0]+'.zip lanotadm@stratus:'+pathOutputPeta+'L2A/'+tile+'/')
                        #print(fecha)
                        #print(dirI)
                except Exception as e:
                    print('***Error en el procesamiento***')
                    #pass
                    processing_sentinel2.agregaErrorSargazoDB(archivol1c,'',fecha,tile,traceback.format_exc().replace("'",""))
                    processing_sentinel2.enviaMail(fecha,tile,traceback.format_exc().replace("'",""))
                    continue
                try:
                    os.chdir(owd)
                    # PORCENTAJE DE NUBES
                    print('3.2 Porcentaje de nubes')
                    porcNube = processing_sentinel2.obtienePorcentajeNube(pathTmp+dirI)
                    print('Procentaje de nubes ',porcNube)              
          
                    print('4. Convirtiendo a GeoTIFF...')
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

                    # COMPUESTO RGB
                    print('7. Creando compuesto RGB...')
                    print('7.1 Creando compuesto RGB FC...')
                    os.system('mkdir -p '+pathOutputGeoTiff+'sargazo/'+tile+'/')                
                    processing_sentinel2.RGB(pathTmp+bandas20m[4]+'.tif',pathTmp+bandas20m[3]+'.tif',pathTmp+bandas20m[2]+'.tif',tile,anio,fecha,fechaImaProc,pathOutputGeoTiff,pathOutputPeta)
                    print('7.2 Creando compuesto RGB TC...')
                    os.system('mkdir -p '+pathOutputGeoTiff+'TC/'+tile+'/')
                    processing_sentinel2.RGB_TC(tile,anio,fecha,fechaImaProc,'L2A','R10m',pathTmp+dirI,pathOutputGeoTiff,pathOutputPeta)
  
#                except IndexError:
                except Exception as e:
                    print('***Error en el procesamiento***')
                    #pass
                    processing_sentinel2.agregaErrorSargazoDB(archivol1c,archivol2,fecha,tile,traceback.format_exc().replace("'",""))
                    processing_sentinel2.enviaMail(fecha,tile,traceback.format_exc().replace("'",""))
                    continue

                finally:
                # BORRA BASURA
                    os.system('rm -r '+pathTmp+'*.tif')
                    os.system('rm -r '+pathTmp+'*json')
                    os.system('rm -r '+pathTmp+'*.csv')
                    os.system('rm -r '+pathTmp+'*.zip')
                    os.system('rm -r '+pathTmp+'*.SAFE')
                    #if dateTime == 'automatico' or dateTime == 'manual':
                    #    os.system('rm -r '+pathTmp+'*')
                
            else:
                print('======================================')
                print('Archivo: '+archivo+' ya fue procesado')
                print('======================================')
    # Guarda fecha en un log para el mosaico
    processing_sentinel2.logFecha(fecha,'/'.join(pathTmp.split('/')[:-2])+'/')
    print("Tiempo de procesamiento total: ",round((time.time()-iniTotal)/60,2))
    # BORRA DIR DESCARGA
    # NO DESCOMENTAR EN SEMIMANUAL PORQUE BORRA IMAGENES
    if dateTime == 'automatico' or dateTime == 'manual':
       os.system('rm -r '+pathTmp+'*')




