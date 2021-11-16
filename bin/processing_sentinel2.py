#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
import os,time
from glob import glob
from osgeo import gdal,osr
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon,Point,LineString,MultiPoint
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
import datetime
import numpy as np
import matplotlib.pyplot as plt
from xml.dom import minidom
from skimage import data
from skimage.util import img_as_ubyte
from skimage.filters.rank import entropy
from skimage.morphology import disk
import psycopg2
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
import traceback

def obtienePorcentajeNube(pathInput):
    mydoc = minidom.parse(pathInput+'/MTD_MSIL2A.xml')
    items = mydoc.getElementsByTagName('n1:Quality_Indicators_Info')
    porcNube = float(items[0].getElementsByTagName('Cloud_Coverage_Assessment')[0].firstChild.nodeValue)
    return porcNube

def obtieneBufferLM(landMask):
    if landMask != "land_sargazo_UTM16N_20m.tif":
        bufferLM = landMask.split('.')[0].split('_')[-1]
    else:
        bufferLM = ''    
    return bufferLM

def obtieneArchivoZip(pathArchivo):
    archivo = pathArchivo.split('/')[-1].split('.')[0]+'.zip'
    return archivo

def sen2cor(pathSen2Cor,pathCFG,pathInput,pathOutput,resolution):
    os.system(pathSen2Cor+'L2A_Process --resolution '+resolution+' --GIP_L2A '+pathCFG+' --output_dir '+pathOutput+' '+pathInput)

def verificaLog(pathLog,archivo):
    file = open(pathLog,'r')
    lines = file.readlines()
    for i in lines:
        if archivo in i:
            return True
    file.close
    return False

def logSargazo(pathLog,fecha,tile,banderaSar,totalSar,archivo,archivoProc,fechaProc):
        file = open(pathLog,'a')
        file.write(fecha+','+tile+','+banderaSar+','+totalSar+','+archivo+','+archivoProc+','+fechaProc+'\n')
        file.close

def logArchivo(pathLog,fecha,tile,archivo,archivoProc,fechaProc):
        file = open(pathLog,'a')
        file.write(fecha+','+tile+','+archivo+','+archivoProc+','+fechaProc+'\n')
        file.close

def obtieneTile(pathArchivo):
    tile = pathArchivo.split('/')[-1].split('_')[5]
    return tile

def obtieneAnio(path):
   anio = path.split('/')[-1].split('_')[2][:4]
   return anio

def obtieneFechaLog():
   fecha = datetime.datetime.now().strftime('%Y-%m-%-dT%H:%M')
   return fecha

def obtieneFechaProc():
   fecha = datetime.datetime.now()
   return fecha.strftime('%Y%m%dT%H%M%S')

def listaArchivos(pathInput):
    archivos = glob(pathInput)
    return archivos

def listaBandas(pathInput,nivel,resolucion,banda):
    if nivel == 'L2A':
        archivoBanda = glob(pathInput+'/GRANULE/L2*/IMG_DATA/'+resolucion+'/*'+banda+'*.jp2')
    elif nivel == 'L1C':
        archivoBanda = glob(pathInput+'/GRANULE/L1C*/IMG_DATA/*.jp2')
    elif nivel == 'L1C_resampled':
        archivoBanda = glob(pathInput+'/'+banda+'.img')
    print("Archivo usado:"+archivoBanda[0])
    return archivoBanda[0]

def remplazaProcesado(nombre,tile,fecha):
    archivo = glob('')    

def tipoCompresion(pathInput):
    compresion = pathInput.split('/')[-1].split('.')[-1]
    return compresion

def nomDir(pathInput,nivel):
    archivo = pathInput.split('/')[-1].split('.')[0]
    if nivel == 'L2A':
        return archivo+'.SAFE'
    elif nivel == 'L1C':
        return archivo+'.SAFE'
    elif nivel == 'L1C_resampled':
        return archivo+'.resampled.data'

def nomDirQuality(pathInput,maskQuality):
    archivoQuality = glob(pathInput+'/GRANULE/L2*/QI_DATA/'+maskQuality)
    archivoQuality = archivoQuality[0]
    return archivoQuality

def obtieneFecha(pathDir):
    fecha = pathDir.split('/')[-1].split('.')[0].split('_')[2]
    fecha = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    return fecha.strftime('%Y%m%dT%H%M%S')

def obtieneFechaImaProc(pathDir):
    fecha = pathDir.split('/')[-1].split('.')[0].split('_')[-1]
    #fecha = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    return fecha

def obtieneFechaVertice(pathDir):
    fecha = pathDir.split('/')[-1].split('.')[0].split('_')[4]
    fecha = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    return fecha.strftime('%Y%m%dT%H%M%S')

def descomprime(pathInput,pathOutput):
    compresion = tipoCompresion(pathInput) 
    if compresion == 'gz':
        os.system('tar -xvzf '+pathInput+' -C '+pathOutput)
    elif compresion == 'zip':
        os.system('unzip '+pathInput+' -d '+pathOutput)

def verificaL2A(tile,fecha,pathInput):
    archivo = glob(pathInput+tile+'/*'+fecha+'*'+tile+'*')
    if len(archivo) >= 1:
        return True
    else:
        return False

def copiaL2A(tile,fecha,pathInput,pathOutput):
    archivo = glob(pathInput+tile+'/*'+fecha+'*'+tile+'*')[0]
    os.system('cp '+archivo+' '+pathOutput)
    return archivo

def aperturaDS(pathBand):
    ds = gdal.Open(pathBand)
    return ds

def imgToGeoTIF(ds,tif,pathOutput):
    print("Pasando a tif: "+pathOutput+tif+'.tif')
    gdal.Translate(pathOutput+tif+'.tif',ds)

#def remuestrea(ds,tif,dim,pathOutput):
    #os.system('gdalwarp -tr '+dim+' '+dim+' '+pathOutput+ds+'.tif '+pathOutput+tif+'.tif')
#    gdal.Warp(pathOutput+tif+'.tif',ds,options=gdal.WarpOptions(xRes=dim,yRes=dim))

def creaTif(dsRef,npy,output):
    geotransform = dsRef.GetGeoTransform()
    nx = dsRef.RasterXSize
    ny = dsRef.RasterYSize
    dst_ds = gdal.GetDriverByName('GTiff').Create(output, ny, nx, 1, gdal.GDT_Float32)
    dst_ds.SetGeoTransform(geotransform)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(dsRef.GetProjectionRef())
    dst_ds.SetProjection(srs.ExportToWkt())
    dst_ds.GetRasterBand(1).WriteArray(npy)
    dst_ds.FlushCache()
    dst_ds = None

def obtieneCuadrante(ds):
    xSize = ds.RasterXSize
    ySize = ds.RasterYSize
    geo = ds.GetGeoTransform()
    xmin = geo[0]
    ymax = geo[3]
    xres = geo[1]
    yres = geo[5]
    xmax = xmin + xres*xSize
    ymin = ymax + yres*ySize

    return [xmin,ymax,xmax,ymin]

def obtieneParametrosGeoTrasform(ds):
    geo = ds.GetGeoTransform()
    nx = ds.RasterXSize
    ny = ds.RasterYSize
    xmin = geo[0]
    ymax = geo[3]
    xres = geo[1]
    yres = geo[5]
    xmax = xmin + xres*nx
    ymin = ymax + yres*ny

    return nx,ny,xmin,ymax,xres,yres,xmax,ymin

def remuestrea(pathOutput,ds,dimx,dimy):
    gdal.Translate(pathOutput,ds,options=gdal.TranslateOptions(xRes=dimx,yRes=dimy))

def RGB(r,g,b,tile,anio,fecha,fechaProc,pathOutputGeoTiff,pathOutputPeta):
    nombre = pathOutputGeoTiff+'sargazo/'+tile+'/'+'S2_MSI_SAR_'+tile+'_'+fecha+'_'+fechaProc+".tif"
    os.system('gdal_merge.py -separate -co PHOTOMETRIC=RGB -o '+nombre+' '+r+' '+g+' '+b)
    # MANDA A PETA
    os.system('scp '+nombre+' lanotadm@stratus:'+pathOutputPeta+'l2/geotiff/sargazo/'+tile+'/')

def RGB_TC(tile,anio,fecha,fechaProc,nivel,resolucion,pathInput,pathOutputGeoTiff,pathOutputPeta):
    dirTC = listaBandas(pathInput,nivel,resolucion,'TCI')
    nombre = pathOutputGeoTiff+'TC/'+tile+'/'+'S2_MSI_TC_'+tile+'_'+fecha+'_'+fechaProc+'.tif'
    os.system('gdal_translate '+dirTC+' '+nombre)
    # MANDA A PETA
    os.system('scp '+nombre+' lanotadm@stratus:'+pathOutputPeta+'l2/geotiff/TC/'+tile+'/')

def poligonizacion(tile,anio,fecha,bufferLM,pathLM,pathInput,pathOutput,pathOutputEmpty):
    time = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    fechaDia = time.strftime('%Y-%m-%d')
    os.system('gdal_polygonize.py '+pathInput+'nubesBajas_mask.tif -f "GeoJSON" '+pathInput+'alg_mask_filter_tmp.json')
    df = gpd.read_file(pathInput+'alg_mask_filter_tmp.json')
    df = df[df.DN == 1]

    if len(df)>= 1:
        print('=============================================')
        print('Deteccion de sargazo con filtro de pixel: ',len(df),' elementos')
        print('=============================================')
        df['IDpoligono'] = range(1, len(df) + 1)
        df['tile'] = tile
        df['fecha'] = fecha
        df['fechaDia'] = fechaDia
        df["area_km2"] = round(df['geometry'].area*0.000001,4)
        #gdf = gpd.read_file(pathLM+'land_UTM16N_20m_distance.geojson')
        gdf = gpd.read_file(pathLM+'land_UTM16N_20m_2021.geojson')
        distances = []
        df['distCosta_km'] = None
        for i in range(len(df)):
            distance = round(gdf['geometry'].iloc[0].distance(df['geometry'].iloc[i])*0.001,4)
            #print(distance)
            #df['distCosta'].iloc[i] = distance
            distances.append(distance)
        df['distCosta_km'] = distances
        df = df.drop(columns=['DN'])      
        df.to_file(pathInput+'alg_mask_filter_tmp_sar.json', driver="GeoJSON")
        banderaSar = True
        nombre = None
        totalSar = str(round(df['area_km2'].sum(),4))
        return nombre, banderaSar, totalSar
    else:
        print('=========================')
        print('NO DETECCIÓN DE SARGAZO')
        print('=========================')
        #os.system('mkdir -p '+pathOutputEmpty+tile+'/')
        #nombre = pathOutputEmpty+tile+'/'+'S2_MSI_SAR_'+tile+'_'+bufferLM+'_'+fecha+".txt"
        nombre = ''
        #f = open(nombre,'w')
        #f.write('No detección de sargazo')
        #f.close()
        #print('Tile:'+tile+'\nFecha:'+fecha)
        banderaSar = False
        totalSar = '0'
        return nombre, banderaSar, totalSar

def obtieneVertices(pathInput,pathOutput,pathOutputPeta):
    polys = gpd.read_file(pathInput)
    points = polys.copy()
    points = points.explode()
    points.geometry = points.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
    nombre = pathOutput+pathInput.split('/')[-1].split('.')[0]+'_vertices.json'
    points.to_file(nombre,driver='GeoJSON')
    # MANDA A PETA
    os.system('scp '+nombre+' lanotadm@stratus:'+pathOutputPeta+'l2/geojson/sargazo_vertices/')

def detfooMascaraVectorial(pathTmp):
    detfoo = 'MSK_DETFOO_B8A.json'
    df = gpd.read_file(pathTmp+'alg_mask_filter_tmp_sar.json')
    df_mask = gpd.read_file(pathTmp+detfoo)
    res_difference = gpd.overlay(df, df_mask, how='difference')
    print('=============================================')
    print('Detección de sargazo con mascara detfoo: ',len(res_difference),' elementos')
    print('=============================================')
    res_difference.to_file(pathTmp+'alg_mask_filter_tmp_sar_detfoo.json', driver="GeoJSON")

def mascarasVectoriales(tile,anio,fecha,fechaProc,bufferLM,pathLM,pathTmp,pathOutput,pathOutputEmpty,pathOutputPeta):
    # CON DETFOO
    #df = gpd.read_file(pathTmp+'alg_mask_filter_tmp_sar_detfoo.json')
    # SIN DETFOO
    df = gpd.read_file(pathTmp+'alg_mask_filter_tmp_sar.json')
    df_mask = gpd.read_file(pathLM+'land_UTM16N_20m_2021.geojson')
    res_difference = gpd.overlay(df, df_mask, how='difference')
    print('=============================================')
    print('Detección de sargazo con mascara de tierra: ',len(res_difference),' elementos')
    print('=============================================')
    df_maskCloudShadow = gpd.read_file(pathTmp+'cloudMaskShadow_b250_bin_rec_tmp.json')
    res_difference = gpd.overlay(res_difference, df_maskCloudShadow, how='difference')
    print('=============================================')
    print('Detección de sargazo con mascara de nubes/sombra: ',len(res_difference),' elementos')
    print('=============================================')
    #df_detfooMask = gpd.read_file(pathTmp+'MSK_DETFOO_B8A.json')
    #res_difference = gpd.overlay(res_difference, df_detfooMask, how='difference')
    #print('=============================================')
    #print('Detección de sargazo con mascara detfoo y entropia: ',len(res_difference),' elementos')
    #print('=============================================')
    #df_maskCloud = gpd.read_file(pathTmp+'cloudMask_b250_bin_rec_mask_tmp.json')
    #res_difference = gpd.overlay(res_difference, df_maskCloud, how='difference')
    #print('=============================================')
    #print('Detección de sargazo con mascara de nubes: ',len(res_difference),' elementos')
    #print('=============================================')
    os.system('mkdir -p '+pathOutput+tile+'/')
    nombre = pathOutput+tile+'/'+'S2_MSI_SAR_'+tile+'_'+fecha+'_'+fechaProc+".json"
    res_difference["geometry"] = [MultiPolygon([feature]) if type(feature) == Polygon \
    else feature for feature in res_difference["geometry"]]
    if len(res_difference)>= 1:
        banderaSar = True
        # Km2
        totalSar = str(round(res_difference['area_km2'].sum(),4))
        # ARCHIVO FINAL

        # MANDA A DATA
        res_difference.to_file(nombre, driver="GeoJSON")
        # MANDA A PETA
        os.system('scp '+nombre+' lanotadm@stratus:'+pathOutputPeta+'l2/geojson/sargazo/'+tile+'/')
    else:
        print('=========================')
        print('NO DETECCIÓN DE SARGAZO')
        print('=========================')
        #os.system('mkdir -p '+pathOutputEmpty+tile+'/')
        #nombre = pathOutputEmpty+tile+'/'+'S2_MSI_SAR_'+tile+'_'+bufferLM+'_'+fecha+".txt"
        #f = open(nombre,'w')
        #print('=========================')
        #print('NO DETECCIÓN DE SARGAZO')
        #print('=========================')
        #f.close()
        #print('Tile:'+tile+'\nFecha:'+fecha)
        banderaSar = False
        totalSar = '0'    
    return banderaSar, totalSar, nombre

def tierraMascara(cuadrante,pathMask,pathTmp):
    #gdal.Translate(pathTmp+'tmp_mask.tif',dsMascara,options=gdal.TranslateOptions(projWin=cuadrante))
    cuadrante = str(cuadrante[0])+' '+str(cuadrante[1])+' '+str(cuadrante[2])+' '+str(cuadrante[3])
    os.system('gdal_translate -projwin '+cuadrante+' '+pathMask+' '+pathTmp+'landMask_tmp.tif')

def aguaMascara(cuadrante,pathSCL,pathTmp):
    # Esta parte e spara ver si funciona mejor con solo agua
    #os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'aguaMask.tif --calc="0*(A!=2)+0*(A!=3)+0*(A!=10)+1*(A==2)+1*(A==3)+1*(A==10)"')
    os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'aguaMask.tif --calc="0*(A!=2)+1*(A==2)"')

def nubesMascara(cuadrante,bufferNubes,pathSCL,pathTmp):
    cuadrante = str(cuadrante[0])+' '+str(cuadrante[1])+' '+str(cuadrante[2])+' '+str(cuadrante[3])

    # Esta parte es para eficientizar la poligonizacion de las nubes
    #os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'cirrusMask.tif --calc="0*(A!=8)"')
    os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'cirrusMask.tif --calc="0*(A!=7)+0*(A!=8)+0*(A!=9)+0*(A!=10)+1*(A==7)+1*(A==8)+1*(A==9)+1*(A==10)"')

    os.system('gdal_polygonize.py '+pathTmp+'cirrusMask.tif -f "GeoJSON" '+pathTmp+'SCL_tmp.json')
    df = gpd.read_file(pathTmp+'SCL_tmp.json')
    df = df[df['DN'] == 1]
    if len(df) == 0:
        print("No buffer de nubes")
        banderaNub = False
        return banderaNub
    else:
        print("Buffer de nubes")
        banderaNub = True
        df = df.buffer(bufferNubes)
        df_g = df.unary_union
        df = gpd.GeoDataFrame(crs=df.crs, geometry=[df_g])
        df.to_file(pathTmp+"cloudMask_b250_tmp.geojson", driver='GeoJSON')
        os.system('gdal_rasterize -burn 8 -tr 20 20 -l cloudMask_b250_tmp '+pathTmp+'cloudMask_b250_tmp.geojson '+pathTmp+'cloudMask_b250_tmp.tif')
        os.system('gdal_calc.py -A '+pathTmp+'cloudMask_b250_tmp.tif --outfile='+pathTmp+'cloudMask_b250_bin_tmp.tif --calc="0*(A==8)+1*(A==0)"')
        os.system('gdal_translate -projwin '+cuadrante+' '+pathTmp+'cloudMask_b250_bin_tmp.tif '+pathTmp+'cloudMask_b250_bin_rec_tmp.tif')

        os.system('gdal_polygonize.py '+pathTmp+'cloudMask_b250_bin_rec_tmp.tif -f "GeoJSON" '+pathTmp+'cloudMask_b250_bin_rec_tmp.json')
        df = gpd.read_file(pathTmp+'cloudMask_b250_bin_rec_tmp.json')
        df = df[df['DN'] == 0]
        df.to_file(pathTmp+"cloudMask_b250_bin_rec_mask_tmp.json", driver='GeoJSON')

        return banderaNub

def nubesSombraMascara(cuadrante,bufferNubes,porcNube,pathTmp):

    cuadrante = str(cuadrante[0])+' '+str(cuadrante[1])+' '+str(cuadrante[2])+' '+str(cuadrante[3])

    b12 = aperturaDS(pathTmp+'B12.tif').ReadAsArray()
    #b11 = aperturaDS(pathTmp+'B11.tif').ReadAsArray()
    ref = aperturaDS(pathTmp+'B12.tif')

    #nubesMask = np.where((b12 > 1220) & (b11 > 395), 0, 1)
    nubesMask = np.where(b12 > 1220, 0, 1)

    creaTif(ref,nubesMask,pathTmp+'cloudMaskShadow_bin_tmp.tif')

    os.system('gdal_polygonize.py '+pathTmp+'cloudMaskShadow_bin_tmp.tif -f "GeoJSON" '+pathTmp+'cloudMaskShadow_bin_tmp.json')
    df = gpd.read_file(pathTmp+'cloudMaskShadow_bin_tmp.json')
    df = df[df['DN'] == 0]
    if len(df) == 0:
        print("No buffer de nubes")
        banderaNub = False
        return banderaNub
    elif porcNube >= 60.0:
        banderaNub = True
        df.to_file(pathTmp+"cloudMaskShadow_b250_bin_rec_tmp.json", driver='GeoJSON')
    else:
        print("Buffer de nubes")
        banderaNub = True
        df = df.buffer(bufferNubes)
        print("Disolviendo Buffer")
        df_g = df.unary_union
        df = gpd.GeoDataFrame(crs=df.crs, geometry=[df_g])
        #df.to_file(pathTmp+"cloudMaskShadow_b250_tmp.json", driver='GeoJSON')
        df.to_file(pathTmp+"cloudMaskShadow_b250_bin_rec_tmp.json", driver='GeoJSON')
        # ESTO NO PORQUE YA ESTA POLIGONIZADO
        #print("Rasterizando Buffer")
        #os.system('gdal_rasterize -burn 1 -tr 20 20 -l cloudMaskShadow_b250_tmp '+pathTmp+'cloudMaskShadow_b250_tmp.json '+pathTmp+'cloudMaskShadow_b250_tmp.tif')
        #print("Filtrando Buffer")
        #os.system('gdal_calc.py -A '+pathTmp+'cloudMaskShadow_b250_tmp.tif --outfile='+pathTmp+'cloudMaskShadow_b250_bin_tmp.tif --calc="0*(A==1)+1*(A==0)"')
        #os.system('gdal_translate -projwin '+cuadrante+' '+pathTmp+'cloudMaskShadow_b250_bin_tmp.tif '+pathTmp+'cloudMaskShadow_b250_bin_rec_tmp.tif')
        #print("Poligonizando Buffer Filtrado")
        #os.system('gdal_polygonize.py '+pathTmp+'cloudMaskShadow_b250_bin_tmp.tif -f "GeoJSON" '+pathTmp+'cloudMaskShadow_b250_bin_tmp.json ')
        #df = gpd.read_file(pathTmp+'cloudMaskShadow_b250_bin_tmp.json')
        #df = df[df['DN'] == 0]
        #df.to_file(pathTmp+"cloudMaskShadow_b250_bin_rec_tmp.json", driver='GeoJSON')

        return banderaNub

def detfooMascara(detfoo_dist,pathInput,pathOutput):
    #ogr2ogr -f "GeoJSON" MSK_DETFOO_B04.geojson MSK_DETFOO_B04.gml
    detfoo = 'MSK_DETFOO_B8A.gml'
    archivoQuality = nomDirQuality(pathInput,detfoo)
    gdf = gpd.read_file(archivoQuality)

    gdf = gdf.sort_values(by=['gml_id'])
    gdf_crs = gdf.crs
    #ext = gdf.iloc[0].geometry.bounds

    detfoot_buffers = []

    for i in range(len(gdf)):
        if i == 0:        
            detfoot = gdf.iloc[i].geometry
            ext = detfoot.bounds
            detfoot_buff = LineString([Point(ext[2],ext[3]),Point(ext[0],ext[1])]).buffer(detfoo_dist)
            detfoot_buffers.append(detfoot_buff)
        elif i == len(gdf)-1:        
            detfoot = gdf.iloc[i].geometry
            ext = detfoot.bounds
            detfoot_buff = LineString([Point(ext[2],ext[3]),Point(ext[0],ext[1])]).buffer(detfoo_dist)
            detfoot_buffers.append(detfoot_buff)
        elif i != len(gdf)-2:
            detfoot = gdf.iloc[i].geometry
            ext = detfoot.bounds
            detfootSig = gdf.iloc[i+1].geometry
            extSig = detfootSig.bounds
            detfoot_buff = LineString([Point(ext[2],ext[3]),Point(extSig[0],extSig[1])]).buffer(detfoo_dist)
            detfoot_buffers.append(detfoot_buff)

    df_detfoot_buffers = pd.DataFrame(detfoot_buffers)
    df_detfoot_buffers = df_detfoot_buffers.drop([0], axis=1)
    gdf_detfoot_buffers = gpd.GeoDataFrame(df_detfoot_buffers, geometry=detfoot_buffers, crs=gdf_crs)
    gdf_detfoot_buffers.to_file(pathOutput+detfoo.split('.')[0]+'.json',driver='GeoJSON')

def sargazoBin(banderaNub,nivel,pathInput,pathOutput):
    #Prueba BR
    #os.system('gdal_calc.py -A '+pathInput+'B02.tif -B '+pathInput+'B03.tif --type=Float64 --outfile='+pathOutput+'BR.tif --calc="B.astype(numpy.float64)/A.astype(numpy.float64)"')
    #os.system('gdal_calc.py -A '+pathInput+'BR.tif --outfile='+pathOutput+'alg_tmp.tif --calc="logical_and(A>0.45,A<0.57)"')
    os.system('gdal_calc.py -A '+pathInput+'B8A.tif -B '+pathInput+'B04.tif -C '+pathInput+'B11.tif --outfile='+pathOutput+'alg_tmp_val.tif --calc="logical_and(A>700,B<1000,C<500)"')
    os.system('gdal_calc.py -A '+pathInput+'B8A.tif -B '+pathInput+'B04.tif --outfile='+pathOutput+'alg_tmp_band_8A.tif --calc="1*(B<A)+0*(B>A)"')
    os.system('gdal_calc.py -A '+pathInput+'B08_20.tif -B '+pathInput+'B04.tif --outfile='+pathOutput+'alg_tmp_band_8.tif --calc="1*(B<A)+0*(B>A)"')
    os.system('gdal_calc.py -A '+pathInput+'alg_tmp_val.tif -B '+pathInput+'alg_tmp_band_8A.tif -C '+pathInput+'alg_tmp_band_8.tif --outfile='+pathOutput+'alg_tmp.tif --calc="A*B*C"')

    if nivel == 'L1C' or banderaNub == False:
        #Esto es para probar lo del corte
	#os.system('gdal_calc.py -A '+pathOutput+'alg_tmp.tif -B '+pathInput+'landMask_tmp.tif --outfile='+pathOutput+'alg_mask_tmp.tif --calc="A*B"')
        os.system('gdal_calc.py -A '+pathOutput+'alg_tmp.tif -B '+pathInput+'aguaMask.tif --outfile='+pathOutput+'alg_mask_tmp.tif --calc="A*B"')
    elif nivel == 'L2A' and banderaNub == True:
	#Esto es para probar lo del corte 
        #os.system('gdal_calc.py -A '+pathOutput+'alg_tmp.tif -B '+pathInput+'landMask_tmp.tif -C '+pathInput+'cloudMask_b250_bin_rec_tmp.tif --outfile='+pathOutput+'alg_mask_tmp.tif --calc="A*B*C"')
        os.system('gdal_calc.py -A '+pathOutput+'alg_tmp.tif -B '+pathInput+'aguaMask.tif -C '+pathInput+'cloudMask_b250_bin_rec_tmp.tif --outfile='+pathOutput+'alg_mask_tmp.tif --calc="A*B*C"')
    #os.system('gdal_calc.py -A '+pathOutput+tile+'_'+fecha+'_result_bin.tif -B '+pathInput+'maskNubes_b250_bin_tmp.tif --outfile='+pathOutput+tile+'_'+fecha+'_result_binFinal.tif --calc="A*B"')

def sargazoBinNumpy(pathInput):
    b11 = aperturaDS(pathInput+'B11.tif').ReadAsArray()
    b8A = aperturaDS(pathInput+'B8A.tif').ReadAsArray()
    b08 = aperturaDS(pathInput+'B08_20.tif').ReadAsArray()
    b04 = aperturaDS(pathInput+'B04.tif').ReadAsArray()

    ref = aperturaDS(pathInput+'B04.tif')

    sargazoBin = np.where((b8A > 700) & (b04 < 1000) & (b11 < 500) & (b04 < b8A) & (b04 < b08), 1, 0)

    creaTif(ref,sargazoBin,pathInput+'alg_tmp_numpy.tif')
    #os.system('gdal_calc.py -A '+pathInput+'alg_tmp_numpy.tif -B '+pathInput+'aguaMask.tif --outfile='+pathInput+'alg_mask_tmp_numpy.tif --calc="A*B"')
    #os.system('gdal_calc.py -A '+pathInput+'alg_tmp_numpy.tif -B '+pathInput+'landMask_tmp.tif --outfile='+pathInput+'alg_mask_tmp_numpy.tif --calc="A*B"')
    # MASCARA DE NUBES SLC
    #os.system('gdal_calc.py -A '+pathInput+'alg_tmp_numpy.tif -B '+pathInput+'cloudMask_b250_bin_rec_tmp.tif --outfile='+pathInput+'alg_mask_tmp_numpy.tif --calc="A*B"')
    # MASCARA DE NUBES Y SOMBRA B12
    #os.system('gdal_calc.py -A '+pathInput+'alg_tmp_numpy.tif -B '+pathInput+'cloudMaskShadow_b250_bin_rec_tmp.tif --outfile='+pathInput+'alg_mask_tmp_numpy.tif --calc="A*B"')

def entropiaNumpy(pathInput):
    ds = gdal.Open(pathInput+'B12.tif')
    b12 = ds.ReadAsArray()
    entropia = entropy(b12, disk(5))
    creaTif(ds,entropia,pathInput+'b12_entropia.tif')
    return entropia

""" def pixelNubesBajas(dsRef,dsSar,nubesBajas,entropia,entropiaMin):
	nuMask = dsRef.ReadAsArray()
	b4 = dsRef.ReadAsArray()
	sar = dsSar.ReadAsArray()

	cont = 0
	listaBanderas = []


    # Entropia
    #entropiaMin = 6.2

	# Valor de referencia B4 Sugerido 900
	nubeBaja = nubesBajas

	for i in range(nuMask.shape[0]-1):
		for j in range(nuMask.shape[1]-1):
			#print(nuMask.shape[0],nuMask.shape[1])
			#print('pocision:',i,j)
			#print('valor:',sar[i,j])
			if sar[i,j] == 1:
				# ESQUINAS
				if (i == 0 and j == 0) and ((b4[i,j+1] > nubeBaja or b4[i+1,j+1] > nubeBaja or b4[i+1,j] > nubeBaja) or (entropia[i,j+1] > entropiaMin or entropia[i+1,j+1] > entropiaMin or entropia[i+1,j] > entropiaMin)):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso1')

				elif (i == 0 and j == nuMask.shape[1]) and ((b4[i,j-1] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i+1,j] > nubeBaja) or (entropia[i,j-1] > entropiaMin or entropia[i+1,j-1] > entropiaMin or entropia[i+1,j] > entropiaMin)):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso2')

				elif (i == nuMask.shape[0] and j == 0) and ((b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j+1] > nubeBaja) or (entropia[i-1,j] > entropiaMin or entropia[i-1,j+1] > entropiaMin or entropia[i,j+1] > entropiaMin)):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso3')

				elif (i == nuMask.shape[0] and j == nuMask.shape[1]) and ((b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i,j-1] > nubeBaja) or (entropia[i-1,j-1] > entropiaMin or entropia[i-1,j] > entropiaMin or entropia[i,j-1] > entropiaMin)):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso4')
				#BORDES
				elif (i == 0) and (b4[i,j-1] > nubeBaja or b4[i,j+1] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i+1,j] > nubeBaja or b4[i+1,j+1] > nubeBaja) or (entropia[i,j-1] > entropiaMin or entropia[i,j+1] > entropiaMin or entropia[i+1,j-1] > entropiaMin or entropia[i+1,j] > entropiaMin or entropia[i+1,j+1] > entropiaMin):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso5')

				elif (i == nuMask.shape[0]) and (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j-1] > nubeBaja or b4[i,j+1] > nubeBaja) or (entropia[i-1,j-1] > entropiaMin or entropia[i-1,j] > entropiaMin or entropia[i-1,j+1] > entropiaMin or entropia[i,j-1] > entropiaMin or entropia[i,j+1] > entropiaMin):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso6')

				elif (j == 0) and (b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j+1] > nubeBaja or b4[i+1,j] > nubeBaja or b4[i+1,j+1] > nubeBaja) or (entropia[i-1,j] > entropiaMin or entropia[i-1,j+1] > entropiaMin or entropia[i,j+1] > entropiaMin or entropia[i+1,j] > entropiaMin or entropia[i+1,j+1] > entropiaMin):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso7')

				elif (j == nuMask.shape[1]) and (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i,j-1] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i+1,j] > nubeBaja) or (entropia[i-1,j-1] > entropiaMin or entropia[i-1,j] > entropiaMin or entropia[i,j-1] > entropiaMin or entropia[i+1,j-1] > entropiaMin or entropia[i+1,j] > entropiaMin):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso8')
				#GENERAL
				elif (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j+1] > nubeBaja or b4[i+1,j+1] > nubeBaja or b4[i+1,j] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i,j-1] > nubeBaja or (entropia[i-1,j-1] > entropiaMin or entropia[i-1,j] > entropiaMin or entropia[i-1,j+1] > entropiaMin or entropia[i,j+1] > entropiaMin or entropia[i+1,j+1] > entropiaMin or entropia[i+1,j] > entropiaMin or entropia[i+1,j-1] > entropiaMin or entropia[i,j-1] > entropiaMin)):
					nuMask[i,j] = 0
					# RECORRE
					#nuMask[i-1,j-1] = 3
					#nuMask[i-1,j] = 3
					#nuMask[i-1,j+1] = 3
					#nuMask[i,j+1] = 3
					#nuMask[i+1,j+1] = 3
					#nuMask[i+1,j] = 3
					#nuMask[i+1,j-1] = 3
					#nuMask[i,j-1] = 3
					cont = cont + 1
					listaBanderas.append('Caso10')
                # ENTROPIA
                        elif (entropia[i,j] >= 6.0):
                            nuMask[i,j] = 0

                            cont = cont + 1
                            listaBanderas.append('Caso11')
				# SARGAZO
			else:
				nuMask[i,j] = 1
		else:
			nuMask[i,j] = 0

	#print(cont)
	#print(bandera)
	print(set(listaBanderas))
	#np.save("nuMask.npy",nuMask)

	return nuMask """

def filtroPixel(dsRef,dsSar,nubeBaja,entropia,dsSCL,pathTmp):

    # Nube baja con B12
    nuMask = dsRef.ReadAsArray()
    b12 = dsRef.ReadAsArray()
    sar = dsSar.ReadAsArray()
    scl = dsSCL.ReadAsArray()
    df_detfoo = gpd.read_file(pathTmp+'MSK_DETFOO_B8A.json')
    nx,ny,xmin,ymax,xres,yres,xmax,ymin = obtieneParametrosGeoTrasform(dsRef)

    print('=============================================')
    print('Detección de sargazo algoritmo: ',len(sar[sar == 1]),' elementos')
    print('=============================================')

    contB12 = 0
    contEnt = 0
    contSCL = 0
    listaBanderas = []

    #Entropia
    entropiaMin = 5.0
    #entropiaMin = 1000

    for i in range(nuMask.shape[0]):
        for j in range(nuMask.shape[1]):
            if sar[i,j] == 1:
                #ENTROPIA CON DETFOO                
                y = (i*yres + ymax) + yres/2
                x = (j*xres + xmin) + xres/2
                sargazoPunto = Point(x,y)
                for k in range(len(df_detfoo)):
                    if df_detfoo.iloc[k].geometry.contains(sargazoPunto) == True and entropia[i,j] >= entropiaMin:
                        nuMask[i,j] = 0
                        listaBanderas.append('Entropia y Detfoo')
                        contEnt += 1 
                        continue
                # NUBE BAJA B12
                if b12[i,j] >= nubeBaja:
                    nuMask[i,j] = 0
                    listaBanderas.append('Nube baja')
                    contB12 += 1 
#                elif entropia[i,j] >= entropiaMin:
#                    nuMask[i,j] = 0
#                    listaBanderas.append('Entropia')
#                    contEnt += 1   
                # SCL
                elif (scl[i,j] == 3) or (scl[i,j] == 8) or (scl[i,j] == 9) or (scl[i,j] == 10) or (scl[i,j] == 11):
                    nuMask[i,j] = 0
                    listaBanderas.append('SCL')
                    contSCL += 1  
                else:
                    nuMask[i,j] = 1
            else:
                nuMask[i,j] = 0

    print(set(listaBanderas))
    print('Filtrados Nube Baja: ',contB12)
    print('Filtrados Entropia y Detfoo: ',contEnt)
    print('Filtrados SCL: ',contSCL)
    #print('=============================================')
    #print('Detección de sargazo algoritmo con filtro de pixel: ',len(nuMask[nuMask == 1]),' elementos')
    #print('=============================================')

    return nuMask

""" def pixelNubesBajasN(dsRef,dsSar,nubesBajas,entropia,entropiaMin):
	nuMask = dsRef.ReadAsArray()
	b4 = dsRef.ReadAsArray()
	sar = dsSar.ReadAsArray()

	cont = 0
	listaBanderas = []

    # Entropia
    #entropiaMin = 6.2

	# Valor de referencia B4 Sugerido 900
	nubeBaja = nubesBajas

	for i in range(nuMask.shape[0]-1):
		for j in range(nuMask.shape[1]-1):
			#print(nuMask.shape[0],nuMask.shape[1])
			#print('pocision:',i,j)
			#print('valor:',sar[i,j])
			if sar[i,j] == 1 and entropia[i,j] >= 6.0:
                    nuMask[i,j] = 0
				#GENERAL
				if (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j+1] > nubeBaja or b4[i+1,j+1] > nubeBaja or b4[i+1,j] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i,j-1] > nubeBaja):
					nuMask[i,j] = 0
					# RECORRE
					#nuMask[i-1,j-1] = 3
					#nuMask[i-1,j] = 3
					#nuMask[i-1,j+1] = 3
					#nuMask[i,j+1] = 3
					#nuMask[i+1,j+1] = 3
					#nuMask[i+1,j] = 3
					#nuMask[i+1,j-1] = 3
					#nuMask[i,j-1] = 3
					listaBanderas.append('Caso1')
                if (entropia[i-1,j-1] > entropiaMin or entropia[i-1,j] > entropiaMin or entropia[i-1,j+1] > entropiaMin or entropia[i,j+1] > entropiaMin or entropia[i+1,j+1] > entropiaMin or entropia[i+1,j] > entropiaMin or entropia[i+1,j-1] > entropiaMin or entropia[i,j-1] > entropiaMin):
                    nuMask[i,j] = 0
					listaBanderas.append('Caso2') 
                # ENTROPIA
                if (entropia[i,j] >= 6.0):
                    nuMask[i,j] = 0
                    cont = cont + 1
                    listaBanderas.append('Caso3')

				# SARGAZO
			else:
				nuMask[i,j] = 1

	#print(cont)
	#print(bandera)
	print(set(listaBanderas))
	#np.save("nuMask.npy",nuMask)

	return nuMask """

def creaCSV(pathInput,pathOutput):
    gdf = gpd.read_file(pathInput)
    gdf.area_km2 = round(gdf.area_km2,4)
    crs = gdf.crs.srs.split(':')[-1]
    archivoCSV = pathOutput+pathInput.split('/')[-1].split('.')[0]+'.csv'
    gdf.to_csv(archivoCSV,index=False)

    return archivoCSV,crs

def conexionDB():
    conect = psycopg2.connect(
            host = "132.247.103.145",
            database = "sargazo",
            user = "sargazo",
            password = "iTh1Mou*",
            port = 5433
            )
    cur = conect.cursor()
    return conect,cur

def insertSargazoDB(conect,cur,crs,pathInput):
    print('Añadiendo a DB')
    with open(pathInput, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
			#print('Añadiendo a DB: ', row)
            cur.execute("INSERT INTO sargazo VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, ST_Transform(ST_GeomFromText(%s,"+crs+"),4326))", row)
        cur.execute("SELECT * from sargazo")
    row = cur.fetchall()
    conect.commit()

def deleteSargazoDB(conect,cur,tile,fecha):
    print('Borrando sargazo de DB: ')
    cur.execute("DELETE FROM sargazo WHERE tile="+tile+" AND fechadia="+fecha)
    conect.commit()

def deleteSargazoLogDB(conect,cur,tile,fecha):
    print('Borrando sargazo_log de DB: ')
    cur.execute("DELETE FROM sargazo_log WHERE tile="+tile+" AND fechadia="+fecha)
    conect.commit()

def insertSargazoLogDB(conect,cur,pathl2a,pathsargazo,fecha,tile,sargazo,totalsar,porcNube,tproc):
    time = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    fechaDia = time.strftime('%Y-%m-%d')
    fechaproc = obtieneFechaProc()
    print('Añadiendo log a DB: ')
    cur.execute("INSERT INTO sargazo_log VALUES (DEFAULT, '"+pathl2a+"', '"+pathsargazo+"', '"+fecha+"', '"+fechaproc+"', '"+fechaDia+"', '"+tile+"','"+sargazo+"','"+totalsar+"','"+porcNube+"','"+tproc+"')")
    cur.execute("SELECT * from sargazo_log")
    row = cur.fetchall()
    conect.commit()

def insertSargazoLogErrorDB(conect,cur,pathl1c,pathl2a,fecha,tile,tiperror):
    time = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    fechaDia = time.strftime('%Y-%m-%d')
    fechaproc = obtieneFechaProc()
    print('Añadiendo log a DB: ')
    cur.execute("INSERT INTO sargazo_logerror VALUES (DEFAULT, '"+pathl1c+"', '"+pathl2a+"', '"+fecha+"', '"+fechaproc+"', '"+fechaDia+"', '"+tile+"', '"+tiperror+"')")
    cur.execute("SELECT * from sargazo_logerror")
    row = cur.fetchall()
    conect.commit()


def agregaSargazoDB(crs,pathl2a,pathsargazo,fecha,tile,sargazo,totalsar,porcNube,tproc,pathInput):
    conect,cur = conexionDB()
    try:
        insertSargazoDB(conect,cur,crs,pathInput)
        insertSargazoLogDB(conect,cur,pathl2a,pathsargazo,fecha,tile,sargazo,totalsar,porcNube,tproc)
        print ("Se agrego a la DB archivo: "+pathInput)
    except Exception as e:
        print(f'Ocurrio un error en la transacción DB: {e}')
        # Mandar correo
        enviaMail(fecha, tile, traceback.format_exc().replace("'",""))
        cur.close()
        conect.close()
    conect.close()

def borraSargazoDB(fecha,tile):
    conect,cur = conexionDB()
    try:
        deleteSargazoLogDB(conect, cur, tile, fecha)
        deleteSargazoDB(conect, cur, tile, fecha)
        print ("Se elimino sargazo de la DB: "+tile+" "+tile)
    except Exception as e:
        print(f'Ocurrio un error en la transacción DB: {e}')
        # Mandar correo
        enviaMail(fecha, tile, traceback.format_exc().replace("'",""))
        cur.close()
        conect.close()
    conect.close()

def agregaNoSargazoDB(pathl2a,pathsargazo,fecha,tile,sargazo,totalsar,porcNube,tproc):
    conect,cur = conexionDB()
    try:        
        insertSargazoLogDB(conect,cur,pathl2a,pathsargazo,fecha,tile,sargazo,totalsar,porcNube,tproc)
        #print ("Se agrego a la DB archivo: "+pathInput)
    except Exception as e:
        print(f'Ocurrio un error en la transacción DB: {e}')
        # Mandar correo
        enviaMail(fecha, tile, traceback.format_exc().replace("'",""))
        cur.close()
        conect.close()
    conect.close()

def agregaErrorSargazoDB(pathl1c,pathl2a,fecha,tile,tiperror):
    conect,cur = conexionDB()
    try:        
        insertSargazoLogErrorDB(conect,cur,pathl1c,pathl2a,fecha,tile,tiperror)
        #print ("Se agrego a la DB archivo: "+pathInput)
    except Exception as e:
        print(f'Ocurrio un error en la transacción DB: {e}')
        # Mandar correo
        enviaMail(fecha, tile,traceback.format_exc().replace("'",""))
        cur.close()
        conect.close()
    conect.close()

def verificaSargazoDB(tile,fecha):	
    conect,cur = conexionDB()
    try:
        cur.execute("SELECT * FROM sargazo_log where tile = '"+tile+"' AND fecha = '"+fecha+"'")
        row = cur.fetchall()
        #print(len(row))
        conect.commit()
    except Exception as e:
        print(f'Ocurrio un error en la transacción DB log: {e}')
        # Mandar correo
        enviaMail(fecha, tile, traceback.format_exc().replace("'",""))
        cur.close()
        conect.close()
    conect.close()
    
    return len(row)

def enviaMail(fecha,tile,error):
    mail_content = '''El proceso de deteccion de sargazo con sentinel-2 tuvo un error de ejecución:
    \nFecha: '''+fecha+'''
    \nTile: '''+tile+'''
    \nError: '''+error

    #The mail addresses and password
    sender_address = 'alertaslanot@gmail.com'
    sender_pass = 'aet9iMei'
    receiver_address = 'urielmendozacastillo@gmail.com'
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = 'Sargazo: Error en el procesamiento.'   #The subject line
    #The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))
    #Create SMTP session for sending the mail
    port = 465
    context = ssl.create_default_context()
    session = smtplib.SMTP_SSL('smtp.gmail.com', port, context=context) #use gmail with port
    #session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    print('Mail de error enviado...')

def createMosaic(fecha,compuesto,pathInput,pathOutputPeta,pathOutputWeb):
    tiles = ['T16QDF','T16QDG','T16QDH','T16QDJ','T16QEF','T16QEG','T16QEH','T16QEJ']
    archivosTiff = []
    for tile in tiles:
        #print('AQUI '+pathInput+'/'+compuesto+'/'+tile+'/*'+fecha+'*')
        try:
            archivoTiff = glob(pathInput+'/'+compuesto+'/'+tile+'/*'+fecha+'*')[0]
            archivosTiff.append(archivoTiff)
        except IndexError:
            continue        
    archivosTiffString = " ".join(archivosTiff)
    os.system('gdal_merge.py -o '+pathInput+'/'+compuesto+'/mosaicos/latest_'+compuesto+'.tif -of gtiff '+archivosTiffString)

    # MANDA A PETA
    os.system('scp '+pathInput+'/'+compuesto+'/mosaicos/latest_'+compuesto+'.tif'+' lanotadm@stratus:'+pathOutputPeta+'l2/geotiff/'+compuesto+'/mosaicos/')
    # MANDA A WEB
    os.system('scp '+pathInput+'/'+compuesto+'/mosaicos/latest_'+compuesto+'.tif'+' sargazo@cumulus:'+pathOutputWeb+'l2/geotiff/'+compuesto+'/mosaicos/')