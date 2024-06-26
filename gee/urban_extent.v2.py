import ee
import helpers as h
import data
import math
ee.Initialize()


BS=10
N=0
BU_TYPE='joint'
BU_TYPE='wsl'
BU_TYPE='ghsl'
#
# CONSTANTS
#
MAX_AREA=2e6
MAX_NNN_DISTANCE=1000
KM_RADIUS=80
MINBUFF=1000
CITY_CENTROIDS_ID='projects/wri-datalab/AUE/city_data-2010pop100k'


MAX_INFLUENCE_DISTANCE=2000
MIN_INFLUENCE_DISTANCE=100

"""
A=p * r^2
p * (r+D)^2 = p * r^2 * a
r+D=r * sqrt(a)
D = (sqrt(a)-1) * r
  = (sqrt(a)-1) * sqrt(A/p)
  = sqrt(A) * (sqrt(a)-1)/sqrt(p) === sqrt(A) * M


a=1.25
M=0.118/sqrt(p)

==> p=PI: M=0.06659354695
==> p=4:  M=0.05901699437
"""

GROWTH_RATE=0.1
GREEN_ZONE=100
MAX_ERROR=1
MAX_BUFFER_ERROR=10

# dw=ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
# not_water=dw.select(['label']).filterDate('2018-01-01','2018-07-01').reduce(ee.Reducer.mode()).neq(0)
inlandwater=ee.ImageCollection("GLCF/GLS_WATER").reduce(ee.Reducer.firstNonNull())
not_water=inlandwater.neq(2)


#
# ASSETS
#
cities=ee.FeatureCollection(CITY_CENTROIDS_ID).sort('City Name')
ALL_NAMES=cities.toList(6000).map(lambda c: ee.Feature(c).get('City Name')).getInfo()
print('NAME COUNT:',len(ALL_NAMES))
MATCHED_NAMES=[n for n in data.AUE_CITIES if n in ALL_NAMES]
print('MATCHED COUNT:',len(MATCHED_NAMES))
CITY_NAMES=MATCHED_NAMES[N*BS:(N+1)*BS]
print(N*BS,(N+1)*BS,CITY_NAMES)


BUILT_UP_ID1='JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1'
builtup_im1=ee.Image(BUILT_UP_ID1)
bu1=builtup_im1.select(['built']).gte(3).selfMask()

BUILT_UP_ID2="DLR/WSF/WSF2015/v1"
builtup_im2=ee.Image(BUILT_UP_ID2)
bu2=builtup_im2.eq(255).selfMask()

if BU_TYPE=='ghsl':
  SCALE=38
  bu=bu1.selfMask().toInt().rename('bu')
elif BU_TYPE=='wsl':
  SCALE=10
  bu=bu2.selfMask().toInt().rename('bu')
else:
  SCALE=10
  bu=ee.ImageCollection([
    bu1.selfMask().toInt().rename('bu'),
    bu2.selfMask().toInt().rename('bu')
  ]).reduce(ee.Reducer.firstNonNull())

asset_name=f'ue-v2_{BU_TYPE}-water_msk_r{KM_RADIUS}_s{SCALE}_n{BS}-{N+1}'
print('DEST:',asset_name)
#
# HELPERS
#
def nearest_non_null(centroid,im,max_distance=MAX_NNN_DISTANCE,scale=SCALE):
    scale=scale or im.projection().nominalScale()
    distance_im=ee.FeatureCollection([centroid]).distance(max_distance)
    nearest=distance_im.addBands(ee.Image.pixelLonLat()).updateMask(im).reduceRegion(
      reducer=ee.Reducer.min(3), 
      geometry=centroid.buffer(max_distance,MAX_BUFFER_ERROR), 
      scale=scale
    )
    return ee.Geometry.Point([nearest.getNumber('min1'), nearest.getNumber('min2')])


def fill_small(feat):
    feat=ee.Feature(feat)
    return h.fill_holes(feat,MAX_AREA)


def geom_contains_pixels(geom,im):
  return im.rename(['count']).reduceRegion(
    reducer=ee.Reducer.count(),
    geometry=ee.Geometry(geom),
    scale=SCALE
  ).getNumber('count').gt(0)


def get_influence_distance(geom):
  d=ee.Geometry(geom).area(MAX_ERROR).sqrt().multiply(GROWTH_RATE)
  if MIN_INFLUENCE_DISTANCE:
    d=d.max(MIN_INFLUENCE_DISTANCE)
  return d


#
# MAIN
#
def city_extent(city_name):
    city=cities.filter(ee.Filter.eq('City Name',city_name)).first()
    centroid=city.geometry()
    #
    # URBAN/SUBURBAN IMAGE:
    # => usubu: 0 rural, 1 suburban, 2 urban
    # => city_center: nearest non-null centroid
    #
    usubu_rededucer=ee.Reducer.mean()
    usubu_kernel=ee.Kernel.circle(
      radius=math.ceil(584/SCALE), 
      units='pixels', 
      normalize=True,
      magnitude=1
    )
    usubuc=bu.unmask(0).updateMask(not_water).reduceNeighborhood(
      reducer=usubu_rededucer,
      kernel=usubu_kernel,
      skipMasked=True,
    ).updateMask(bu.gte(0))

    usubu=ee.Image(0).where(usubuc.gte(0.25).And(usubuc.lt(0.5)),1).where(usubuc.gte(0.5),2)
    city_center=nearest_non_null(centroid,usubu.selfMask())
    #
    # VECTORIZE:
    # s1: features containing city_center
    # sN: features not containing city_center
    #
    MIN_CC=5
    geom=city_center.buffer(KM_RADIUS*1000,MAX_BUFFER_ERROR)
    cc=bu.connectedPixelCount(MIN_CC,True).eq(MIN_CC)
    feats=cc.selfMask().reduceToVectors(
      reducer=ee.Reducer.countEvery(),
      scale=SCALE,
      geometry=geom,
      maxPixels=1e11
    )

    center_filter=ee.Filter.intersects(leftField='.geo',rightValue=city_center,maxError=MAX_BUFFER_ERROR)

    s1=feats.filter(center_filter)
    sN=feats.filter(center_filter.Not())

    # Incorporate urbanized open spaces by 
    # - adding a 100 meter fringe open space buffer to interim cluster t1, === buffer t1 100 meter
    # - filling holes
    s1=ee.FeatureCollection(h.flatten_to_polygons(s1))
    s1=s1.map(fill_small,True)
    g1=s1.geometry().buffer(GREEN_ZONE,MAX_BUFFER_ERROR)
    s1=ee.FeatureCollection([ee.Feature(g1)])
    d1=get_influence_distance(g1)
    #
    # get all regions where the sum of the influence zones overlap
    #
    sN=sN.filter(ee.Filter.withinDistance(
      distance=MAX_INFLUENCE_DISTANCE, 
      leftField='.geo',
      rightValue=g1, 
      maxError=1
    ))

    def _influence_check(f):
      f=ee.Feature(f)
      g=f.geometry()
      d=get_influence_distance(g)
      test=g1.withinDistance(right=g, distance=d1.add(d), maxError=MAX_ERROR)
      return ee.Algorithms.If(test,f.set('influence_distance',d),None)

    sN_infl=sN.map(_influence_check,True)
    # 
    # only keep polygons containing urban pix
    #
    urban=usubu.eq(2).selfMask()
    def has_urban_pixel(feat):
      return geom_contains_pixels(ee.Feature(feat).geometry(),urban)

    sN_urbn=ee.FeatureCollection(h.flatten_to_polygons(sN_infl,has_urban_pixel))
    data={
        's1_influence_distance': d1
    }
    #
    # combine features
    #
    feats=ee.FeatureCollection([s1,sN_urbn]).flatten()
    return ee.Feature(feats.geometry(maxError=MAX_ERROR).dissolve(MAX_ERROR)).copyProperties(city).set(data)


features=ee.FeatureCollection(ee.List(CITY_NAMES).map(city_extent))

task=ee.batch.Export.table.toAsset(
      collection=features, 
      description=asset_name, 
      assetId=f'projects/wri-datalab/urban_land_use/urban_extent/{asset_name}')

print(task.start())
print(task.status())



