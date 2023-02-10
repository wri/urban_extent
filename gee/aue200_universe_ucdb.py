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
# POP_SORT=True
POP_SORT=False
MIN_POP=100000
CITY_DATA_ID='projects/wri-datalab/AUE/AUEUniverseofCities'
AUE_UE_ID='projects/wri-datalab/AUE/urban_edge/urban_edge_t3-v2'
UCDB_ID='projects/wri-datalab/GHSL_UCDB'
DEST_NAME='AUE200_Universe_UCDB-NM_BNDS'


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
  ue_city_name=feat.getString('City Name')
  ue_city_name_part=ue_city_name.slice(0,5)

  search_region=bounds

  fc=CITY_DATA_FC.filterBounds(search_region)
  ucdb=UCDB.filterBounds(search_region)

  if POP_SORT:
    fc=fc.map(lambda f: ee.Feature(f).set('distance',centroid_distance(f,point))).sort('Pop_2010')
  else:
    fc=fc.map(lambda f: ee.Feature(f).set('distance',centroid_distance(f,point))).sort('distance')

  cities=fc.aggregate_array('City Name')
  distances=fc.aggregate_array('distance')
  
  fcm=fc.filter(ee.Filter.stringContains(
      'City Name',
      ue_city_name_part
    ))

  fcm=ee.Algorithms.If(
    fcm.size(),
    fcm.first(),
    fc.first()
  )


  if POP_SORT:
    ucdb=ucdb.map(lambda f: ee.Feature(f).set('distance',centroid_distance(f,point))).sort('P15')
  else:
    ucdb=ucdb.map(lambda f: ee.Feature(f).set('distance',centroid_distance(f,point))).sort('distance')
  ucdb_cities=ucdb.aggregate_array('UC_NM_MN')
  ucdb_distances=ucdb.aggregate_array('distance')
  ucdbm=ucdb.filter(ee.Filter.stringContains(
      'UC_NM_MN',
      ue_city_name_part
    ))

  ucdbm=ee.Algorithms.If(
    ucdbm.size(),
    ucdbm.first(),
    ucdb.first()
  )

  return feat.set({
    'match_count': fc.size(),
    'matched_cities': cities,
    'matched_distances': distances,
    'matched_feat': fcm,
    'ucdb_match_count': ucdb.size(),
    'ucdb_matched_cities': ucdb_cities,
    'ucdb_matched_distances': ucdb_distances,
    'ucdb_matched_feat': ucdbm
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
    'ue_area': feat.geometry().area(10),
    'ue_city_name': ue_city_name,
    'match_count': mcount,
    'matched_distances': matched_distances,
    'matched_cities': matched_cities,
    'ucdb_match_count': ucdb_mcount,
    'ucdb_matched_distances': ucdb_matched_distances,
    'ucdb_matched_cities': ucdb_matched_cities,
    }).copyProperties(ucdb_matched_feat)


# # test=UE.filter(ee.Filter.stringContains('City Name','Zhengzhou')).first()
# test=UE.filter(ee.Filter.eq('City Name','Raleigh')).first()

# out=count_matches(test)
# out2=extract_matches(out)
# pprint(out2.toDictionary().getInfo())

#
# RUN
#
uem=UE.map(count_matches,False).filter(
  ee.Filter.And(
    ee.Filter.gt('match_count',0),
    ee.Filter.gt('ucdb_match_count',0)))
print('---')
univ_ucdb=uem.map(extract_matches)
print('---')



#
# EXPORT
#
name=DEST_NAME
if POP_SORT:
  name=f'{name}-psort'
task=ee.batch.Export.table.toAsset(
      collection=univ_ucdb, 
      description=name, 
      assetId=f'projects/wri-datalab/AUE/{name}')

task.start()
print('-'*100)
pprint(task.status())
