# General definitions and configuration
# Set the Copernicus access credentials here

# ------------------------------------------------------------------------------

# Copernicus API access credentials
# Insert your api credencials
Copernicus_username = "lanot_2020"
Copernicus_password = "lanot_2020"

# ------------------------------------------------------------------------------

# Some tiles of interest in UTM/MGRS format

# SENTINEL-2A and SENTINEL-2B occupy the same orbit, but separated by 180 degrees. The mean orbital altitude is 786 km. The orbit inclination is 98.62 and the Mean Local Solar Time (MLST) at the descending node is 10:30.

tiles = {}

# Contiene Cancun
tiles["cancun"] = ["16QEJ"]

# Coastal tiles of the Riviera Maya from Cancun to Tulum
tiles["cancun_tulum"] = ["16QEJ", "16QDH", "16QEH", "16QDG", "16QEG", "16QDF", "16QEF"]

# The complete "Mexican Caribbean", extending to about Cuba eastward and
# down to Honduras southward
tiles["mexican_caribbean"] = [
"16QEJ", "16QFJ", "16QGJ", "16QHJ",
"16QDH", "16QEH", "16QFH", "16QGH", "16QHH",
"16QDG", "16QEG", "16QFG", "16QGG", "16QHG",
"16QDF", "16QEF", "16QFF", "16QGF", "16QHF",
"16QCE", "16QDE", "16QEE", "16QFE", "16QGE", "16QHE",
"16QCD", "16QDD", "16QED", "16QFD", "16QGD", "16QHD",
"16PCC", "16PDC", "16PEC", "16PFC", "16PGC", "16PHC",
]

# The French Antilles: Guadeloupe and Martinique
tiles["french_Antilles"] = [
"20QND", "20QPD", "20QQD",
"20PNC", "20PPC", "20PQC",
"20PNB", "20PPB", "20PQB",
"20PNA", "20PPA", "20PQA"
]

# The French Guiana; 22NCL contains Cayenne
tiles["guyane"] = [
"21NZG", "21NHZ", "22NBM", "22NBN", "22NCN", "22NCM", "22NCL", "22NDN",
"22NDM", "22NDL", "22NEM", "22NEL"
]

# Sargazo1: Region de monitoreo de sargazo
tiles['sargazo_1'] = [
"16QDJ","16QEJ","16QDH","16QEH","16QDG","16QEG","16QDF","16QEF"
]

# Mascara Tierra: Region para generar las mascaras de tierra por año
tiles['mascara_tierra'] = [
"16QCJ","16QDJ","16QEJ","16QCH","16QDH","16QEH","16QCG","16QDG","16QEG","16QCF","16QDF","16QEF","16QCE","16QDE","16QEE"
]

tiles["prueba"] = [
"16QEG"
]
# ------------------------------------------------------------------------------
