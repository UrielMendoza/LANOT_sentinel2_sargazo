# Instalador que descarga las dos versiones de se2core y descarga las mascaras y archivos de prueba

wget http://step.esa.int/thirdparties/sen2cor/2.5.5/Sen2Cor-02.05.05-Linux64.run;
wget http://step.esa.int/thirdparties/sen2cor/2.8.0/Sen2Cor-02.08.00-Linux64.run;
sh Sen2Cor-02.05.05-Linux64.run;
sh Sen2Cor-02.08.00-Linux64.run;
rm Sen2Cor-02.05.05-Linux64.run;
rm  Sen2Cor-02.08.00-Linux64.run;
mkdir -p ./data/masks/;
mkdir -p ./data/masks/;
mkdir -p ./test/L1C/T16QEF/2020/;
mkdir -p ./test/L2A/;
mkdir -p ./test/geojson/sargazo/;
mkdir -p ./test/geojson/empty/;
mkdir -p ./test/geotiff/sargazo/;
mkdir -p ./test/tmp/automatico;
mkdir -p ./test/tmp/manual;
mkdir -p ./test/tmp/historico;
wget -P ./data/masks/ http://132.247.103.154/tmp/sargazo/data/masks/land_sargazo_UTM16N_20m.tif;
wget -P ./data/masks/ http://132.247.103.154/tmp/sargazo/data/masks/land_sargazo_UTM16N_20m_b2km.tif;
wget -P ./data/masks/ http://132.247.103.154/tmp/sargazo/data/masks/land_sargazo_UTM16N_20m_b5km.tif;
wget -P ./test/L1C/T16QEF/2020/ http://132.247.103.154/tmp/sargazo/test/L1C/T16QEF/2020/S2B_MSIL1C_20200720T160829_N0209_R140_T16QEF_20200720T193314.zip;
mkdir -p ../logs_sentinel2_sargazo;
wget -P ../logs_sentinel2_sargazo/ http://132.247.103.154/tmp/sargazo/data/logs/proc_L1C_L2A.txt;
wget -P ../logs_sentinel2_sargazo/ http://132.247.103.154/tmp/sargazo/data/logs/proc_L2A_sargazo.txt;
wget -P ../logs_sentinel2_sargazo/ http://132.247.103.154/tmp/sargazo/data/logs/proc_L2A_sargazoGeoTiff.txt;
wget -P ../logs_sentinel2_sargazo/ http://132.247.103.154/tmp/sargazo/data/logs/proc_L2A_sargazo_b2km.txt;
wget -P ../logs_sentinel2_sargazo/ http://132.247.103.154/tmp/sargazo/data/logs/proc_L2A_sargazo_b5km.txt;
# Falta crear lo logs directorio y encabezados txt
# Falta crear peticion para la ruta del input y output