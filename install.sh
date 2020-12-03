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
mkdir -p ./test/sargazo/empty;
mkdir -p ./test/sargazo/geojson/;
mkdir -p ./test/tmp/;
wget -P ./data/masks/ http://132.247.103.154/tmp/sargazo/data/masks/land_sargazo_UTM16N_20m.tif;
wget -P ./test/L1C/T16QEF/2020/ http://132.247.103.154/tmp/sargazo/test/L1C/T16QEF/2020/S2B_MSIL1C_20200720T160829_N0209_R140_T16QEF_20200720T193314.zip;
# Falta crear lo logs directoiro y encabezados txt
# Falta crear peticion para la ruta del input y output