import os
from processing_sentinel2 import listaArchivos,nomDir,tipoCompresion,descomprime,obtieneFechaLog,obtieneAnio,sen2core,log,obtieneArchivoZip,verificaLog

pathSen2core_8 = '/home/lanotadm/sargazo/Sen2Cor-02.08.00-Linux64/bin/'
pathCFG_8 = '/home/lanotadm/sen2cor/2.8/cfg/L2A_GIPP.xml'
pathSen2core_5 = '/home/lanotadm/sargazo/Sen2Cor-02.05.05-Linux64/bin/'
pathCFG_5 = '/home/lanotadm/sen2cor/2.5/cfg/L2A_GIPP.xml'
pathInput = '/data/input/sentinel2/L1C/'
pathOutput = '/data/input/sentinel2/L2A/'
pathTmp = '/data/input/sentinel2/tmp/'
pathLog = '/home/lanotadm/sargazo/logs/proc_L1C_L2A.txt'

tiles = list(map(lambda x : x.split('/')[-1],listaArchivos(pathInput+'*')))
#cont = 0
for tile in tiles:
	aniosDir = listaArchivos(pathInput+tile+'/*')
	for anioDir in aniosDir:
		archivos = listaArchivos(anioDir+'/*')
		for archivo in archivos:
			compresion = tipoCompresion(archivo)
			if compresion == 'zip':
				print(archivo)
				if not verificaLog(pathLog,archivo):
					descomprime(archivo,compresion,pathTmp)
					dirL1C = nomDir(archivo,'L1C')
					# Solucion para fallo de sen2core opcional
					#os.system('sudo mkdir '+pathTmp+dirL1C+'/AUX_DATA')
					
					if int(anioDir) < 2018:
						sen2core(pathSen2core_8,pathCFG_8,pathTmp+dirL1C,pathOutput+tile+'/','20')
					else:
						sen2core(pathSen2core_5,pathCFG_5,pathTmp+dirL1C,pathOutput+tile+'/','20')
					
					#Comprimir el L2 y guardarlo en el txt
					dirL2A = listaArchivos(pathTmp+'*L2*')[0]
					anio = obtieneAnio(archivo)
					archivoZip = obtieneArchivoZip(dirL2A)

					os.system('mkdir -p '+pathOutput+tile+'/'+anio)
					
					os.system('cd '+pathTmp+';zip -r '+pathOutput+tile+'/'+anio+'/'+dirL2A.split('/')[-1].split('.')[0]+'.zip ./'+dirL2A.split('/')[-1])
					os.system('cd '+'/'.join(dirL2A.split('/')[:-1])+';zip -r '+archivoZip+' '+dirL2A.split('/')[-1]+';mv '+archivoZip+' '+pathOutput+tile+'/'+anio)
					
					os.system('rm -r '+pathTmp+dirL1C)
					os.system('rm -r '+dirL2A)
					#os.system('rm -r '+pathTmp+'\*L2*')

					fecha = obtieneFechaLog()
					
					log(pathLog,archivo,pathOutput+tile+'/'+anio+'/'+dirL2A.split('/')[-1].split('.')[0]+'.zip',fecha)
					#cont+=1
				else:
					print('Archivo: '+archivo+' ya fue procesado a L2A')
#print(cont)
