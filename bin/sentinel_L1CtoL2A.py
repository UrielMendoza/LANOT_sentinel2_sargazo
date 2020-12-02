import os
from processing_sentinel import listaArchivos,nomDir,tipoCompresion,descomprime,obtieneFechaLog,obtieneAnio,sen2core,log

#pathSen2core = '/home/lanotadm/sargazo/Sen2Cor-02.08.00-Linux64/bin/'
pathSen2core = '/home/lanotadm/sargazo/Sen2Cor-02.05.05-Linux64/bin/'
#pathCFG = '/home/lanotadm/sen2cor/2.8/cfg/L2A_GIPP.xml'
pathCFG = '/home/lanotadm/sen2cor/2.5/cfg/L2A_GIPP.xml'
resolution = '20'
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
				descomprime(archivo,compresion,pathTmp)
				dirL1C = nomDir(archivo,'L1C')
				# Solucion para fallo de sen2core opcional
				#os.system('sudo mkdir '+pathTmp+dirL1C+'/AUX_DATA')
				sen2core(pathSen2core,pathCFG,pathTmp+dirL1C,pathOutput+tile+'/',resolution)
				dirL2A = listaArchivos(pathTmp+'*L2*')[0]
				anio = obtieneAnio(archivo)

				os.system('mkdir -p '+pathOutput+tile+'/'+anio)

				os.system('cd '+pathTmp+';zip -r '+pathOutput+tile+'/'+anio+'/'+dirL2A.split('/')[-1].split('.')[0]+'.zip ./'+dirL2A.split('/')[-1])
				os.system('rm -r '+pathTmp+dirL1C)
				os.system('rm -r '+dirL2A)
				#os.system('rm -r '+pathTmp+'\*L2*')

				fecha = obtieneFechaLog()

				#Comprimir el L2 y guardarlo en el txt
				log(pathLog,archivo,pathOutput+tile+'/'+anio+'/'+dirL2A.split('/')[-1].split('.')[0]+'.zip',fecha)
				#cont+=1
#print(cont)
