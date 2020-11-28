#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 23:52:19 2020

@author: urielm
"""
import os
from glob import glob
from osgeo import gdal,osr
import geopandas as gpd
import datetime
import numpy as np
import matplotlib.pyplot as plt

def sen2core(pathSen2Core,pathCFG,pathInput,pathOutput,resolution):
        os.system(pathSen2Core+'L2A_Process --resolution '+resolution+' --GIP_L2A '+pathCFG+' '+pathInput)

def log(pathLog,archivo,archivoProc,fecha):
        file = open(pathLog,'a')
        file.write('\n'+archivo+','+archivoProc+','+fecha)
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

def listaArchivos(pathInput):
    archivos = glob(pathInput)
    return archivos

def listaBandas(pathInput,nivel,banda):
    if nivel == 'L2A':
        archivoBanda = glob(pathInput+'/GRANULE/L2*/IMG_DATA/R20m/*'+banda+'*.jp2')
    elif nivel == 'L1C':
        archivoBanda = glob(pathInput+'/GRANULE/L1C*/IMG_DATA/*.jp2')
    elif nivel == 'L1C_resampled':
        archivoBanda = glob(pathInput+'/'+banda+'.img')
    #print(archivoBanda)
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

def obtieneFecha(pathDir):
    fecha = pathDir.split('/')[-1].split('.')[0].split('_')[-1]
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
    gdal.Translate(pathOutput+tif+'.tif',ds)

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

def remuestrea(salida,ds,dimx,dimy):
    gdal.Translate(salida,ds,options=gdal.TranslateOptions(xRes=dimx,yRes=dimy))

def RGB(r,g,b,salida):
    os.system('gdal_merge.py -separate -co PHOTOMETRIC=RGB -o '+salida+' '+r+' '+g+' '+b)

def poligonizacion(tile,anio,fecha,pathInput,pathOutput,pathOutputEmpty):
    index = 0
    time = datetime.datetime.strptime(fecha,'%Y%m%dT%H%M%S')
    os.system('gdal_polygonize.py '+pathInput+'nubesBajas_mask.tif -f "GeoJSON" '+pathInput+'alg_mask_filter_tmp.json')
    df = gpd.read_file(pathInput+'alg_mask_filter_tmp.json')
    df = df[df.DN == 1]

    if len(df)>= 1:
        print('Deteccion de saragazo: ',len(df),' elementos')
        os.system('mkdir -p '+pathOutput+tile+'/'+anio)
        df["area"] = round(df['geometry'].area,2)
        df['fecha'] = fecha
        df['tile'] = tile
        df['index'] = index
        df['IDpolygon'] = range(1, len(df) + 1)
        df.to_file(pathOutput+tile+'/'+anio+'/'+'S2_MSI_SAR_'+tile+'_'+fecha+".json", driver="GeoJSON")
        index = index + 1
        return pathOutput+tile+'/'+anio+'/'+'S2_MSI_SAR_'+tile+'_'+fecha+".json"
    else:
        print('No deteccion de sargazo')
        os.system('mkdir -p '+pathOutputEmpty+tile+'/'+anio)
        f = open(pathOutputEmpty+tile+'/'+anio+'/'+'S2_MSI_SAR_'+tile+'_'+fecha+".txt",'w')
        f.write('No detección de sargazo')
        f.close()
        #print('Tile:'+tile+'\nFecha:'+fecha)
        return pathOutputEmpty+tile+'/'+anio+'/'+'S2_MSI_SAR_'+tile+'_'+fecha+".txt"

def tierraMascara(cuadrante,pathMask,pathTmp):
    #gdal.Translate(pathTmp+'tmp_mask.tif',dsMascara,options=gdal.TranslateOptions(projWin=cuadrante))
    cuadrante = str(cuadrante[0])+' '+str(cuadrante[1])+' '+str(cuadrante[2])+' '+str(cuadrante[3])
    os.system('gdal_translate -projwin '+cuadrante+' '+pathMask+' '+pathTmp+'landMask_tmp.tif')

def nubesMascara(cuadrante,pathSCL,pathTmp):
    cuadrante = str(cuadrante[0])+' '+str(cuadrante[1])+' '+str(cuadrante[2])+' '+str(cuadrante[3])
    os.system('gdal_polygonize.py '+pathSCL+' -f "GeoJSON" '+pathTmp+'SCL_tmp.json')
    df = gpd.read_file(pathTmp+'SCL_tmp.json')
    df = df[df['DN'] == 8]
    if len(df) == 0:
        banderaNub = False
        return banderaNub
    else:
        banderaNub = True
        df = df.buffer(250)
        df_g = df.unary_union
        df = gpd.GeoDataFrame(crs=df.crs, geometry=[df_g])
        df.to_file(pathTmp+"cloudMask_b250_tmp.geojson", driver='GeoJSON')
        os.system('gdal_rasterize -burn 8 -tr 20 20 -l cloudMask_b250_tmp '+pathTmp+'cloudMask_b250_tmp.geojson '+pathTmp+'cloudMask_b250_tmp.tif')
        os.system('gdal_calc.py -A '+pathTmp+'cloudMask_b250_tmp.tif --outfile='+pathTmp+'cloudMask_b250_bin_tmp.tif --calc="0*(A==8)+1*(A==0)"')
        os.system('gdal_translate -projwin '+cuadrante+' '+pathTmp+'cloudMask_b250_bin_tmp.tif '+pathTmp+'cloudMask_b250_bin_rec_tmp.tif')

        return banderaNub

def sargazoBin(banderaNub,nivel,pathInput,pathOutput):
    os.system('gdal_calc.py -A '+pathInput+'B8A.tif -B '+pathInput+'B04.tif -C '+pathInput+'B11.tif --outfile='+pathOutput+'alg_tmp.tif --calc="logical_and(A>1000,B<1000,C<500)"')
    if nivel == 'L1C' or banderaNub == False:
        os.system('gdal_calc.py -A '+pathOutput+'alg_tmp.tif -B '+pathInput+'landMask_tmp.tif --outfile='+pathOutput+'alg_mask_tmp.tif --calc="A*B"')
    elif nivel == 'L2A' and banderaNub == True:
        os.system('gdal_calc.py -A '+pathOutput+'alg_tmp.tif -B '+pathInput+'landMask_tmp.tif -C '+pathInput+'cloudMask_b250_bin_rec_tmp.tif --outfile='+pathOutput+'alg_mask_tmp.tif --calc="A*B*C"')
    #os.system('gdal_calc.py -A '+pathOutput+tile+'_'+fecha+'_result_bin.tif -B '+pathInput+'maskNubes_b250_bin_tmp.tif --outfile='+pathOutput+tile+'_'+fecha+'_result_binFinal.tif --calc="A*B"')

def pixelNubesBajas(dsRef,dsSar):
	nuMask = dsRef.ReadAsArray()
	b4 = dsRef.ReadAsArray()
	sar = dsSar.ReadAsArray()

	cont = 0
	listaBanderas = []

	for i in range(nuMask.shape[0]):
		for j in range(nuMask.shape[1]):
			#print(nuMask.shape[0],nuMask.shape[1])
			#print('pocision:',i,j)
			#print('valor:',sar[i,j])
			if sar[i,j] == 1:
				# ESQUINAS
				if (i == 0 and j == 0) and (b4[i,j+1] > 1000 or b4[i+1,j+1] > 1000 or b4[i+1,j] > 1000):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso1')

				elif (i == 0 and j == nuMask.shape[1]) and (b4[i,j-1] > 1000 or b4[i+1,j-1] > 1000 or b4[i+1,j] > 1000):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso2')

				elif (i == nuMask.shape[0] and j == 0) and (b4[i-1,j] > 1000 or b4[i-1,j+1] > 1000 or b4[i,j+1] > 1000):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso3')

				elif (i == nuMask.shape[0] and j == nuMask.shape[1]) and (b4[i-1,j-1] > 1000 or b4[i-1,j] > 1000 or b4[i,j-1] > 1000):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso4')
				#BORDES
				elif (i == 0) and (b4[i,j-1] > 1000 or b4[i,j+1] > 1000 or b4[i+1,j-1] > 1000 or b4[i+1,j] > 1000 or b4[i+1,j+1] > 1000):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso5')

				elif (i == nuMask.shape[0]) and (b4[i-1,j-1] > 1000 or b4[i-1,j] > 1000 or b4[i-1,j+1] > 1000 or b4[i,j-1] > 1000 or b4[i,j+1] > 1000):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso6')

				elif (j == 0) and (b4[i-1,j] > 1000 or b4[i-1,j+1] > 1000 or b4[i,j+1] > 1000 or b4[i+1,j] > 1000 or b4[i+1,j+1] > 1000) and (sar[i,j] == 1):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso7')

				elif (j == nuMask.shape[1]) and (b4[i-1,j-1] > 1000 or b4[i-1,j] > 1000 or b4[i,j-1] > 1000 or b4[i+1,j-1] > 1000 or b4[i+1,j] > 1000):
					nuMask[i,j] = 0
					cont = cont + 1
					listaBanderas.append('Caso8')
				#GENERAL
				elif (b4[i-1,j-1] > 1000 or b4[i-1,j] > 1000 or b4[i-1,j+1] > 1000 or b4[i,j+1] > 1000 or b4[i+1,j+1] > 1000 or b4[i+1,j] > 1000 or b4[i+1,j-1] > 1000 or b4[i,j-1] > 1000):
					nuMask[i,j] = 0
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
