# sargazo_sentinel2
 Deteccion automatica de sargazo en el caribe mexicano, mediante imagenes Sentinel-2.
## Desarrollo
 Desarrollado en en Laboratorio Nacional de Observacion de la Tierra LANOT, IGG UNAM.
## Descripción
 * Descarga automatica de imagenes del data hub Copernicus.
 * Conversion de nivel L1C a L2A, mediante el paquete sen2cor.
 * Algoritmo de busqueda por condicional en las bandas del infrarojo.
 * Aplicacion de mascaras de tierra, nube alta con buffer para eliminar bordes y nube baja con filtro de vecindad.
 * Poligonización de los datos binarios.
