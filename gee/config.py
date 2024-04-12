import ee
ee.Initialize()

import os

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
STUDY_AREA_SCALE_FACTOR = 100
VECTOR_SCALE = None
OFFSET = None
LIMIT = 1
DRY_RUN = False
OFFSET = 0

# Set output image collection for all processed cities
#os.chdir(os.getcwd()+'/gee')
ROOT = 'data'
IC_ID = f'{ROOT}/test_chris_Apr2024/builtup_density_JRCs_50compare_L2_100'

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

USE_TESTCITIES = False # not used
USE_REGION_FILTER = False # not used
USE_COMPLETED_FILTER = True # used
USE_COM = True # used
# COM_CITIES = []

NEW_CENTER_CITIES_CENTROIDS=ee.Dictionary({
#   'Yangon': ee.Geometry.Point([96.185, 16.870]),#10248???
#   'Kishoreganj': ee.Geometry.Point([90.79, 24.43]),#9905 check
#   'Dayton': ee.Geometry.Point([-84.173, 39.706]),#702 check
#   'Lublin': ee.Geometry.Point([22.585, 51.23]),#3289 check
  'Zacatecas': ee.Geometry.Point([-102.54, 22.758]),#115 check
#   'Davenport': ee.Geometry.Point([-90.58, 41.525]),#541 check
#   'Savannah': ee.Geometry.Point([-81.11, 32.055]),#656 check
  'Makhachkala': ee.Geometry.Point([47.52, 42.964]),#5250 check COM
  'Lagos': ee.Geometry.Point([3.297, 6.6]),#2125
  })

import alternate_centroids as alt_cent

NEW_CENTER_CITIES_CENTROIDS = alt_cent.NEW_CENTER_CITIES_CENTROIDS
NEW_CENTER_CITIES_CENTROIDS_IDS = alt_cent.NEW_CENTER_CITIES_CENTROIDS_IDS

# NEW_CENTER_CITIES = NEW_CENTER_CITIES_CENTROIDS.keys()
# NEW_CENTER_CITIES_IDS = NEW_CENTER_CITIES_CENTROIDS_IDS.keys()

USE_NEW_CENTER_CITIES = False # not used for now, but may need to use in the future

PI = ee.Number.expression('Math.PI')

PPOLICY = {
    'builtup': 'mode',
    'density': 'mean',
}


# Built-up layer options
# select pixel built-up density threshold for GHSL2023release
# minimum m2 built out of possible 10000 for each GHSL grid cell included
BuiltAreaThresh = 1000
# set the built-up year for which to produce extents
mapYear = 2020
