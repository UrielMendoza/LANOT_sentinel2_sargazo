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

def sen2core(pathSen2Core,pathCFG,pathInput,pathOutput,resolution):
    os.system(pathSen2Core+'L2A_Process --resolution '+resolution+' --GIP_L2A '+pathCFG+' --output_dir '+pathOutput+' '+pathInput)

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

def descomprime(pathInput,compresion,pathOutput):
    if compresion == 'gz':
        os.system('tar -xvzf '+pathInput+' -C '+pathOutput)
    elif compresion == 'zip':
        os.system('unzip '+pathInput+' -d '+pathOutput)

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

def remuestrea(pathOutput,ds,dimx,dimy):
    gdal.Translate(pathOutput,ds,options=gdal.TranslateOptions(xRes=dimx,yRes=dimy))

def RGB(r,g,b,tile,anio,fecha,fechaProc,pathOutputGeoTiff):
    os.system('gdal_merge.py -separate -co PHOTOMETRIC=RGB -o '+pathOutputGeoTiff+'sargazo/'+tile+'/'+anio+'/'+'S2_MSI_SAR_'+tile+'_'+fecha+'_'+fechaProc+".tif"+' '+r+' '+g+' '+b)

def RGB_TC(tile,anio,fecha,fechaProc,nivel,resolucion,pathInput,pathOutputGeoTiff):
    dirTC = listaBandas(pathInput,nivel,resolucion,'TCI')
    os.system('gdal_translate '+dirTC+' '+pathOutputGeoTiff+'TC/'+tile+'/'+anio+'/'+'S2_MSI_TC_'+tile+'_'+fecha+'_'+fechaProc+'.tif')

def poligonizacion(tile,anio,fecha,bufferLM,pathInput,pathOutput,pathOutputEmpty):
    time = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    os.system('gdal_polygonize.py '+pathInput+'nubesBajas_mask.tif -f "GeoJSON" '+pathInput+'alg_mask_filter_tmp.json')
    df = gpd.read_file(pathInput+'alg_mask_filter_tmp.json')
    df = df[df.DN == 1]

    if len(df)>= 1:
        print('Deteccion de sargazo sin mascara de tierra: ',len(df),' elementos')
        df["area"] = df['geometry'].area
        df['fecha'] = fecha
        df['tile'] = tile
        df['IDpolygon'] = range(1, len(df) + 1)
        df.to_file(pathInput+'alg_mask_filter_tmp_sar.json', driver="GeoJSON")
        banderaSar = True
        nombre = None
        totalSar = str(df['area'].sum())
        return nombre, banderaSar, totalSar
    else:
        print('No deteccion de sargazo')
        os.system('mkdir -p '+pathOutputEmpty+tile+'/'+anio)
        nombre = pathOutputEmpty+tile+'/'+anio+'/'+'S2_MSI_SAR_'+tile+'_'+bufferLM+'_'+fecha+".txt"
        f = open(nombre,'w')
        f.write('No detección de sargazo')
        f.close()
        #print('Tile:'+tile+'\nFecha:'+fecha)
        banderaSar = False
        totalSar = '0'
        return nombre, banderaSar, totalSar

def obtieneVertices(pathInput,pathOutput):
    polys = gpd.read_file(pathInput)
    points = polys.copy()
    points = points.explode()
    points.geometry = points.geometry.apply(lambda x: MultiPoint(list(x.exterior.coords)))
    points.to_file(pathOutput.split('.')[0]+'_vertices.json',driver='GeoJSON')

def detfooMascaraVectorial(pathTmp):
    detfoo = 'MSK_DETFOO_B8A.json'
    df = gpd.read_file(pathTmp+'alg_mask_filter_tmp_sar.json')
    df_mask = gpd.read_file(pathTmp+detfoo)
    res_difference = gpd.overlay(df, df_mask, how='difference')
    print('Deteccion de sargazo con mascara detfoo: ',len(res_difference),' elementos')
    res_difference.to_file('alg_mask_filter_tmp_sar_detfoo.json', driver="GeoJSON")

def tierraMascaraVectorial(tile,anio,fecha,fechaProc,bufferLM,pathLM,pathTmp,pathOutput):
    df = gpd.read_file(pathTmp+'alg_mask_filter_tmp_sar_detfoo.json')
    df_mask = gpd.read_file(pathLM+'land_UTM16N_20m'+bufferLM+'.geojson')
    res_difference = gpd.overlay(df, df_mask, how='difference')
    print('Deteccion de sargazo con mascara de tierra: ',len(res_difference),' elementos')
    os.system('mkdir -p '+pathOutput+tile+'/'+anio)
    nombre = pathOutput+tile+'/'+anio+'/'+'S2_MSI_SAR_'+tile+'_'+bufferLM+fecha+'_'+fechaProc+".json"
    #res_difference["geometry"] = [Polygon([feature]) if type(feature) == Polygon \
    #else feature for feature in res_difference["geometry"]]
    if len(res_difference)>= 1:
        banderaSar = True
        totalSar = str(df['area'].sum())
    else:
        banderaSar = False
        totalSar = '0'
    res_difference.to_file(nombre, driver="GeoJSON")
    return banderaSar, totalSar, nombre

def tierraMascara(cuadrante,pathMask,pathTmp):
    #gdal.Translate(pathTmp+'tmp_mask.tif',dsMascara,options=gdal.TranslateOptions(projWin=cuadrante))
    cuadrante = str(cuadrante[0])+' '+str(cuadrante[1])+' '+str(cuadrante[2])+' '+str(cuadrante[3])
    os.system('gdal_translate -projwin '+cuadrante+' '+pathMask+' '+pathTmp+'landMask_tmp.tif')

def aguaMascara(cuadrante,pathSCL,pathTmp):
    # Esta parte e spara ver si funciona mejor con solo agua
    #os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'aguaMask.tif --calc="0*(A!=2)+0*(A!=3)+0*(A!=10)+1*(A==2)+1*(A==3)+1*(A==10)"')
    os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'aguaMask.tif --calc="0*(A!=2)+1*(A==2)"')

def nubesMascara(cuadrante,pathSCL,pathTmp):
    cuadrante = str(cuadrante[0])+' '+str(cuadrante[1])+' '+str(cuadrante[2])+' '+str(cuadrante[3])

    # Esta parte es para eficientizar la poligonizacion de las nubes
    #os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'cirrusMask.tif --calc="0*(A!=8)"')
    os.system('gdal_calc.py -A '+pathSCL+' --outfile='+pathTmp+'cirrusMask.tif --calc="0*(A!=8)+0*(A!=9)+0*(A!=10)++1*(A==8)+1*(A==9)+1*(A==10)"')

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
        df = df.buffer(350)
        df_g = df.unary_union
        df = gpd.GeoDataFrame(crs=df.crs, geometry=[df_g])
        df.to_file(pathTmp+"cloudMask_b250_tmp.geojson", driver='GeoJSON')
        os.system('gdal_rasterize -burn 8 -tr 20 20 -l cloudMask_b250_tmp '+pathTmp+'cloudMask_b250_tmp.geojson '+pathTmp+'cloudMask_b250_tmp.tif')
        os.system('gdal_calc.py -A '+pathTmp+'cloudMask_b250_tmp.tif --outfile='+pathTmp+'cloudMask_b250_bin_tmp.tif --calc="0*(A==8)+1*(A==0)"')
        os.system('gdal_translate -projwin '+cuadrante+' '+pathTmp+'cloudMask_b250_bin_tmp.tif '+pathTmp+'cloudMask_b250_bin_rec_tmp.tif')

        return banderaNub

def detfooMascara(detfoo_dist,pathInput,pathOutput):
    #ogr2ogr -f "GeoJSON" MSK_DETFOO_B04.geojson MSK_DETFOO_B04.gml
    detfoo = 'MSK_DETFOO_B8A.gml'
    archivoQuality = nomDirQuality(pathInput,detfoo)
    gdf = gpd.read_file(archivoQuality)

    gdf = gdf.sort_values(by=['gml_id'])
    gdf_crs = gdf.crs
    ext = gdf.iloc[0].geometry.bounds

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
    os.system('gdal_calc.py -A '+pathInput+'alg_tmp_numpy.tif -B '+pathInput+'cloudMask_b250_bin_rec_tmp.tif --outfile='+pathInput+'alg_mask_tmp_numpy.tif --calc="A*B"')

def pixelNubesBajas(dsRef,dsSar,nubesBajas):
	nuMask = dsRef.ReadAsArray()
	b4 = dsRef.ReadAsArray()
	sar = dsSar.ReadAsArray()

	cont = 0
	listaBanderas = []

	# Valor de referencia B4 Sugerido 900
	nubeBaja = nubesBajas

	for i in range(nuMask.shape[0]-1):
		for j in range(nuMask.shape[1]-1):
			#print(nuMask.shape[0],nuMask.shape[1])
			#print('pocision:',i,j)
			#print('valor:',sar[i,j])
			if sar[i,j] == 1:
				# ESQUINAS
				if (i == 0 and j == 0) and (b4[i,j+1] > nubeBaja or b4[i+1,j+1] > nubeBaja or b4[i+1,j] > nubeBaja):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso1')

				elif (i == 0 and j == nuMask.shape[1]) and (b4[i,j-1] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i+1,j] > nubeBaja):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso2')

				elif (i == nuMask.shape[0] and j == 0) and (b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j+1] > nubeBaja):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso3')

				elif (i == nuMask.shape[0] and j == nuMask.shape[1]) and (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i,j-1] > nubeBaja):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso4')
				#BORDES
				elif (i == 0) and (b4[i,j-1] > nubeBaja or b4[i,j+1] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i+1,j] > nubeBaja or b4[i+1,j+1] > nubeBaja):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso5')

				elif (i == nuMask.shape[0]) and (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j-1] > nubeBaja or b4[i,j+1] > nubeBaja):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso6')

				elif (j == 0) and (b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j+1] > nubeBaja or b4[i+1,j] > nubeBaja or b4[i+1,j+1] > nubeBaja) and (sar[i,j] == 1):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso7')

				elif (j == nuMask.shape[1]) and (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i,j-1] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i+1,j] > nubeBaja):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso8')
				#GENERAL
				elif (b4[i-1,j-1] > nubeBaja or b4[i-1,j] > nubeBaja or b4[i-1,j+1] > nubeBaja or b4[i,j+1] > nubeBaja or b4[i+1,j+1] > nubeBaja or b4[i+1,j] > nubeBaja or b4[i+1,j-1] > nubeBaja or b4[i,j-1] > nubeBaja):
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
				# SARGAZO
				else:
					nuMask[i,j] = 1
			else:
				nuMask[i,j] = 0

	#print(cont)
	#print(bandera)
	print(set(listaBanderas))
	#np.save("nuMask.npy",nuMask)

	return nuMask
