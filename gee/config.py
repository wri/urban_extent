import os
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
# CONSTANTS
STUDY_AREA_SCALE_FACTOR = 20
OFFSET = None
LIMIT = None
DRY_RUN = False
OFFSET = 0

# Set output image collection for all processed cities
#os.chdir(os.getcwd()+'/gee')
ROOT='projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024'
IC_ID = f'{ROOT}/builtup_density_JRCs_50compare_L2_20_wP'

MAX_NNN_DISTANCE = 2500
MAX_ERR = 10
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

USE_COMPLETED_FILTER = True # used
USE_COM = True # used


import inspected_centroids as insp_cent

NEW_INSPECTED_CENTROIDS_IDS = insp_cent.NEW_INSPECTED_CENTROIDS_IDS
NEW_INSPECTED_CITIES_IDS = NEW_INSPECTED_CENTROIDS_IDS.keys()
USE_INSPECTED_CENTROIDS = False # not used for now, but may need to use in the future


# Built-up layer options
# select pixel built-up density threshold for GHSL2023release
# minimum m2 built out of possible 10000 for each GHSL grid cell included
BuiltAreaThresh = 1000
# set the built-up year for which to produce extents
mapYear = 2020


# New City data (13K cities)
# GRGN_L2
# linear average relationships between population and built-up area
df = pd.read_csv('GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2.csv', encoding='latin1', low_memory=False)
# Drop rows where all columns are NaN
df = df.dropna(how='all')
# Drop rows where B15 is 0
df = df[df['B15'] != 0]
# Replace value Polynesia with Melanesia in column 'GRGN_L2'
# Only one city in Polynesia
df['GRGN_L2'] = df['GRGN_L2'].replace('Polynesia', 'Melanesia')
df['GRGN_L2'].value_counts()

# TODO: move to helpers.py
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
