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
VECTOR_SCALE=None
INPUT_VECTOR_SCALE=VECTOR_SCALE
LIMIT=None
DRY_RUN=False
RASTER_BUFFER=False
VECTOR_BUFFER=None
TEST_CITY=None

RASTER_BUFFER=100
# VECTOR_SCALE=100
# VECTOR_SCALE=250
# INPUT_VECTOR_SCALE=None
# OFFSET=157
# LIMIT=10
# DRY_RUN=True
# VECTOR_BUFFER=100
# VECTOR_BUFFER=500
# TEST_CITY='Tokyo'
# TEST_CITY='Berlin'



#
# CONSTANTS
#
MAX_FILL=2e6
MAX_ERR=10
GROWTH_RATE=0.0666
PI=ee.Number.expression('Math.PI')
AREA_PROPS=['rural_area','suburban_area','urban_area']
AREA_REDUCER=ee.Reducer.sum().combine(
        ee.Reducer.sum(),outputPrefix=f'suburban_area_').combine(
          ee.Reducer.sum(),outputPrefix=f'urban_area_')


ROOT='projects/wri-datalab/urban_land_use/data'
DEST_NAME=f'urban_extents/ue_WSF15_GHSL16_WC21'
if INPUT_VECTOR_SCALE:
  SR_ID=f'{ROOT}/super_extents/builtup_density_WC21-vs{INPUT_VECTOR_SCALE}'
else:
  SR_ID=f'{ROOT}/super_extents/builtup_density_WC21'


#
# IMPORTS
#
SUPER_IC=ee.ImageCollection(SR_ID)
CITY_DATA=ee.FeatureCollection('projects/wri-datalab/AUE/AUE200_Universe')
GHSL=ee.Image('JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1')
WSF=ee.ImageCollection("users/mattia80/WSF2015_v1").reduce(ee.Reducer.firstNonNull())
WSF19=ee.ImageCollection("users/mattia80/WSF2019_20211102").reduce(ee.Reducer.firstNonNull())
DW=ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").select('label').filterDate('2022-03-01','2022-11-01').mode()
WC21=ee.ImageCollection("ESA/WorldCover/v200").reduce(ee.Reducer.firstNonNull())


_proj=GHSL.select('built').projection().getInfo()
GHSL_CRS=_proj['crs']
GHSL_TRANSFORM=_proj['transform']
print("GHSL PROJ:",GHSL_CRS,GHSL_TRANSFORM)
if VECTOR_SCALE:
  TRANSFORM=None
else:
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
  bu_pixels=bu.gt(0)
  if RASTER_BUFFER:
    bu_pixels=bu_pixels.distance(RASTER_BUFFER,False).gte(0)
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
  return feat.copyProperties(im)



#
# EXPORT
#
if TEST_CITY:
  name=f'TESTER_{TEST_CITY}'
  SUPER_IC=SUPER_IC.filter(ee.Filter.eq('City__Name',TEST_CITY))
else:
  name=DEST_NAME
  if LIMIT:
    SUPER_IC=SUPER_IC.limit(LIMIT,'Pop_2010')
    name=f'{name}-lim{LIMIT}'
  else:
    SUPER_IC=SUPER_IC.sort('Pop_2010')

if VECTOR_BUFFER:
  name=f'{name}-b{VECTOR_BUFFER}'
if VECTOR_SCALE:
  name=f'{name}-vs{VECTOR_SCALE}'
if RASTER_BUFFER:
  name=f'{name}-rb{RASTER_BUFFER}'

description=re.sub('[\.\,\/]','--',name)
urban_extents_fc=ee.FeatureCollection(SUPER_IC.map(urban_extent))
print('\n'*1)
print(f'EXPORTING [{SUPER_IC.size().getInfo()}]:',f'{ROOT}/{name}')
task=ee.batch.Export.table.toAsset(
      collection=urban_extents_fc, 
      description=description, 
      assetId=f'{ROOT}/{name}')
if DRY_RUN:
  print('--dry_run')
else:
  task.start()
  print(task.status())




