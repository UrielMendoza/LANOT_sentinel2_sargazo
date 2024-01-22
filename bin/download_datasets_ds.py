'''
Utilities to search for and download Sentinel-2 datasets with Datspace Copernicus.
The Copernicus access credentials are stored in the base.py file.

@autor: urielm
@date: 2024-01-18
'''
# ==============================================================================

import datetime
import os
import zipfile
import pandas as pd
import requests
import json
from creds import * 
import time

import base


# ==============================================================================

def search_products(tile=None, date=None, search_string=None, product_type="L1C", satellite=None, query_args=None) -> dict: 
  '''
  Searches Copernicus DataSpace for Sentinel-2 datasets (products) for a given
  tile and date. Alternatively, if search_string is given pass that directly
  to the Copernicus API (ignoring all other arguments).
  Parameters:
  tile : string
    The UTM/MGRS tile, e.g. '16QEJ'
  date : datetime object
  '''
  # Date in format YYYYMMDD
  date = date.strftime("%Y%m%d")
  # Level of the product
  if product_type == "L1C":
    level = "MSIL1C"
  
  # Join the level and date
  date = f"{level}_{date}"

  products = {}
  #ids_ds = []
  #names = []
  #origin_dates = []

  # Build the URL with the search parameters
  url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=contains(Name, '{date}') and contains(Name, '{tile}')"

  # Set the pettion to DataSpace and obtain the JSON response
  json_response = requests.get(url).json()

  # Create a DataFrame from the JSON response
  df = pd.DataFrame.from_dict(json_response["value"]).iloc[0]

  # Print the DataFrame
  #print(df)

  # Save the parameters of the response
  id_ds = df['Id']
  name = df['Name']
  origin_date = df['OriginDate']
  print(id)
  print(name)
  #ids_ds.append(id_ds)
  #names.append(name)

  #origin_dates.append(origin_date)
  
  products['ids'] = id_ds
  products['names'] = name
  products['tiles'] = tile
  products['origin_dates'] = origin_date

  return products

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def get_access_token(username: str, password: str) -> str:
  '''
  Get an access token for the Copernicus DataSpace API.
  Parameters:
    username : str
      The username for the Copernicus DataSpace API
    password : str
      The password for the Copernicus DataSpace API
  '''
  data = {
      "client_id": "cdse-public",
      "username": username,
      "password": password,
      "grant_type": "password",
      }
  try:
      r = requests.post("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
      data=data,
      )
      r.raise_for_status()
  except Exception as e:
      raise Exception(
          f"Access token creation failed. Reponse from the server was: {r.json()}"
          )
  return r.json()["access_token"]
        
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def download_products(products, datadir, unzip=False, max_retries=5, verbose=True):
  '''
  Downloads a set of Sentinel-2 products.
  Parameters:
    products : dict
      A dict with Sentinel-2 products, as returned by SentinelAPI.query() or
      search_products()
    datadir : string
      The directory to save the downloaded products to
    unzip : boolean (default: False)
      If True, unzip the downloaded products
    max_retries : int (default: 5)
      How many times to retry downloading a product if the download fails
    verbose : boolean (default: True)
      If True, print status messages
  '''
   # Get the access token with the credentials
  access_token = get_access_token(base.Dataspace_username, base.Dataspace_password)
  #print(access_token)

  # Using the product ID and access token, you can download the product
  #url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products(22018785-4dca-4e29-b40f-926dd0c1aa99)/$value"

  #for id, name, tile, origin_date in zip(products['ids'], products['names'], products['tiles'], products['origin_dates']):  
  id = products['ids']
  name = products['names']
  tile = products['tiles']
  origin_date = products['origin_dates']

  url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({id})/$value"
  headers = {"Authorization": f"Bearer {access_token}"}

  session = requests.Session()
  session.headers.update(headers)
  response = session.get(url, headers=headers, stream=True)

  # Create dir with the tile name
  if not os.path.exists(f"{datadir}T{tile}"):
    os.makedirs(f"{datadir}T{tile}") 

  if unzip:
    with open(f"{datadir}T{tile}/{name}.zip", 'wb') as file:
        print(f'Downloading {tile} {origin_date} {id}...')
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
  # Wait to download the file
  #time.sleep(30)

# ------------------------------------------------------------------------------

def search_and_download_datasets(tiles, start_date, end_date, datadir, unzip=False, max_retries=3, verbose=True, query_args=None):
  '''
    Searches Copernicus DataSpace for Sentinel-2 datasets (products) for a given
    tile and date, and downloads them.
    Parameters:
      tile : string
        The UTM/MGRS tile, e.g. '16QEJ'
      start_date : datetime object
      end_date : datetime object
      datadir : string
        The directory to save the downloaded products to download_products()
      unzip : boolean (default: False)
        If True, unzip the downloaded products
      max_retries : int (default: 5)
        How many times to retry downloading a product if the download fails
      verbose : boolean (default: True)
        If True, print status messages
      query_args : dictionary (default: None)
        Additional query arguments to be passed directly to SentinelAPI.query().
  '''
  for tile in tiles:
    # Find products
    products = search_products(tile, start_date, end_date, query_args=query_args)
    # Download products
    download_products(products, datadir, unzip=unzip, max_retries=max_retries, verbose=verbose)
    # Empty the products dictionary
    products = None


# ==============================================================================


if __name__ == "__main__":
  # Download the specified tiles in the given range of dates from Copernicus DataSpace
  tiles = base.tiles["prueba"]
  datadir ='../'

  start_date = datetime.date(2024, 1, 16)
  end_date = datetime.date(2024, 1, 16)
  step = datetime.timedelta(days=1)

  print('Sentinel-2\nInicio:',end_date,'\nTermino:',start_date)

  # ------------------------------------------------------------------------------
  search_and_download_datasets(tiles, start_date, end_date, datadir, unzip=True)

