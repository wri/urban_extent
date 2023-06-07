import ee
import helpers as h
import data
import math
import re
from pprint import pprint
ee.Initialize()
#
# CONFIG
#
REGION_INDEX=2

VECTOR_SCALE=None
INPUT_VECTOR_SCALE=VECTOR_SCALE
LIMIT=None
DRY_RUN=False
RASTER_BUFFER=False
VECTOR_BUFFER=None
TEST_CITY=None
ENSURE_FEATS=False
SPLIT_INDEX=False

ENSURE_FEATS=True
# RASTER_BUFFER=100
# VECTOR_SCALE=100
# VECTOR_SCALE=250
# INPUT_VECTOR_SCALE=None
# OFFSET=157
LIMIT=20
# DRY_RUN=True
# VECTOR_BUFFER=100
# VECTOR_BUFFER=500
# TEST_CITY='Tokyo'
# TEST_CITY='Berlin'

# SPLIT_INDEX=1



#
# CONSTANTS
#
REGIONS=[
  'East Asia and the Pacific (EAP)',    # 0
  'Europe and Japan (E&J)',   # 1
  'Land-Rich Developed Countries (LRDC)',   # 2
  'Latin America and the Caribbean (LAC)',   # 3
  'South and Central Asia (SCA)',   # 4
  'Southeast Asia (SEA)', # 5
  'Sub-Saharan Africa (SSA)',   # 6
  'Western Asia and North Africa (WANA)'   # 7
]
REGIONS_SHORT=[
  'EastAsiaPacific',
  'EuropeJapan',
  'LandRichDevelopedCountries',
  'LatinAmericaCaribbean',
  'SouthCentralAsia',
  'SoutheastAsia',
  'SubSaharanAfrica',
  'WesternAsiaNorthAfrica'
]

MAX_FILL=2e6
MAX_ERR=10
GROWTH_RATE=0.0666
PI=ee.Number.expression('Math.PI')
AREA_PROPS=['rural_area','suburban_area','urban_area']
AREA_REDUCER=ee.Reducer.sum().combine(
        ee.Reducer.sum(),outputPrefix=f'suburban_area_').combine(
          ee.Reducer.sum(),outputPrefix=f'urban_area_')


ROOT='users/emackres'
SUFFIX='WSFevo' # 'GHSL2023_2015'  'WSFevo_2015' 'GHSL_WSFunion_2015'
SR_ID=f'{ROOT}/builtup_density_{SUFFIX}'

YEAR = 2015

REGION=REGIONS[REGION_INDEX]
REGION_SHORT=REGIONS_SHORT[REGION_INDEX]
DEST_NAME=f'{REGION_SHORT}_{SUFFIX}_{YEAR}'
DEST_NAME=f'{SUFFIX}_{YEAR}_ShanghaiOnly'



if RASTER_BUFFER:
  RASTER_BUFFER_KERNEL=ee.Kernel.euclidean(RASTER_BUFFER,'meters')
else:
  RASTER_BUFFER_KERNEL=None
#
# IMPORTS
#
SUPER_IC=ee.ImageCollection(SR_ID)#.filter(ee.Filter.eq('builtup_year',YEAR))#.filter(ee.Filter.eq('Reg_Name',REGION))
print(DEST_NAME,REGION,REGION_SHORT,SUPER_IC.size().getInfo())


if VECTOR_SCALE:
  TRANSFORM=None
else:
  GHSL=ee.Image('JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1')
  _proj=GHSL.select('built').projection().getInfo()
  GHSL_CRS=_proj['crs']
  GHSL_TRANSFORM=_proj['transform']
  print("GHSL PROJ:",GHSL_CRS,GHSL_TRANSFORM)
  TRANSFORM=GHSL_TRANSFORM
  VECTOR_SCALE=None


#
# UTILS
#
def get_info(**kwargs):
  return ee.Dictionary(kwargs).getInfo()


def print_info(**kwargs):
  pprint(get_info(**kwargs))


def safe_keys(name):
  return ee.String(name).replace(' ','__','g').replace('#','NB','g')


#
# HELPERS
#
def get_influence_distance(area):
  return ee.Number(area).sqrt().multiply(GROWTH_RATE)


def fill_small(feat):
  return h.fill_holes(feat,MAX_FILL)


#
# MAIN
#
def add_coord_length(feat):
  feat=ee.Feature(feat)
  geom=feat.geometry()
  coord_length=geom.coordinates().size()
  geom_type=geom.type()
  return feat.set({
      'coord_length': coord_length
    })


def urban_extent(im):
  im=ee.Image(im)
  bu=im.select('builtup')
  bu_class=im.select('builtup_class')
  pa=ee.Image.pixelArea()
  bu_pixels=bu_class.gt(0).multiply(bu).selfMask()
  if RASTER_BUFFER:
    bu_pixels=bu_pixels.distance(
      kernel=RASTER_BUFFER_KERNEL,
      skipMasked=False).gte(0)
  pa=bu_pixels.selfMask().addBands([
      pa.multiply(bu_class.eq(0)),
      pa.multiply(bu_class.eq(1)),
      pa.multiply(bu_class.eq(2))
  ]).rename(['label']+AREA_PROPS)
  feats=pa.reduceToVectors(
    reducer=ee.Reducer.sum(),
    crs=GHSL_CRS, 
    scale=VECTOR_SCALE,
    crsTransform=TRANSFORM,
    maxPixels=1e11,
    bestEffort=True
  )
  feats=feats.filter(ee.Filter.gt('urban_area',0))
  data=feats.reduceColumns(
    reducer=AREA_REDUCER,
    selectors=AREA_PROPS
  )
  data=data.rename(['sum','suburban_area_sum','urban_area_sum'],AREA_PROPS)
  feats=h.flatten_to_polygons(feats)
  feats=feats.map(add_coord_length)
  flat_feats=feats.filter(ee.Filter.eq('coord_length',1))
  complex_feats=feats.filter(ee.Filter.gt('coord_length',1))
  complex_feats=complex_feats.map(fill_small)
  feats=ee.FeatureCollection([
    flat_feats,
    complex_feats
  ]).flatten()    
  feat=ee.Feature(feats.geometry(MAX_ERR),data)
  if VECTOR_BUFFER:
    feat=feat.buffer(VECTOR_BUFFER,MAX_ERR)
  if ENSURE_FEATS:
    feat=feat.set('nb_input_features',feats.size())
  return feat.copyProperties(im)



#
# EXPORT
#
name=DEST_NAME
count=SUPER_IC.size()
split_pos=count.divide(2).toInt()
limit_pos=count.subtract(LIMIT)

if SPLIT_INDEX is not False:
  name=f'{name}_split{SPLIT_INDEX}'
  if SPLIT_INDEX==1:
    SUPER_IC=SUPER_IC.limit(count.subtract(split_pos),'City__Name',False)  
  else:
    SUPER_IC=SUPER_IC.limit(split_pos,'City__Name',True)  


if TEST_CITY:
  name=f'TESTER_{TEST_CITY}'
  SUPER_IC=SUPER_IC.filter(ee.Filter.eq('City__Name',TEST_CITY))
else:
  if LIMIT:
    SUPER_IC=SUPER_IC.limit(LIMIT,'Pop_2010',False).filter(ee.Filter.inList('City__Name',['Shanghai, Shanghai']))
    name=f'{name}-lim{LIMIT}'
    # SUPER_IC=SUPER_IC.limit(limit_pos,'Pop_2010',True).sort('system:asset_size')
    # name=f'{name}-lim{LIMIT}remainder'
  else:
    SUPER_IC=SUPER_IC.sort('Pop_2010')


urban_extents_fc=ee.FeatureCollection(SUPER_IC.map(urban_extent))
if ENSURE_FEATS:
  urban_extents_fc=urban_extents_fc.filter(ee.Filter.gt('nb_input_features',0))


if VECTOR_BUFFER:
  name=f'{name}-b{VECTOR_BUFFER}'
if VECTOR_SCALE:
  name=f'{name}-vs{VECTOR_SCALE}'
if RASTER_BUFFER:
  name=f'{name}-rb{RASTER_BUFFER}-smask'
description=re.sub('[\.\,\/]','--',name)
asset_id=f'{ROOT}/urban_extents/{name}'
print('\n'*1)
print(f'EXPORTING [{SUPER_IC.size().getInfo()}]:',asset_id)
pprint(SUPER_IC.aggregate_array('City__Name').getInfo())

task=ee.batch.Export.table.toAsset(
      collection=urban_extents_fc, 
      description=description, 
      assetId=asset_id)
if DRY_RUN:
  print('--dry_run')
else:
  task.start()
  print(task.status())




