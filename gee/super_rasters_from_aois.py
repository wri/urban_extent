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
""""
Note on STUDY_AREA_SCALE_FACTOR:

if A=a*b=w*a^2, and w=4*alpha
R(circle) ~ alpha * sqrt(A)
ratio=A(circle)/A ~ alpha^2 * pi 

* for w = 16, ratio ~ 12
* for w = 36, ratio ~ 30

Note that city centers might be far from "centered"
"""
STUDY_AREA_SCALE_FACTOR=20
VECTOR_SCALE=100
VECTOR_SCALE=None
OFFSET=None
LIMIT=None
DRY_RUN=False
# OFFSET=100
# LIMIT=2
# DRY_RUN=True


#
# CONSTANTS
#
ROOT='projects/wri-datalab/urban_land_use/data/super_extents'
IC_ID=f'{ROOT}/builtup_density_WC21'
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
CITY_DATA=ee.FeatureCollection('projects/wri-datalab/AUE/AUE200_Universe')
AOIS=ee.FeatureCollection('projects/wri-datalab/urban_land_use/data/HandDrawnAOIs')
aoi_idents=AOIS.aggregate_array('City__ID__Number')

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
# BU IMAGE
#
BU_GHSL=GHSL.select(['built']).gte(3).selfMask().rename(['bu']).toUint8()
BU_WSF=WSF.eq(255).selfMask().rename(['bu']).toUint8()
BU_WSF19=WSF19.eq(255).selfMask().rename(['bu']).toUint8()
BU_DW=DW.eq(6).selfMask().rename(['bu']).toUint8()
BU_WC21=WC21.eq(50).selfMask().rename(['bu']).toUint8()
BU=ee.ImageCollection([
    BU_WSF,
    BU_GHSL,
    BU_WC21
    ]).reduce(ee.Reducer.firstNonNull()).rename('bu')
IS_BUILTUP=BU.gt(0).rename(['builtup'])
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
_usubu=ee.Image(0).where(_density.gte(SUBURBAN_BOUND).And(_density.lt(URBAN_BOUND)),1).where(_density.gte(URBAN_BOUND),2).rename(['builtup_class'])
_density=_density.multiply(100).rename(['density'])
BU_DENSITY_CAT=_usubu.addBands([_density,IS_BUILTUP]).toUint8()
BU_CONNECTED=IS_BUILTUP.connectedPixelCount(MINPIXS).eq(MINPIXS).selfMask()
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
CITY_DATA=CITY_DATA.filter(ee.Filter.inList('City__ID__Number',aoi_idents))



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
      crsTransform=GHSL_TRANSFORM)
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
  print_info(cname=cname)
  centroid=feat.geometry()
  bu_centroid_xy=ee.List(nearest_non_null(centroid))
  bu_centroid=ee.Geometry.Point(bu_centroid_xy)
  crs=get_crs(bu_centroid)
  region=ee.String(feat.get('Reg_Name')).trim()
  pop=feat.getNumber('Pop_2010')
  est_area=get_area(pop,region)
  est_influence_distance=get_influence_distance(est_area)
  scaled_area=est_area.multiply(STUDY_AREA_SCALE_FACTOR)
  radius=get_radius(scaled_area)
  study_bounds=centroid.buffer(radius,MAX_ERR)
  center_of_mass=ee.Geometry(get_com(study_bounds))
  study_bounds=center_of_mass.buffer(radius,MAX_ERR)
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
        'study_area_scale_factor': STUDY_AREA_SCALE_FACTOR
    }).copyProperties(feat)


def vectorize(data):
  data=ee.Feature(data)
  study_area=AOIS.filter(ee.Filter.eq('City__ID__Number',data.get('City__ID__Number')))
  study_area=ee.Feature(study_area.first()).geometry()
  bu_centroid=ee.Geometry(data.get('bu_city_center'))
  feats=BU_CONNECTED.reduceToVectors(
    reducer=ee.Reducer.countEvery(),
    crs=GHSL_CRS,
    scale=VECTOR_SCALE,
    crsTransform=TRANSFORM,
    geometry=study_area,
    maxPixels=1e11,
    bestEffort=True
  )
  centroid_filter=ee.Filter.withinDistance(
    distance=CENTROID_SEARCH_RADIUS,
    leftField='.geo',
    rightValue=bu_centroid, 
    maxError=MAX_ERR
  )
  feats=ee.FeatureCollection(feats.map(buffered_feat))
  geoms=feats.geometry(MAX_ERR).dissolve(MAX_ERR).geometries()
  feats=ee.FeatureCollection(geoms.map(geom_feat))
  feats=feats.filter(centroid_filter)
  feats=fill_polygons(feats)
  return ee.Feature(feats.geometry()).copyProperties(data).set('augmented_study_area',True)
  # feat=ee.Feature(feats.first())
  # return feat.copyProperties(data)


def get_super_feat(feat):
  feat=get_circle_data(feat)
  feat=vectorize(feat)
  return feat


#
# EXPORT
#
print(f'DEST: {IC_ID}')
CITY_DATA=CITY_DATA.sort('Pop_2010')
if OFFSET and LIMIT:
  LIMIT=LIMIT+OFFSET
IDS=CITY_DATA.aggregate_array('City__ID__Number').getInfo()[OFFSET:LIMIT]
# 
for i,ident in enumerate(IDS):
  feat=ee.Feature(CITY_DATA.filter(ee.Filter.eq('City__ID__Number',ident)).first())
  city_name=feat.getString('City__Name').getInfo()
  print('\n'*1)
  print(f'{i}: {city_name} [{ident}]')
  feat=ee.Feature(get_super_feat(feat))
  # print_info(super_feat=feat.toDictionary())
  print('='*100)
  asset_name=re.sub('[\ \.\,\/]','',f'{city_name}-{ident}')
  bu=ee.Image(BU_DENSITY_CAT.copyProperties(feat))
  geom=feat.geometry()
  task=ee.batch.Export.image.toAsset(
    image=bu,
    description=asset_name,
    assetId=f'{IC_ID}/{asset_name}',
    pyramidingPolicy=PPOLICY,
    region=geom,
    crs=GHSL_CRS,
    crsTransform=GHSL_TRANSFORM,
    maxPixels=1e11,
  )
  if DRY_RUN:
    print('-- dry_run:',asset_name)
  else:
    task.start()
    print('TASK SUBMITTED:',asset_name,task.status(),'\n')
  print('\n'*1)






