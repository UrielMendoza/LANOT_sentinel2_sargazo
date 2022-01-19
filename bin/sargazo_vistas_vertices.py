#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon 20 Sep 2021 06:29:33 PM CDT

@author: Alejandro Aguilar Sierra, asierra@unam.mx 
Laboratorio Nacional de Observación de la Tierra, UNAM

Input fecha
Output png

Versión 1.0

"""

description = "Genera una imagen TC combinada con polígonos de sargazo correspondientes a una fecha específica."

import os
import re
import sys
import json
import glob
import datetime
from PIL import Image, ImageDraw
from pathlib import Path
from osgeo import gdal,osr

#lanotdir = '/usr/local/share/lanot'
#outdir = './'
#verticesdir = '/data/output/sentinel2/l2/geojson/sargazo_vertices'
#geotiffdir = '/data/output/sentinel2/l2/geotiff/TC'

Image.MAX_IMAGE_PIXELS = 614960590 
white = (255, 255, 255)

ulx = 399960.0
uly = 2400000.0
lrx = 709800.0
lry = 1990200.0

height = 1200
width = 1200

area = 0

def mapeo(x, y):
    u = int(width*(x - ulx)/(lrx - ulx))
    v = int(height*(uly - y)/(uly - lry))
    return u, v

def lee_poligonos(filename, image):
    f = open(filename)
    data = json.load(f)
    draw = ImageDraw.Draw(image)
    d = 2
    global area

    for i in data['features']:
        p = i['geometry']['coordinates']
        a = i['properties']['area_km2']
        #print(type(p), p[0][0], a)
        area += a
        puntos = []
        d = 1
        for j in p:
            #print(j)
            x, y = j
            u, v = mapeo(x, y)
            #puntos.append((u,v))
            #print(x, y, u, v)
            draw.rectangle([u-d,v-d,u+d,v+d], fill=(255,0,0,255))
        #draw.polygon(puntos, fill=(255,0,0,255))
  
    f.close()

def lee_vertices(filename, image):
    import json

    f = open(filename)
    data = json.load(f)

    draw = ImageDraw.Draw(image)
    d = 2
    for i in data['features']:
        x, y = i['geometry']['coordinates']
        u, v = mapeo(x, y)
        print(x, y, u, v)
        draw.rectangle([u-d,v-d,u+d,v+d], fill=(255,0,0,255))
  
    f.close()

import aggdraw

def draw_text(x, y, text, align, bw=5):
    global font
    global draw
    p = aggdraw.Pen("white", 0.5)
    b = aggdraw.Brush((0,0,0), 100)
    title_sz =  draw.textsize(text, font)
    if align == 1:
        x -= title_sz[0]/2
    elif align == 2:
        x -= title_sz[0]
    draw.rectangle((x-bw, y, x+title_sz[0]+bw, y+title_sz[1]), b, b) 
    draw.text((x, y), text, font)
    draw.flush()
    
def GetExtent(gt,cols,rows):
    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]
    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            ext.append([x,y])
            #print x,y
        yarr.reverse()
    return ext

def get_limits(path):
    global ulx, uly, lrx, lry
    ds = gdal.Open(path)
    gt=ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    ext=GetExtent(gt,cols,rows)
    ulx = ext[0][0]
    uly = ext[0][1]
    lrx = ext[2][0]
    lry = ext[2][1]
    
def vistasSargazo(fecha, region, pathTmp, pathOutputGeoTiff, pathVertices, pathOutputVistas, pathLanot, pathOutputPeta, pathOutputWeb):

    #if len(sys.argv) < 2:
    #    print("Usanza: ", sys.argv[0], " <fecha YYYMMDDTHHMM>")
    #    exit(1)

    label = fecha
    pattern = re.compile(label)
    #lista = []
    #for filename in os.listdir(verticesdir):
     #   if pattern.match(filename, 18):
      #      print(filename)
       #     files.append(filename)


    fecha = datetime.datetime.strptime(label, '%Y%m%dT%H%M%S')
    fecha_str = fecha.strftime("%Y/%m/%d %H:%M")
    print(fecha, fecha_str, label)

    lista = glob.glob(pathVertices+"/*"+label+"*.json")

    print("Lista", lista, len(lista))
    
    if len(lista) == 0:
        print("Error: No existe fecha", label)
        exit(1)

    # Crear la imagen base con todos los mosaicos
    mosaicos = ''
    for path in Path(pathOutputGeoTiff).rglob('*'+label+'*.tif'):
        print(path, type(path))
        mosaicos += str(path) + ' '

    print("gdal_merge.py -o "+pathTmp+"tmp.tif "+mosaicos)
    os.system("gdal_merge.py -o "+pathTmp+"tmp.tif "+mosaicos)
    path = pathTmp+"tmp.tif"
    get_limits(path)
    print(ulx, uly, lrx, lry)
    
    im_in = Image.open(path)
    height = 1200
    width = int(height * im_in.width / im_in.height)
    im_in = im_in.resize((width, height)).convert('RGB')

    for pathjson in lista:
        lee_poligonos(pathjson, im_in)
        #lee_vertices(pathjson, im_in)

    logo = Image.open(pathLanot + '/logos/lanot_negro_sn.jpg')
    w = 200
    h = int(w * logo.height / logo.width)
    logo = logo.resize((w, h))
    im_in.paste(logo, (10, 140))

    draw = aggdraw.Draw(im_in)
    p = aggdraw.Pen("white", 0.5)
    b = aggdraw.Brush((0,0,0), 100)
    white = (255, 255, 255)
    font = aggdraw.Font(white, "/usr/share/fonts/truetype/ttf-bitstream-vera/VeraMono.ttf", 30)

    title = "Sargazo "+fecha_str+" Z"
    draw_text(im_in.width-15, im_in.height - 75, title, 2)
    print("area ", area)
    #areakm2 = area*1e-6
    areatext = "Area = {:5.4f} km2".format(area)
    print(areatext)
    draw_text(im_in.width-15, im_in.height - 40, areatext, 2)

    # S2_MSI_sargazoTC_s1_20190211T161411
    outfile = pathOutputVistas+"S2_MSI_sargazoTC_"+region+"_"+label+".png"
    print(outfile)
    print("Guardando", outfile)
    im_in.save(outfile)

    # MANDA A PETA
    os.system('scp '+outfile+' lanotadm@stratus:'+pathOutputPeta+'vistas/sargazo_TC/')
    # MANDA A WEB
    os.system('scp '+outfile+' sargazo@cumulus:'+pathOutputWeb+'vistas/sargazo_TC/')