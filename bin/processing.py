
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

def semiManual():
    start_date = None
    end_date = None
    region = "sargazo1"
    landMask = "land_sargazo_UTM16N_20m.tif"
    #nubesBajas = 900
    return start_date,end_date,region,landMask

def automatico():
    start_date = datetime.datetime.now()
    end_date = datetime.datetime.now()
    region = "sargazo1"
    landMask = "land_sargazo_UTM16N_20m.tif"
    #nubesBajas = 900
    return start_date,end_date,region,landMask

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
    print("Regiones disponibles establecidas por PATH/ROW: \n1. Cancun\n2. Cancun-Tulum\n3. Sargazo1\n4. Caribe Mexicano\n5. Antillas francesas\n6. Guyanan\n7. Prueba\n")
    while True:
        resR = int(input())
        if resR == 1 or resR == 2 or resR == 3 or resR == 4 or resR == 5 or resR == 6 or resR == 7:
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

def sargazoL2A(pathInputL1C,pathInput,pathOutput,pathTmp,pathLM,pathOutputEmpty,pathOutputGeoTiff,pathOutputPeta,pathInputPeta,pathVertices,pathLog,dateTime):

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
     
    if dateTime != 'semiManual':
        #try:
        # DESCARGA
        print('1. Descargando...')
        print('Sentinel-2\nInicio:',start_date,'\nTermino:',end_date)
        #download_datasets.search_and_download_datasets(tiles, start_date, end_date, pathTmp, unzip=False)
        
        # Reste dias para prueba
        #print('Sentinel-2\nInicio:',start_date-datetime.timedelta(days=2),'\nTermino:',end_date-datetime.timedelta(days=2))
        #download_datasets.search_and_download_datasets(tiles, start_date - datetime.timedelta(days=2), end_date - datetime.timedelta(days=2), pathTmp, unzip=False)
        #except AttributeError:
        #    print('Error de descarga')
        #    pass
    
    tilesDirs = processing_sentinel2.listaArchivos(pathTmp+'*T16QDJ')

    print(tilesDirs)

    # ALGORITMO
    for tileDir in tilesDirs:
        
        archivos = processing_sentinel2.listaArchivos(tileDir+'/*20210531*')
        archivos.sort()
        
        for archivo in archivos:
            
            ini = time.time()
            print('Procesando: '+archivo)
            fecha = processing_sentinel2.obtieneFecha(archivo)
            tile = processing_sentinel2.obtieneTile(archivo)
            anio = processing_sentinel2.obtieneAnio(archivo)
            dirI = processing_sentinel2.nomDir(archivo,'L2A')
            print("Fecha: "+fecha)
            print("Tile: "+tile)

            # COMPRUEBA LOG
            #if not processing_sentinel2.verificaLog(pathLog+nomLog,archivo):
            if processing_sentinel2.verificaSargazoDB(tile,fecha) == 0:                   
#                try:
                    # INICIA PROCESO
                    print('2. Descomprimiendo...')
                    compresion = processing_sentinel2.tipoCompresion(archivo)
                    processing_sentinel2.descomprime(archivo,compresion,pathTmp)

                    # MANDA A PETA y DATA L1C
                    print('2.1 Moviendo L1C a data y peta...')
                    os.system('mkdir -p '+pathInputL1C+tile+'/'+anio)
                    os.system('cp '+archivo+' '+pathInputL1C+tile+'/'+anio+'/')
                    # MANDA A PETA
                    os.system('scp '+archivo+' lanotadm@stratus:'+pathInputPeta)                   

                    # CORRECCION ATMOSFERICA
                    print('3. Correción atmosferica...')
                    pathSen2core = '../Sen2Cor-02.09.00-Linux64/bin/'
                    pathCFG = '../../sen2cor/2.9/cfg/L2A_GIPP.xml'
                    print(dirI)
                    print(pathTmp)
                    #processing_sentinel2.sen2core(pathSen2core,pathCFG,pathTmp+dirI,pathTmp,'10')
                    l2a = glob(pathTmp+'*MSIL2A*'+fecha+'*'+tile+'*')[0]
                    dirI = processing_sentinel2.nomDir(l2a,'L2A')

                    # COMPRIME Y MUEVE EL L2 CORREGIDO
                    print('3.1 Moviendo L2A a data y peta...')
                    os.system('mkdir -p '+pathInput+tile+'/'+anio)
                    os.system('zip -r '+pathTmp+dirI+'.zip '+pathTmp+dirI)
                    archivol2 = pathInput+tile+'/'+anio+'/'+dirI+'.zip'
                    # MANDA A PETA
                    os.system('scp '+archivol2+' lanotadm@stratus:'+pathOutputPeta+'L2A/')
                    # MANDA A DATA
                    os.system('mv '+pathTmp+dirI+'.zip '+pathInput+tile+'/'+anio)
                    print(l2a)
                    print(dirI)
                    #print(fecha)
                    #print(dirI)

                    # PORCENTAJE DE NUBES
                    print('3.2 Porcentaje de nubes')
                    porcNube = processing_sentinel2.obtienePorcentajeNube(pathTmp+dirI)
                    if porcNube > 80.0 :
                        nubesBajas = 600
                    elif porcNube > 60.0:
                        #nubesBajas = 900
                        nubesBajas = 600
                    else:
                        #nubesBajas = 2500
                        nubesBajas = 600
                    print('Procentaje de nubes ',porcNube)
                    print('Valor de temperatura para filtro nubes bajas: ',nubesBajas)                    
          
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

                    ref = processing_sentinel2.aperturaDS(pathTmp+bandas20m[6]+'.tif')
                    cuadrante = processing_sentinel2.obtieneCuadrante(ref)
                    
                    print('5. Aplicando algoritmo de deteccion de sargazo...')
                    print('5.1 Procesando mascara tierra...')
                    #processing_sentinel2.tierraMascara(cuadrante,pathLM+landMask,pathTmp)
                    print('5.2 Procesando mascara agua...')
                    #processing_sentinel2.aguaMascara(cuadrante,pathTmp+bandas20m[-1]+'.tif',pathTmp)
                    print('5.3 Procesando mascara nubes altas...')
                    #banderaNub = processing_sentinel2.nubesMascara(cuadrante,pathTmp+bandas20m[-1]+'.tif',pathTmp)
                    banderaNub = processing_sentinel2.nubesSombraMascara(cuadrante,pathTmp)
                    print('5.4 Procesando mascara detfoo...')
                    #processing_sentinel2.detfooMascara(200,pathTmp+dirI,pathTmp)
                    print('5.5 Procesando sargazo sin filtro...')
                    #processing_sentinel2.sargazoBin(banderaNub,'L2A',pathTmp,pathTmp)
                    processing_sentinel2.sargazoBinNumpy(pathTmp)
                    dsSar = processing_sentinel2.aperturaDS(pathTmp+'alg_mask_tmp_numpy.tif')
                    print('5.6 Obteniendo entropia...')
                    entropia = processing_sentinel2.entropiaNumpy(pathTmp)
                    print('5.7 Procesando sargazo con filtro...')
                    nuMask = processing_sentinel2.pixelNubesBajasN(ref,dsSar,nubesBajas,entropia)
                    processing_sentinel2.creaTif(ref,nuMask,pathTmp+'nubesBajas_mask.tif')

                    # POLIGONIZACION
                    print('6 Procesando poligonizacion...')
                    archivoProc,banderaSar,totalSar = processing_sentinel2.poligonizacion(tile,anio,fecha,bufferLM,pathLM,pathTmp,pathOutput,pathOutputEmpty)
                    fechaProc = processing_sentinel2.obtieneFechaProc()
                    if banderaSar == True:
                        print('6.1 Aplicando mascara detfoo vectorial...')
                        #processing_sentinel2.detfooMascaraVectorial(pathTmp)
                        print('6.2 Aplicando mascara de tierra vectorial...')
                        banderaSar, totalSarMask, archivoProc = processing_sentinel2.tierraMascaraVectorial(tile,anio,fecha,fechaProc,bufferLM,pathLM,pathTmp,pathOutput,pathOutputEmpty,pathOutputPeta)
                        banderaSar_log = 'si'
                    
                    # BANDERA DE SARGAZO Y AREA TOTAL
                    if banderaSar == True:
                        banderaSar_log = 'si'
                        #totalSar = str((float(totalSar)+ float(totalSarMask))/2)
                        totalSar = totalSarMask
                        #processing_sentinel2.obtieneVertices(archivoProc,pathVertices,pathOutputPeta)
                    else:
                        banderaSar_log = 'no'

                    # COMPUESTO RGB
                    print('7. Creando compuesto RGB...')
                    print('7.1 Creando compuesto RGB FC...')
                    os.system('mkdir -p '+pathOutputGeoTiff+'sargazo/'+tile+'/'+anio)                
                    processing_sentinel2.RGB(pathTmp+bandas20m[4]+'.tif',pathTmp+bandas20m[3]+'.tif',pathTmp+bandas20m[2]+'.tif',tile,anio,fecha,fechaProc,pathOutputGeoTiff,pathOutputPeta)
                    print('7.2 Creando compuesto RGB TC...')
                    os.system('mkdir -p '+pathOutputGeoTiff+'TC/'+tile+'/'+anio)
                    processing_sentinel2.RGB_TC(tile,anio,fecha,fechaProc,'L2A','R20m',pathTmp+dirI,pathOutputGeoTiff,pathOutputPeta)

                    #fechaLog = processing_sentinel2.obtieneFechaLog()
                    #processing_sentinel2.logArchivo(pathLog+'L2A_GeoTiff.csv',fecha,tile,archivo,archivoProc,fechaLog)
                    # BANDERA DE SARGAZO , AREA TOTAL, LOG y DB
                    print('8. Añadiendo a la base de datos y log...')
                    fechaLog = processing_sentinel2.obtieneFechaLog()
                    if banderaSar == True:
                            banderaSar_log = 'si'
                            #totalSar = str((float(totalSar)+ float(totalSarMask))/2)
                            totalSar = totalSarMask
                            processing_sentinel2.obtieneVertices(archivoProc,pathVertices,pathOutputPeta)
                            #processing_sentinel2.logSargazo(pathLog+nomLog,fecha,tile,banderaSar_log,totalSar,archivol2,archivoProc,fechaLog)
                            archivoCSV, crs = processing_sentinel2.creaCSV(archivoProc,pathTmp)
                            processing_sentinel2.agregaSargazoDB(crs,archivol2,archivoProc,fecha,fechaLog,tile,banderaSar_log,totalSar,archivoCSV)
                    else:
                            banderaSar_log = 'no'
                            #processing_sentinel2.logSargazo(pathLog+nomLog,fecha,tile,banderaSar_log,totalSar,archivol2,archivoProc,fechaLog)
                            processing_sentinel2.agregaNoSargazoDB(archivol2,archivoProc,fecha,fechaLog,tile,banderaSar_log,totalSar)

#                except IndexError:
#                except Exception as e:
                    #print('Hay un error en la imagen: ', archivo)
                    #pass
#                    processing_sentinel2.enviaMail(fecha, tile, e)

#                finally:
                # BORRA BASURA
                    #os.system('rm -r '+pathTmp+'*.tif')
                    #os.system('rm -r '+pathTmp+'*.geojson')
                    #os.system('rm -r '+pathTmp+'*.csv')
                    #os.system('rm -r '+pathTmp+'*.json')
                    #os.system('rm -r '+pathTmp+'*.SAFE')
                
            else:
                print('Archivo: '+archivo+' ya fue procesado')

            print("Tiempo de procesamiento: ",time.time()-ini)
 
    # BORRA DIR DESCARGA
    #os.system('rm -r '+pathTmp+'*')




