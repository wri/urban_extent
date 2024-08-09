import requests
from unidecode import unidecode
import re
import pandas as pd
import geopandas as gpd
from translate import Translator
from shapely.geometry import Point
import ee

import geelayers

# Google
with open('key.txt') as f:
    f = f.readlines()
api_key = f[0]
GOOGLE_MAPS_API_KEY = api_key


def geocode_address(city_list, api_key):
    for idx, city_row in city_list.iterrows():
        if idx % 200 == 0:
            print(idx)
        if city_row.notna().loc['UC_NM_MN'] and city_row.notna().loc['CTR_MN_NM']:
            city_name = ','.join([city_row['UC_NM_MN'], city_row['CTR_MN_NM']])
            city_name = unidecode(city_name.strip())
            city_name = re.sub(r'[^A-Za-z0-9\-\_]+', '', city_name)
            url = 'https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'.format(city_name, api_key)
            response = requests.get(url)
            if len(response.json()['results']) > 0:
                output = response.json()['results'][0]['address_components']
                full_name = ', '.join(op['long_name'] for op in output)
                lat = response.json()['results'][0]['geometry']['location']['lat']
                lon = response.json()['results'][0]['geometry']['location']['lng']
                city_list.loc[idx, 'FULL_NAME'] = full_name
                city_list.loc[idx, 'LAT'] = lat
                city_list.loc[idx, 'LON'] = lon
            else:
                continue
        else:
            continue

    # return LON, LAT, FULL_NAME
    return city_list


df = pd.read_csv('data/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.csv', encoding='latin1', low_memory=False)
df = df.dropna(how='all')
city_list = df[['ID_HDC_G0', 'UC_NM_MN', 'CTR_MN_NM']]
city_list = geocode_address(city_list, api_key)
city_list.to_csv('data/city_data_google.csv')


###### Convert manual check results to checked dataset
df = pd.read_csv('data/city_data_to_check_wz.csv', encoding='latin1', low_memory=False)

df.loc[df['SELECT'].notna() & (df['SELECT'] != '') & (df['SELECT'] != 'ToDo'), 'USE_COM'] = 'FALSE'
df.loc[df['SELECT'].notna() & (df['SELECT'] != '') & (df['SELECT'] != 'ToDo'), 'USE_INSPECTED_CENTROIDS'] = 'FALSE'
df.loc[df['SELECT'].notna() & (df['SELECT'] != '') & (df['SELECT'] != 'ToDo'), 'UC_NM_MN'] = df['UC_NM_MN_ORIGINAL']


df.loc[df['SELECT'] == 'COM', 'USE_COM'] = 'TRUE'
df.loc[df['SELECT'] == 'Inspected', 'USE_INSPECTED_CENTROIDS'] = 'TRUE'
df.loc[df['SELECT'] == 'Google', 'USE_INSPECTED_CENTROIDS'] = 'TRUE'
df.loc[df['Inspected_names'].notna() & (df['Inspected_names'] != ''), 'UC_NM_MN'] = df['Inspected_names']


df.loc[df['SELECT'] == 'Source', 'geometry'] = [
    Point(xy) for xy in zip(df.loc[df['SELECT'] == 'Source', 'GCPNT_LON'], df.loc[df['SELECT'] == 'Source', 'GCPNT_LAT'])]
df.loc[df['SELECT'] == 'COM', 'geometry'] = [
    Point(xy) for xy in zip(df.loc[df['SELECT'] == 'COM', 'COM_LON'], df.loc[df['SELECT'] == 'COM', 'COM_LAT'])]
df.loc[df['SELECT'] == 'Overture', 'geometry'] = [
    Point(xy) for xy in zip(df.loc[df['SELECT'] == 'Overture', 'Overture_LON'], df.loc[df['SELECT'] == 'Overture', 'Overture_LAT'])]
df.loc[df['SELECT'] == 'Google', 'geometry'] = [
    Point(xy) for xy in zip(df.loc[df['SELECT'] == 'Google', 'G_LON'], df.loc[df['SELECT'] == 'Google', 'G_LAT'])]
df.loc[df['SELECT'] == 'Inspected', 'geometry'] = [
    Point(xy) for xy in zip(df.loc[df['SELECT'] == 'Inspected', 'Inspected_LON'], df.loc[df['SELECT'] == 'Inspected', 'Inspected_LAT'])]

gdf = gpd.GeoDataFrame(df, geometry='geometry')
gdf.drop(columns=['SELECT', 'Inspected_LON', 'Inspected_LAT', 'Inspected_names'], axis=1, inplace=True)
gdf = gdf.dropna(subset=['geometry'])
gdf.to_csv('data/city_data_checked.csv', index=False)

gdf = gdf.loc[df['GRGN_L1'] == 'Africa', :]
gdf.to_csv('data/city_data_checked_africa.csv', index=False)


###### Check ToDo cities
df = pd.read_csv('data/city_data_to_check_wz.csv', encoding='latin1', low_memory=False)
for cID in df['ID_HDC_G0']:
    if cID % 100 == 0:
        print(cID)
    non_na_pixels = geelayers.BU_CONNECTED.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=ee.Feature(ee.FeatureCollection(geelayers.CITY_DATA_POLY).filter(ee.Filter.eq('ID_HDC_G0', cID)).first()).geometry(),
        scale=100,
        maxPixels=1e9
    ).get('builtup')
    df.loc[df['ID_HDC_G0'] == cID, 'COULD_DO'] = bool(ee.Number(non_na_pixels).gt(0).getInfo())
df.to_csv('data/city_data_to_check_wz_todo.csv', index=False)

###### Check city name
df = pd.read_csv('data/city_data_checked.csv', encoding='latin1', low_memory=False)
filtered_df_1 = df[pd.isna(df['UC_NM_MN'])]
df = df[~pd.isna(df['UC_NM_MN'])]
pattern = re.compile(r'[^\x00-\x7F]')
filtered_df_2 = df[df['UC_NM_MN'].apply(lambda x: pattern.search(x) is not None)]
filtered_df = pd.concat([filtered_df_1, filtered_df_2], ignore_index=True)
filtered_df = filtered_df.sort_values(by='ID_HDC_G0')
filtered_df.to_csv('data/city_name_to_check.csv', index=False)
