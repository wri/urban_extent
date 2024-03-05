import ee
import helpers as h
import alternate_centroids as alt_cent
import data
import math
import re
from unidecode import unidecode
from pprint import pprint
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
STUDY_AREA_SCALE_FACTOR=20
# VECTOR_SCALE=100
VECTOR_SCALE=None
OFFSET=None
LIMIT=None
DRY_RUN=False
OFFSET=0
# LIMIT=500

# DRY_RUN=True
# OFFSET=500
# LIMIT=5000

"""
 RUN 1 ERRORS:  [4189, 2292, 1500, 2062]   
"""

# DRY_RUN=True


#
# CONSTANTS
#
# Set output image collection for all processed cities
#
# ROOT='projects/wri-datalab/cities/urban_land_use/data/dev'
ROOT='projects/wri-datalab/cities/urban_land_use/data'
# IC_ID=f'{ROOT}/builtup_density_GHSL_WSF1519_WC21'
# ROOT = 'users/emackres'
# IC_ID=f'{ROOT}/builtup_density_WSFevo_2015'
# IC_ID=f'{ROOT}/builtup_density_GHSL2023_2015'
# IC_ID=f'{ROOT}/builtup_density_GHSL_WSFunion_2015'
# IC_ID=f'{ROOT}/builtup_density_GHSL_WSFintersection_2015'
# IC_ID=f'{ROOT}/builtup_density_WSFevo'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion_GHSLthresh2pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL_GHSLthresh2pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL_GHSLthresh5pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL_GHSLthresh10pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion_GHSLthresh2pct_WSFres'
# IC_ID=f'{ROOT}/builtup_density_GHSL-WSFunion_GHSLthresh2pct_GHSLres'
# IC_ID=f'{ROOT}/builtup_density_Kigali_GHSL_GHSLthresh10pct'
IC_ID=f'{ROOT}/builtup_density_non-Universe_GHSL_BUthresh10pct'
# IC_ID=f'{ROOT}/builtup_density_GHSL_BUthresh10pct'







if VECTOR_SCALE:
  IC_ID=f'{IC_ID}-vs{VECTOR_SCALE}'


HALTON_TYPE_KEY='Locale sampling (0=Halton only, 1=Halton+)'
MAX_NNN_DISTANCE=2500
MAX_ERR=10
MINPIXS=10
SUBURBAN_BOUND=0.25
URBAN_BOUND=0.5
COM_SEED=1234
NB_COM_SAMPLES=5000
GROWTH_RATE=0.0666
DENSITY_RADIUS=564
DENSITY_UNIT='meters'
CENTROID_SEARCH_RADIUS=200
USE_TESTCITIES=False
USE_REGION_FILTER=False
USE_COMPLETED_FILTER=True
USE_COM=False
# USE_COM=True
COM_CITIES=[
  # 'Bidar',
  # 'Boras',
  # 'Budaun',
  # 'Chandausi',
  # 'Godhra',
  # # 'Ingolstad', ## <=== FAILED Error: Image.clip: The geometry for image clipping must not be empty. 
  # # 'Jaranwala', ## <=== FAILED Error: Image.clip: The geometry for image clipping must not be empty. 
  # # 'Johnson City', ## <=== FAILED Error: Image.clip: The geometry for image clipping must not be empty. 
  # 'La Victoria',
  # 'Mahendranagar',
  # 'Salzgitter',
  # 'Sawai Madhopur',
  # 'Tadepalligudem',
  # 'Tando Adam',
  # # 'Thunder Bay',
  # 'Yeosu'
  ]

NEW_CENTER_CITIES_CENTROIDS=alt_cent.NEW_CENTER_CITIES_CENTROIDS
NEW_CENTER_CITIES_CENTROIDS_IDS=alt_cent.NEW_CENTER_CITIES_CENTROIDS_IDS

NEW_CENTER_CITIES=NEW_CENTER_CITIES_CENTROIDS.keys()
NEW_CENTER_CITIES_IDS=NEW_CENTER_CITIES_CENTROIDS_IDS.keys()

USE_NEW_CENTER_CITIES=False

test_cities=[
  # "Dhaka",
  # "Hong Kong, Hong Kong",
  # "Wuhan, Hubei", 
  # "Bangkok",
  # "Cairo",
  # "Minneapolis-St. Paul", 
  # "Baku", 
  # "Bogota", 
  # "Kinshasa", 
  # "Madrid",
  # "Shanghai, Shanghai",
  # "New York-Newark",
  "Kigali",
]

PI=ee.Number.expression('Math.PI')

PPOLICY={
  'builtup': 'mode',
  'density': 'mean',
}

FIT_PARAMS=ee.Dictionary({
    'East Asia and the Pacific (EAP)':
        {'intercept': 6.844359028945421,
         'offset': 1.791926332415592,
         'score': 0.7375592105175173,
         'slope': 0.9005954865250072},
    'Europe and Japan (E&J)':
        {'intercept': 8.69494278584463,
         'offset': 1.3765398939200644,
         'score': 0.8282268575495757,
         'slope': 0.7909946578460973},
    'Land-Rich Developed Countries (LRDC)':
        {'intercept': 8.815887085043352,
         'offset': 0.7586211992962966,
         'score': 0.8838364233047373,
         'slope': 0.8478077958637914},
    'Latin America and the Caribbean (LAC)':
        {'intercept': 7.304395215265931,
         'offset': 0.6775184545295296,
         'score': 0.9053339438612787,
         'slope': 0.8450702344066737},
    'South and Central Asia (SCA)':
        {'intercept': 7.749750012982069,
         'offset': 1.8054134632856353,
         'score': 0.7487748140929972,
         'slope': 0.7759435551490513},
    'Southeast Asia (SEA)':
        {'intercept': 6.82616432868558,
         'offset': 0.9686848696989969,
         'score': 0.8143299893665737,
         'slope': 0.8944201392252237},
    'Sub-Saharan Africa (SSA)':
        {'intercept': 7.406971326898002,
         'offset': 0.9996327596950607,
         'score': 0.765974222675155,
         'slope': 0.8380261492251289},
    'Western Asia and North Africa (WANA)':
        {'intercept': 6.781561303548658,
         'offset': 0.6353709001657144,
         'score': 0.9426792637978123,
         'slope': 0.877341649095773}
})


#
# IMPORTS
#
# City centroids
# CITY_DATA=ee.FeatureCollection('projects/wri-datalab/AUE/AUE200_Universe')
# CITY_DATA=ee.FeatureCollection('projects/wri-datalab/AUE/AUEUniverseofCities')
# CITY_DATA=ee.FeatureCollection('projects/wri-datalab/AUE/AUEUniverseofCities-updatedcentroidsSept2023')
CITY_DATA=ee.FeatureCollection(alt_cent.NON_UNIVERSE_CITIES)


# Built-up layer options
GHSL=ee.Image('JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1')
WSF=ee.ImageCollection("users/mattia80/WSF2015_v1").reduce(ee.Reducer.firstNonNull())
WC21=ee.ImageCollection("ESA/WorldCover/v200").reduce(ee.Reducer.firstNonNull())
WSF19=ee.ImageCollection("users/mattia80/WSF2019_20211102").reduce(ee.Reducer.firstNonNull())
# DW=ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").select('label').filterDate('2022-03-01','2022-11-01').mode()

# https://gee-community-catalog.org/projects/wsf/
wsf_evo = ee.ImageCollection("projects/sat-io/open-datasets/WSF/WSF_EVO")
wsf_evoImg = wsf_evo.reduce(ee.Reducer.firstNonNull()).selfMask().rename(['bu'])

GHSL2023release = ee.Image("users/emackres/GHS_BUILT_S_MT_2023_100_BUTOT_MEDIAN")
# Map.addLayer(GHSL2023release.gte(500).reduce(ee.Reducer.anyNonZero()).selfMask(),{palette:['red','blue']},"GHSLraw",false)
# b1: 1950, b2: 1955, b3: 1960, b4: 1965, b5: 1970, b6: 1975, b7: 1980, b8: 1985, b9: 1990, b10: 1995, b11: 2000, b12: 2005, b13: 2010, b14: 2015, b15: 2020, b16: 2025, b17: 2030)
# count = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
count = [17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1]
year = [1950,1955,1960,1965,1970,1975,1980,1985,1990,1995,2000,2005,2010,2015,2020,2025,2030]
# select pixel built-up density threshold for GHSL2023release
BuiltAreaThresh = 1000 # minimum m2 built out of possible 10000 for each GHSL grid cell included
GHSL2023releaseYear = GHSL2023release.gte(BuiltAreaThresh).selfMask().reduce(ee.Reducer.count()).remap(count,year).selfMask().rename(['bu']) 

# set the built-up year for which to produce extents
mapYear = 1980

# input options for built-up layers
wsfyear = wsf_evoImg.updateMask(wsf_evoImg.lte(mapYear)).gt(0)
GHSLyear = GHSL2023releaseYear.updateMask(GHSL2023releaseYear.lte(mapYear)).gt(0)
GHSL_WSFcomb = wsfyear.unmask().gt(0).add(GHSLyear.unmask().gt(0)).selfMask()
GHSL_WSFintersect = GHSL_WSFcomb.updateMask(GHSL_WSFcomb.eq(2)).gt(0)
GHSL_WSFunion = GHSL_WSFcomb.updateMask(GHSL_WSFcomb.gte(1)).gt(0)

# obtain projection, CRS and Transform for input layer
# _proj=GHSL.select('built').projection().getInfo()
_proj=GHSL2023release.projection().getInfo()
# _proj=wsf_evo.first().projection().getInfo()

# GHSL_CRS=_proj['crs']
GHSL_CRS= "EPSG:3857" #"ESRI:54009" # for use with GHSL2023release image which doesn't have CRS in metadata. 
GHSL_TRANSFORM=_proj['transform']
print("GHSL PROJ:",GHSL_CRS,GHSL_TRANSFORM)


if VECTOR_SCALE:
  TRANSFORM=None
else:
  TRANSFORM=GHSL_TRANSFORM
  VECTOR_SCALE=None
#
# Select built-up IMAGE
#
# BU_GHSL=GHSL.select(['built']).gte(3).selfMask().rename(['bu']).toUint8()
# BU_WSF=WSF.eq(255).selfMask().rename(['bu']).toUint8()
# BU_WC21=WC21.eq(50).selfMask().rename(['bu']).toUint8()
# BU_WSF19=WSF19.eq(255).selfMask().rename(['bu']).toUint8()
# # BU_DW=DW.eq(6).selfMask().rename(['bu']).toUint8()
# BU=ee.ImageCollection([
#     BU_WSF,
#     BU_GHSL,
#     BU_WC21,
#     BU_WSF19
#     ]).reduce(ee.Reducer.firstNonNull()).rename('bu')
BU = GHSLyear

# create band ("builtup") with binary builtup value
IS_BUILTUP=BU.gt(0).rename(['builtup'])

# create band ("density") with the percent of pixels that are built-up within radius of each pixel
_usubu_rededucer=ee.Reducer.mean()
_usubu_kernel=ee.Kernel.circle(
  radius=DENSITY_RADIUS, 
  units=DENSITY_UNIT, 
  normalize=True,
  magnitude=1
)
_density=IS_BUILTUP.unmask(0).reduceNeighborhood(
  reducer=_usubu_rededucer,
  kernel=_usubu_kernel,
  skipMasked=True,
)
# create band ("builtup_class") with built-up classification (urban, suburban, rural) for each built-up pixel based on its "density" value
_usubu=ee.Image(0).where(_density.gte(SUBURBAN_BOUND).And(_density.lt(URBAN_BOUND)),1).where(_density.gte(URBAN_BOUND),2).rename(['builtup_class'])
_density=_density.multiply(100).rename(['density'])
BU_DENSITY_CAT=_usubu.addBands([_density,IS_BUILTUP]).toUint8()
# create image of all urban or suburban builtup pixels that have at least MINPIXS neighbors that are also urban or suburban builtup pixels
BU_CONNECTED=IS_BUILTUP.multiply(_usubu.gt(0)).selfMask().connectedPixelCount(MINPIXS).eq(MINPIXS).selfMask()
BU_LATLON=BU_CONNECTED.addBands(ee.Image.pixelLonLat())


#
# UTILS
#
def get_info(**kwargs):
  return ee.Dictionary(kwargs).getInfo()


def print_info(**kwargs):
  print(get_info(**kwargs))


def safe_keys(name):
  return ee.String(name).replace(' ','__','g').replace('#','NB','g')


#
# DATA PREP
#
prop_names=CITY_DATA.first().propertyNames()
prop_names=prop_names.remove(HALTON_TYPE_KEY)
safe_prop_names=prop_names.map(safe_keys)
CITY_DATA=CITY_DATA.select(prop_names,safe_prop_names)

# filter options to select subsets of cities
COM_FILTER=ee.Filter.inList('City__Name',COM_CITIES)
if USE_COM:
  CITY_DATA=CITY_DATA.filter(COM_FILTER)
else:
  CITY_DATA=CITY_DATA.filter(COM_FILTER.Not())

TESTCITIES_FILTER=ee.Filter.inList('City__Name',test_cities)
if USE_TESTCITIES:
  CITY_DATA=CITY_DATA.filter(TESTCITIES_FILTER)
else:
  CITY_DATA=CITY_DATA

REGION_FILTER=ee.Filter.eq('Reg_Name','East Asia and the Pacific (EAP)') # 'Land-Rich Developed Countries (LRDC)'
if USE_REGION_FILTER:
  CITY_DATA=CITY_DATA.filter(REGION_FILTER)
else:
  CITY_DATA=CITY_DATA

NCC_FILTER=ee.Filter.inList('City__Name',NEW_CENTER_CITIES)
def toInt(StringInt):
    return ee.Number.parse(StringInt)
NCC_ID_FILTER=ee.Filter.inList('City__ID__Number',NEW_CENTER_CITIES_IDS.map(toInt))
COMB_NCC_FILTER=ee.Filter.Or(NCC_FILTER,NCC_ID_FILTER)
if USE_NEW_CENTER_CITIES:
  CITY_DATA=CITY_DATA.filter(COMB_NCC_FILTER)
else:
  CITY_DATA=CITY_DATA#.filter(COMB_NCC_FILTER.Not())

if LIMIT:
  CITY_DATA=CITY_DATA.limit(LIMIT,'Pop_2010',False)#.filter(ee.Filter.inList('City__Name',['Yingtan, Jiangxi']))
else:
  CITY_DATA=CITY_DATA

# filter to limit cities to be run to those not already in the output ImageCollection. 
COMPLETED_IDS=ee.ImageCollection(IC_ID).aggregate_array('City__ID__Number')
COMPLETED_FILTER=ee.Filter.And(ee.Filter.inList('City__ID__Number',COMPLETED_IDS),ee.Filter.equals('builtup_year',mapYear))
COMPLETED_CITIES_LIST=ee.ImageCollection(IC_ID).filter(COMPLETED_FILTER).aggregate_array('City__ID__Number')

if USE_COMPLETED_FILTER:
  CITY_DATA=CITY_DATA.filter(ee.Filter.inList('City__ID__Number',COMPLETED_CITIES_LIST).Not())
else:
  CITY_DATA=CITY_DATA

pprint(CITY_DATA.aggregate_array('City__Name').getInfo())
pprint(CITY_DATA.aggregate_array('Reg_Name').getInfo())
pprint(CITY_DATA.aggregate_array('City__ID__Number').getInfo())

# raise

#
# HELPERS
#
def get_area(pop,region):
    pop=ee.Number(pop).log()
    params=ee.Dictionary(FIT_PARAMS.get(region))
    slope=params.getNumber('slope')
    intercept=params.getNumber('intercept')
    log_area=slope.multiply(pop).add(intercept)
    return log_area.exp()


def get_radius(area):
  return ee.Number(area).divide(PI).sqrt()


def nearest_non_null(centroid):
    distance_im=ee.FeatureCollection([centroid]).distance(MAX_NNN_DISTANCE)
    bounds=ee.Geometry.Point(centroid.coordinates()).buffer(MAX_NNN_DISTANCE,MAX_ERR)
    nearest=distance_im.addBands(ee.Image.pixelLonLat()).updateMask(BU).reduceRegion(
      reducer=ee.Reducer.min(3),
      geometry=bounds,
      crs=GHSL_CRS,
      crsTransform=GHSL_TRANSFORM
      )
    return [nearest.getNumber('min1'), nearest.getNumber('min2')]


def get_com(geom):
  pts=BU_LATLON.sample(
    region=geom,
    scale=10,
    numPixels=NB_COM_SAMPLES,
    seed=COM_SEED,
    dropNulls=True,
    geometries=False
  )
  return ee.Algorithms.If(
    pts.size(),
    ee.Geometry.Point([
      pts.aggregate_mean('longitude'),
      pts.aggregate_mean('latitude')]),
    geom.centroid(10)
  )


def get_crs(point):
  coords=point.coordinates()
  lon=ee.Number(coords.get(0))
  lat=ee.Number(coords.get(1))
  zone=ee.Number(32700).subtract((lat.add(45).divide(90)).round().multiply(100)).add(((lon.add(183)).divide(6)).round())
  zone=zone.toInt().format()
  return ee.String('EPSG:').cat(zone)


def get_influence_distance(area):
  return ee.Number(area).sqrt().multiply(GROWTH_RATE)


def polygon_feat_boundry(feat):
  feat=ee.Feature(feat)
  geom=ee.Geometry.Polygon(feat.geometry().coordinates().get(0))
  return ee.Feature(geom)

 
def set_geom_type(feat):
  feat=ee.Feature(feat)
  return feat.set('geomType',feat.geometry().type()) 


def geom_feat(g):
  return ee.Feature(ee.Geometry(g))


def coords_feat(coords):
  return ee.Feature(ee.Geometry.Polygon(coords))


def flatten_geometry_collection(feat):
  feat=ee.Feature(feat)
  geoms=feat.geometry().geometries()
  return ee.FeatureCollection(geoms.map(geom_feat))


def flatten_multipolygon(feat):
  coords_list=ee.Feature(feat).geometry().coordinates()  
  return ee.FeatureCollection(coords_list.map(coords_feat))


def fill_polygons(feats):
  feats=feats.map(set_geom_type)
  gc_filter=ee.Filter.eq('geomType', 'GeometryCollection')
  mpoly_filter=ee.Filter.eq('geomType', 'MultiPolygon')
  poly_filter=ee.Filter.eq('geomType', 'Polygon')
  gc_data=feats.filter(gc_filter).map(flatten_geometry_collection).flatten()
  mpoly_data=feats.filter(mpoly_filter).map(flatten_multipolygon).flatten()
  poly_data=feats.filter(poly_filter)
  feats=ee.FeatureCollection([
      poly_data,
      gc_data,
      mpoly_data]).flatten()
  feats=feats.map(set_geom_type).filter(poly_filter)
  feats=feats.map(polygon_feat_boundry)
  return feats

  
def buffered_feat(feat):
  feat=ee.Feature(feat)
  area=feat.area(MAX_ERR)
  return buffered_feat_area(feat,area)


def buffered_feat_area(feat,area):
  feat=ee.Feature(feat)
  area=ee.Number(area)
  infl=get_influence_distance(area)
  return feat.buffer(infl,MAX_ERR).set('buffer',infl)



#
# MAIN
#
def get_circle_data(feat):
  feat=ee.Feature(feat)
  cname=feat.get('City__Name')
  cID=feat.get('City__ID__Number')
  centroid=feat.geometry()
  crs=get_crs(centroid)
  region=ee.String(feat.get('Reg_Name')).trim()
  pop=feat.getNumber('Pop_2010')
  est_area=get_area(pop,region)
  est_influence_distance=get_influence_distance(est_area)
  scaled_area=est_area.multiply(STUDY_AREA_SCALE_FACTOR)
  radius=get_radius(scaled_area)
  study_bounds=centroid.buffer(radius,MAX_ERR)
  center_of_mass=ee.Geometry(get_com(study_bounds))
  study_bounds=center_of_mass.buffer(radius,MAX_ERR)
  if USE_COM:
    bu_centroid_xy=ee.List(nearest_non_null(center_of_mass))
    _use_inspected_centroid=False
  elif USE_NEW_CENTER_CITIES:
    print('ncc',cname.getInfo())
    v = NEW_CENTER_CITIES_CENTROIDS.get(cname,"NA").getInfo()
    if v == "NA":
      inspected_centroid=NEW_CENTER_CITIES_CENTROIDS_IDS.get(ee.Number(cID).format())
    else:
      inspected_centroid=NEW_CENTER_CITIES_CENTROIDS.get(cname)
    inspected_centroid=ee.Geometry(inspected_centroid)
    bu_centroid_xy=ee.List(nearest_non_null(inspected_centroid))
    # print(bu_centroid_xy.getInfo())
    _use_inspected_centroid=True
  else:
    bu_centroid_xy=ee.List(nearest_non_null(centroid))    
    _use_inspected_centroid=False
  bu_centroid=ee.Geometry.Point(bu_centroid_xy)
  return ee.Feature(
      study_bounds,
      {
        'city_center': centroid,
        'bu_city_center': bu_centroid,
        'crs': crs,
        'center_of_mass': center_of_mass,
        'est_area': est_area,
        'scaled_area': scaled_area,
        'study_radius': radius,
        'est_influence_distance': est_influence_distance,
        'study_area_scale_factor': STUDY_AREA_SCALE_FACTOR,
        'use_center_of_mass': USE_COM,
        'use_inspected_centroid': _use_inspected_centroid,
        'builtup_year': mapYear
    }).copyProperties(feat)


def vectorize(data):
  data=ee.Feature(data)
  study_area=data.geometry()
  bu_centroid=ee.Geometry(data.get('bu_city_center'))
  # create vectors from BU_CONNECTED image where it overlaps with city study_area
  feats=BU_CONNECTED.reduceToVectors(
    reducer=ee.Reducer.countEvery(),
    crs=GHSL_CRS,
    scale=VECTOR_SCALE,
    crsTransform=TRANSFORM,
    geometry=study_area,
    maxPixels=1e13,
    bestEffort=True
  )
  centroid_filter=ee.Filter.withinDistance(
    distance=CENTROID_SEARCH_RADIUS,
    leftField='.geo',
    rightValue=bu_centroid, 
    maxError=MAX_ERR
  )
  # buffer each vector feature by its influence distance (function of its area)
  feats=ee.FeatureCollection(feats.map(buffered_feat))
  # dissolve all vectors to merge overlapping influence area features
  geoms=feats.geometry(MAX_ERR).dissolve(MAX_ERR).geometries()
  feats=ee.FeatureCollection(geoms.map(geom_feat))
  # filter to retain only merged vector features that are within CENTROID_SEARCH_RADIUS of bu_centroid 
  feats=feats.filter(centroid_filter)
  # fill holes in vector polygons
  feats=fill_polygons(feats)
  # return vector polygons as a single feature
  return ee.Feature(feats.geometry()).copyProperties(data)


def get_super_feat(feat):
  feat=get_circle_data(feat)
  feat=vectorize(feat)
  return feat


#
# EXPORT
#
# FILTER CITIES HACK
#
# CITIES=[
#   'Dubai',
# ]
# CITY_DATA=CITY_DATA.filter(ee.Filter.inList('City__Name',CITIES))
# print(CITY_DATA.size().getInfo())


pprint(CITY_DATA.sort('City__Name').aggregate_array('City__Name').getInfo())
# print('--')


# FAILED_IDS=[
#     # 1126,
#     # 1057,
#     # 2701,
#     2516,#-
#     # 1750,
#     # 4467,
#     2431,#-
#     # 2600,
#     # 2063,
#     # 2728,
#     # 1241,
#     # 5156,
#     # 5013,
#     # 1012,
#     # 5146,
#     # 1111,
#     # 5047,
#     # 2464,
#     4765,#-
#     # 4618
# ]
# CITY_DATA=CITY_DATA.filter(ee.Filter.inList('City__ID__Number',FAILED_IDS))
# pprint(CITY_DATA.sort('City__Name').aggregate_array('City__Name').getInfo())
# print('--')
# raise


print(f'DEST: {IC_ID}')
# CITY_DATA=CITY_DATA.sort('Pop_2010')
CITY_DATA=CITY_DATA.sort('Pop_2010',False)
if OFFSET and LIMIT:
  LIMIT=LIMIT+OFFSET
IDS=CITY_DATA.aggregate_array('City__ID__Number').getInfo()[OFFSET:LIMIT]
FAILURES=[]
# 
for i,ident in enumerate(IDS):
  # get on city centroid feature 
  feat=ee.Feature(CITY_DATA.filter(ee.Filter.eq('City__ID__Number',ident)).first())
  city_name=feat.getString('City__Name').getInfo()
  print('\n'*1)
  print(f'{i}: {city_name} [{ident}]')
  # get feature for city boundary as defined by vectorize function
  feat=ee.Feature(get_super_feat(feat))
  # print_info(super_feat=feat.toDictionary())
  print('='*100)
  asset_name=unidecode(f'{city_name}-{ident}-{mapYear}')
  asset_name=re.sub(r'[^A-Za-z0-9\-\_]+', '', asset_name)
  bu=ee.Image(BU_DENSITY_CAT.copyProperties(feat))
  geom=feat.geometry()
  # Export image to output ImageCollection with 3 builtup information bands for area within the city boundary 
  task=ee.batch.Export.image.toAsset(
    image=bu,
    description=asset_name,
    assetId=f'{IC_ID}/{asset_name}',
    pyramidingPolicy=PPOLICY,
    region=geom,
    scale=VECTOR_SCALE, 
    crs=GHSL_CRS,
    crsTransform=GHSL_TRANSFORM,
    maxPixels=1e13, #1e11
  )
  if DRY_RUN:
    print('-- dry_run:',asset_name)
  else:
    try:
      task.start()
      print('TASK SUBMITTED:',asset_name,task.status(),'\n')
    except Exception as e:
      print('\n'*2)
      print('*'*100)
      print('*'*100)
      print('\n'*1)
      print(f'CITY_NAME: {city_name}')
      print(f'CITY_ID: {ident}')
      print(f'ASSET_NAME: {asset_name}')
      print(f'ERROR: {e}')
      print('\n'*1)
      print('*'*100)
      print('*'*100)
      print('\n'*2)
      FAILURES.append(ident)
  print('\n'*1)
else:
  print('-')


print('COMPLETE')
print('NB_ERRORS:',len(FAILURES))
print(FAILURES)



