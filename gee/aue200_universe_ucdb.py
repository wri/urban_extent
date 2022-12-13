import ee
import helpers as h
import data
import math
import re
from pprint import pprint
ee.Initialize()
#
# CONSTANTS
#
MIN_POP=100000
CITY_DATA_ID='projects/wri-datalab/AUE/AUEUniverseofCities'
BUILT_UP1_ID='JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1'
BUILT_UP2_ID="DLR/WSF/WSF2015/v1"
AUE_UE_ID='projects/wri-datalab/AUE/urban_edge/urban_edge_t3-v2'
UCDB_ID='projects/wri-datalab/GHSL_UCDB'

UCDB_ID_KEY='ID_HDC_G0'
INCOME_KEY='GDP15_SM'

UCDB_PROP_LIST=[ 
  'ID_HDC_G0', # id
  'GDP90_SM','GDP00_SM','GDP15_SM',  # incomes
  'GCPNT_LAT','GCPNT_LON', # lat/lon
  'CTR_MN_NM', # country
  'UC_NM_MN',  # city
  'UC_NM_LST', # city-list
  'B75','B90','B00','B15', # built-up area
  'P75','P90','P00','P15'  # population
]


#
# ASSETS
#
UCDB=ee.FeatureCollection(UCDB_ID).select(UCDB_PROP_LIST)
UE=ee.FeatureCollection(AUE_UE_ID)
CITY_DATA_FC=ee.FeatureCollection(CITY_DATA_ID).filter(ee.Filter.gte('Pop_2010',MIN_POP)).sort('Pop_2010',False)


#
# HELPERS
#
def centroid_distance(feat,point):
  centroid=ee.Feature(feat).geometry().centroid()
  point=ee.Geometry(point)
  return point.distance(centroid)

def comma_cat(c,p,is_int_str):
  p=ee.String(p)
  if is_int_str:
    c=ee.Number(c).toInt().format()    
  else:
    c=ee.String(c)
  return p.cat(',').cat(c)

def list_string(lst,is_int_str):
  lst=ee.List(lst)
  def ccat(c,p):
    return comma_cat(c,p,is_int_str)
  if is_int_str:
    first=lst.getNumber(0).toInt().format()
  else:
    first=lst.getString(0)
  return lst.slice(1).iterate(ccat,first)


#
# MAIN
#
def count_matches(feat):
  feat=ee.Feature(feat)
  geom=feat.geometry()
  point=geom.centroid()
  bounds=geom.bounds()
  fc=CITY_DATA_FC.filterBounds(bounds)
  ucdb=UCDB.filterBounds(bounds)

  fc=fc.map(lambda f: ee.Feature(f).set('distance',centroid_distance(f,point))).sort('distance')
  cities=fc.aggregate_array('City Name')
  distances=fc.aggregate_array('distance')

  ucdb=ucdb.map(lambda f: ee.Feature(f).set('distance',centroid_distance(f,point))).sort('distance')
  ucdb_cities=ucdb.aggregate_array('UC_NM_MN')
  ucdb_distances=ucdb.aggregate_array('distance')

  return feat.set({
    'match_count': fc.size(),
    'matched_cities': cities,
    'matched_distances': distances,
    'matched_feat': fc.first(),
    'ucdb_match_count': ucdb.size(),
    'ucdb_matched_cities': ucdb_cities,
    'ucdb_matched_distances': ucdb_distances,
    'ucdb_matched_feat': ucdb.first()
  })


def extract_matches(feat):
  feat=ee.Feature(feat)

  match=ee.Feature(feat.get('matched_feat'))
  ucdb_matched_feat=ee.Feature(feat.get('ucdb_matched_feat'))

  matched_distances=list_string(feat.get('matched_distances'),True)
  matched_cities=list_string(feat.get('matched_cities'),False)

  ucdb_matched_distances=list_string(feat.get('ucdb_matched_distances'),True)
  ucdb_matched_cities=list_string(feat.get('ucdb_matched_cities'),False)

  mcount=feat.getNumber('match_count')
  ucdb_mcount=feat.getNumber('ucdb_match_count')
  ue_city_name=feat.get('City Name')


  return match.set({
    'ue_city_name': ue_city_name,
    'match_count': mcount,
    'matched_distances': matched_distances,
    'matched_cities': matched_cities,
    'ucdb_match_count': ucdb_mcount,
    'ucdb_matched_distances': ucdb_matched_distances,
    'ucdb_matched_cities': ucdb_matched_cities,
    }).copyProperties(ucdb_matched_feat)


#
# RUN
#
uem=UE.map(count_matches,False).filter(
  ee.Filter.And(
    ee.Filter.gt('match_count',0),
    ee.Filter.gt('ucdb_match_count',0)))
print('MATCHED CITIES COUNT:',uem.size().getInfo())
pprint(uem.aggregate_histogram('match_count').getInfo())
pprint(uem.aggregate_histogram('ucdb_match_count').getInfo())
print()

univ_ucdb=uem.map(extract_matches)
ex=univ_ucdb.first()
pprint(ex.toDictionary().getInfo())


#
# EXPORT
#
task=ee.batch.Export.table.toAsset(
      collection=univ_ucdb, 
      description='AUE200_Universe_UCDB', 
      assetId=f'projects/wri-datalab/AUE/AUE200_Universe_UCDB')

task.start()
print('-'*100)
pprint(task.status())
