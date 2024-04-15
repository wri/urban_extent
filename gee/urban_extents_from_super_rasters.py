import ee
import helpers as h
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
ENSURE_FEATS=False
SPLIT_INDEX=False

ENSURE_FEATS=True




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


ROOT= 'projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024' #'users/emackres'
SUFFIX= 'JRCs_50compare_L2_20_wP' #'GHSL_BUthresh10pct' #'Kigali_GHSL_GHSLthresh10pct' #'GHSL_GHSLthresh10pct' #'GHSL_GHSLthresh5pct' #'WSFevo' 'GHSL2023_2015'  'WSFevo_2015' 'GHSL_WSFunion_2015'
SR_ID=f'{ROOT}/builtup_density_{SUFFIX}'

YEAR = 2020


DEST_NAME=f'{SUFFIX}_{YEAR}'#_{REGION_SHORT}'
# DEST_NAME=f'{SUFFIX}'#_{YEAR}'



if RASTER_BUFFER:
  RASTER_BUFFER_KERNEL=ee.Kernel.euclidean(RASTER_BUFFER,'meters')
else:
  RASTER_BUFFER_KERNEL=None
#
# IMPORTS
#
SUPER_IC=ee.ImageCollection(SR_ID).filter(ee.Filter.eq('builtup_year',YEAR))#.filter(ee.Filter.eq('Reg_Name',REGION))#.filter(ee.Filter.eq('City__Name','Kigali'))#


if VECTOR_SCALE:
  TRANSFORM=None
else:
  # GHSL=ee.Image('JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1')
  # _proj=GHSL.select('built').projection().getInfo()
  # GHSL_CRS=_proj['crs']
  # GHSL2023release = ee.Image("users/emackres/GHS_BUILT_S_MT_2023_100_BUTOT_MEDIAN")
  GHSL2023release = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{YEAR}")
  _proj=GHSL2023release.projection().getInfo()
  GHSL_CRS= "EPSG:3857"
  
  GHSL_TRANSFORM=_proj['transform']
  print("GHSL PROJ:",GHSL_CRS,GHSL_TRANSFORM)
  TRANSFORM=GHSL_TRANSFORM
  VECTOR_SCALE=None




# #
# # HELPERS
# #
# def get_influence_distance(area):
#   return ee.Number(area).sqrt().multiply(GROWTH_RATE)


# def fill_small(feat):
#   return h.fill_holes(feat,MAX_FILL)


#
# MAIN
#
# def add_coord_length(feat):
#   feat=ee.Feature(feat)
#   geom=feat.geometry()
#   coord_length=geom.coordinates().size()
#   geom_type=geom.type()
#   return feat.set({
#       'coord_length': coord_length
#     })


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
  feats=h.flatten_to_polygons_and_fill_holes(feats,MAX_FILL) 
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
# count=SUPER_IC.size()
# split_pos=count.divide(2).toInt()
# limit_pos=count.subtract(LIMIT)

# if SPLIT_INDEX is not False:
#   name=f'{name}_split{SPLIT_INDEX}'
#   if SPLIT_INDEX==1:
#     SUPER_IC=SUPER_IC.limit(count.subtract(split_pos),'City__Name',False)  
#   else:
#     SUPER_IC=SUPER_IC.limit(split_pos,'City__Name',True)  


# if TEST_CITY:
#   name=f'TESTER_{TEST_CITY}'
#   SUPER_IC=SUPER_IC.filter(ee.Filter.eq('City__Name',TEST_CITY))
# else:
#   if LIMIT:
#     SUPER_IC=SUPER_IC.limit(LIMIT,'Pop_2010',False)#.filter(ee.Filter.inList('City__Name',['Shanghai, Shanghai']))
#     name=f'{name}-lim{LIMIT}'
#     # SUPER_IC=SUPER_IC.limit(limit_pos,'Pop_2010',True).sort('system:asset_size')
#     # name=f'{name}-lim{LIMIT}remainder'
#   else:
#     SUPER_IC=SUPER_IC.sort('Pop_2010')


urban_extents_fc=ee.FeatureCollection(SUPER_IC.map(urban_extent))
if ENSURE_FEATS:
  urban_extents_fc=urban_extents_fc.filter(ee.Filter.gt('nb_input_features',0))


# if VECTOR_BUFFER:
#   name=f'{name}-b{VECTOR_BUFFER}'
# if VECTOR_SCALE:
#   name=f'{name}-vs{VECTOR_SCALE}'
# if RASTER_BUFFER:
#   name=f'{name}-rb{RASTER_BUFFER}-smask'
description=re.sub('[\.\,\/]','--',name)
asset_id=f'{ROOT}/GHSL_BUthresh10pct_{name}'
print('\n'*1)
print(f'EXPORTING [{SUPER_IC.size().getInfo()}]:', asset_id)
# pprint(SUPER_IC.aggregate_array('ID_HDC_G0').getInfo())

task=ee.batch.Export.table.toAsset(
      collection=urban_extents_fc, 
      description=description, 
      assetId=asset_id)
if DRY_RUN:
  print('--dry_run')
else:
  task.start()
  print(task.status())


# post vector check
# Define function to create circle features
def check_buffer_contains(feature):
    # Create the point geometry from the latitude and longitude
    point = ee.Geometry.Point([feature.get('study_center_lon'), feature.get('study_center_lat')])
    # Create the circle buffer around the point with the specified radius
    circle = point.buffer(ee.Number(feature.get('study_radius')).add(ee.Number(feature.get('est_influence_distance'))))
    # Check if the feature geometry is completely within the circle
    geometry = feature.geometry()
    contains = circle.contains(geometry)
    # Copy all the properties from the original feature
    circle = ee.Feature(circle, feature.toDictionary())
    # Add a new property indicating whether the city passed the buffer check
    circle = circle.set('pass_buffer_check', contains)

    return circle


# Map the function over the feature collection to create circles
circleCollection = ee.FeatureCollection(asset_id).map(check_buffer_contains)
# Filter the circle collection
filteredCircleCollection = circleCollection.filter(ee.Filter.eq('pass_buffer_check', False))
alt_scale_factor_ids = filteredCircleCollection.aggregate_array('fid').getInfo()

len(alt_scale_factor_ids)
