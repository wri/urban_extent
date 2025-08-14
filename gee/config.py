import ee
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
ee.Initialize()


#
# CONFIG
#
"""""""""""""""""""""""""""""""""""""""""""""""""""
Note on STUDY_AREA_SCALE_FACTOR:

if A=a*b=w*a^2, and w=4*alpha
R(circle) ~ alpha * sqrt(A)
ratio=A(circle)/A ~ alpha^2 * pi 

* for w = 16, ratio ~ 12
* for w = 36, ratio ~ 30

Note that city centers might be far from "centered"
"""""""""""""""""""""""""""""""""""""""""""""""""""
#
# CONSTANTS
#
DRY_RUN = False
MAX_NNN_DISTANCE = 2500
MAX_ERR = 1
MINPIXS = 10
SUBURBAN_BOUND = 0.25
URBAN_BOUND = 0.5
COM_SEED = 1234
NB_COM_SAMPLES = 5000
GROWTH_RATE = 0.0666
DENSITY_RADIUS = 564
DENSITY_UNIT = 'meters'
CENTROID_SEARCH_RADIUS = 200
PI = ee.Number.expression('Math.PI')
PPOLICY = {
    'builtup': 'mode',
    'density': 'mean',
}
USE_COMPLETED_FILTER = True  # used


#
# SETTINGS.OPTIONAL
#
# Built-up layer options
# select pixel built-up density threshold
# minimum m2 built out of possible 10000 for each GHSL grid cell included
BuiltAreaThresh = 1000

# Use old UCDB population and built-up area estimates for regional calibration
# City data from Global Human Settlement Layer (GHSL, 13K cities)
# https://human-settlement.emergency.copernicus.eu/ghs_stat_ucdb2015mt_r2019a.php
# linear average relationships between population and built-up area
df = pd.read_csv('data/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.csv', encoding='latin1', low_memory=False)
# Drop rows where all columns are NaN
df = df.dropna(how='all')
# Drop rows where B15 is 0
df = df[df['B15'] != 0]

# Use GRGN_L2 as regions for regression
# Replace value Polynesia with Melanesia in column 'GRGN_L2'
# Only 1 city in Polynesia
df['GRGN_L2'] = df['GRGN_L2'].replace('Polynesia', 'Melanesia')
# .replace('Caribbean', 'Latin America and the Caribbean').replace('South America', 'Latin America and the Caribbean').replace('Central America', 'Latin America and the Caribbean').replace('Australia/New Zealand', 'Australia and New Zealand').replace('Middle Africa', 'Australia and New Zealand')
df['GRGN_L2'].value_counts()

results = {}
for region in df['GRGN_L2'].unique():
    subset = df[df['GRGN_L2'] == region]
    # Prepare the data
    X = np.log(subset[['P15']])
    Y = np.log(subset['B15']*1000000)
    # Perform linear regression
    model = LinearRegression()
    model.fit(X, Y)
    # Store the results
    results[region] = {
        'intercept': model.intercept_,
        'slope': model.coef_[0],
        'score': model.score(X, Y)
    }

FIT_PARAMS = ee.Dictionary(results)


#
# SETTINGS.REQUIRED
#
# Set the built-up year for which to produce extents
# [1980, 1990, 2000, 2005, 2010, 2015, 2020]
mapYear = 2020

# Set output image collection for all processed cities
ROOT = 'projects/wri-datalab/cities/urban_land_use/data'
# Update output image collection id
IC_ID = f'{ROOT}/global_GUPPD_Mar2025/builtup_density_JRCs_{mapYear}a'
# f'{ROOT}/african_cities_July2024/builtup_density_JRCs_africa_1980'
# f'{ROOT}/test_tori_Apr2024/builtup_density_JRCs_Kigali_Nairobi_Addis'

# Input city point feature collection
# Checked city points
# CITY_DATA_POINT = ee.FeatureCollection('projects/wri-datalab/cities/urban_land_use/data/global_cities_Aug2024/city_data_checked')
CITY_DATA_POINT = ee.FeatureCollection(
    'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Mar2025/guppd_v1_wUCnewcent')
# 'projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/city_data_checked'
# 'projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/city_data_checked_africa'
# 'projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/city_data_Kigali_Nairobi_Addis'
# Polygons [not used]
# CITY_DATA_POLY = ee.FeatureCollection('projects/wri-datalab/AUE/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2')
# CITY_DATA_POLY = ee.FeatureCollection('projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Mar2025/guppd_v1_poly')

# Column names from the city point data attributes
# unique city numeric id
CITY_ID_COL = 'ORIG_FID'
# city name
CITY_NAME_COL = 'CIES_NM_TL'
# city population
CITY_POP_COL = 'P_R23_2020'
# city region
CITY_REG_COL = 'GRGN_L2'

# CSV file for result and progress tracking
CITY_TRACKER = f'data/guppd_checked_cities_track_{mapYear}_guppd_v1_wUCnewcent.csv'
