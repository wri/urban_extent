import ee
import helpers as h
import data
import math
ee.Initialize()


BS=10
N=0
SCALE=10
# SCALE=38
# SCALE=50

#
# CONSTANTS
#
MAX_AREA=2e6
MAX_NNN_DISTANCE=1000
KM_RADIUS=80
MINBUFF=1000
CITY_CENTROIDS_ID='projects/wri-datalab/AUE/city_data-2010pop100k'




MAX_INFLUENCE_DISTANCE=2000
GROWTH_RATE=0.1
MIN_BUFF=100
GREEN_ZONE=100
MAX_ERROR=1
MAX_BUFFER_ERROR=10


# dw=ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
# not_water=dw.select(['label']).filterDate('2018-01-01','2018-07-01').reduce(ee.Reducer.mode()).neq(0)
inlandwater=ee.ImageCollection("GLCF/GLS_WATER").reduce(ee.Reducer.firstNonNull())
not_water=inlandwater.neq(2)


CITY_NAMES=['Medan','Shenzhen, Guangdong']
# CITY_NAMES=['Shenzhen, Guangdong']
# CITY_NAMES=['Medan']
asset_name=f'v2_{KM_RADIUS}-{SCALE}'+'MedanShenzhen'


#
# ASSETS
#
cities=ee.FeatureCollection(CITY_CENTROIDS_ID).sort('City Name')
# ALL_NAMES=cities.toList(6000).map(lambda c: ee.Feature(c).get('City Name')).getInfo()
# print('NAME COUNT:',len(ALL_NAMES))
# MATCHED_NAMES=[n for n in data.AUE_CITIES if n in ALL_NAMES]
# print('MATCHED COUNT:',len(MATCHED_NAMES))
# CITY_NAMES=MATCHED_NAMES[N*BS:(N+1)*BS]
# print(N*BS,(N+1)*BS,CITY_NAMES)

# asset_name=f'ue_wsl-water_msk_r{KM_RADIUS}_s{SCALE}_n{BS}-{N+1}'

# CITY_NAMES=['Alexandria']
# asset_name=f'ue_joint_v2-Alexandria_pix_inw_mb_{MINBUFF}_r{KM_RADIUS}_s{SCALE}_n{BS}-{N+1}'


print(asset_name,CITY_NAMES)
# BUILT_UP_ID='JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1'
# builtup_im=ee.Image(BUILT_UP_ID)
# bu=builtup_im.select(['built']).gte(3).selfMask()

# BUILT_UP_ID="DLR/WSF/WSF2015/v1"
# builtup_im=ee.Image(BUILT_UP_ID)
# bu=builtup_im.eq(255).selfMask()

BUILT_UP_ID1='JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1'
builtup_im1=ee.Image(BUILT_UP_ID1)
bu1=builtup_im1.select(['built']).gte(3).selfMask()

BUILT_UP_ID2="DLR/WSF/WSF2015/v1"
builtup_im2=ee.Image(BUILT_UP_ID2)
bu2=builtup_im2.eq(255).selfMask()


bu=ee.ImageCollection([
  bu1.selfMask().toInt().rename('bu'),
  bu2.selfMask().toInt().rename('bu')
]).reduce(ee.Reducer.firstNonNull())


if SCALE!=10:
    print('reproject')
    bu=bu.reproject(crs='epsg:4326',scale=SCALE)

# CITY_NAMES=cities.toList(2).map(lambda f: ee.Feature(f).get('City Name'))
# print('CITY_NAMES:',CITY_NAMES.getInfo())

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


# *****************
# NEW
# *****************



def get_influence_distance(geom):
  return ee.Geometry(geom).area(MAX_ERROR).sqrt().multiply(GROWTH_RATE)




#
# MAIN
#

# *****************

#
# 1. Select City, Get Centroid
#
def city_extent(city_name):

    city=cities.filter(ee.Filter.eq('City Name',city_name)).first()
    centroid=city.geometry()
    # print(city.toDictionary().getInfo(),centroid.getInfo())



    #
    # 2. URBAN/SUBURBAN IMAGE
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
    # usubuc=bu.unmask(0).reduceNeighborhood(
    usubuc=bu.unmask(0).updateMask(not_water).reduceNeighborhood(
      reducer=usubu_rededucer,
      kernel=usubu_kernel,
      skipMasked=True,
    ).updateMask(bu.gte(0))

    usubu=ee.Image(0).where(usubuc.gte(0.25).And(usubuc.lt(0.5)),1).where(usubuc.gte(0.5),2)
    city_center=nearest_non_null(centroid,usubu.selfMask())






    # 4. Select all of built-up pixels that are contiguous to p0, and merge these pixels to create study area s1. 
    # >>> already since no rural pix: Merge the contiguous suburban and urban pixels in s1 to create interim cluster t1. 

    MIN_CC=5
    geom=city_center.buffer(KM_RADIUS*1000,MAX_BUFFER_ERROR)
    # cc=bu.connectedPixelCount(MIN_CC,True).reproject(bu.projection()).eq(MIN_CC)
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


    # # 5. Incorporate urbanized open spaces by 
    # # - adding a 100 meter fringe open space buffer to interim cluster t1, === buffer t1 100 meter
    # # - filling holes

    s1=ee.FeatureCollection(h.flatten_to_polygons(s1))
    s1=s1.map(fill_small,True)
    g1=s1.geometry().buffer(GREEN_ZONE,MAX_BUFFER_ERROR)
    s1=ee.FeatureCollection([ee.Feature(g1)])
    d1=get_influence_distance(g1)



    # print('boomtown')
    # print(ee.Dictionary({
    #   'd1': d1,
    #   's1': s1.size(),
    #   # 'sn':sN.size(),
    #   # 'sn_infl':sN_infl.size(),
    #   # 'example':sN_infl.first().toDictionary()
    # }).getInfo())

    #
    # get all regions where the sum of the influence zones overlap
    #

    sN=sN.filter(ee.Filter.withinDistance(
      distance=MAX_INFLUENCE_DISTANCE, 
      leftField='.geo',
      rightValue=g1, 
      maxError=1
    ))


    # print('boomtown1')
    # print(ee.Dictionary({
    #   # 'd1': d1,
    #   # 's1': s1.size(),
    #   'sn':sN.size(),
    #   # 'sn_infl':sN_infl.size(),
    #   # 'example':sN_infl.first().toDictionary()
    # }).getInfo())

    def _influence_check(f):
      f=ee.Feature(f)
      g=f.geometry()
      d=get_influence_distance(g)
      test=g1.withinDistance(right=g, distance=d1.add(d), maxError=MAX_ERROR)
      return ee.Algorithms.If(test,f.set('influence_distance',d),None)


    sN_infl=sN.map(_influence_check,True)

    # print('boomtown2')
    # print(ee.Dictionary({
    #   # 'd1': d1,
    #   # 'sn':sN.size(),
    #   'sn_infl':sN_infl.size(),
    #   'example':sN_infl.first().toDictionary()
    # }).getInfo())


    # #
    # # only keep polygons containing urban pix
    # #
    urban=usubu.eq(2).selfMask()


    def has_urban_pixel(feat):
      return geom_contains_pixels(ee.Feature(feat).geometry(),urban)

    sN_urbn=ee.FeatureCollection(h.flatten_to_polygons(sN_infl,has_urban_pixel))
    data={
        's1_influence_distance': d1
    }
    #
    # COMBINE FEATURES
    #
    # print(ee.Dictionary(data).getInfo())

    feats=ee.FeatureCollection([s1,sN_urbn]).flatten()

    # print('bOOM')
    # print(ee.Dictionary({
    #   'feats':feats.size(),
    #   'feat':feats.first().toDictionary()
    # }).getInfo())

    return ee.Feature(feats.geometry(maxError=MAX_ERROR).dissolve(MAX_ERROR)).copyProperties(city).set(data)

# out=city_extent(CITY_NAMES[0])
# print('kapow')
# print(ee.Feature(out).toDictionary().getInfo())

features=ee.FeatureCollection(ee.List(CITY_NAMES).map(city_extent))

task=ee.batch.Export.table.toAsset(
      collection=features, 
      description=asset_name, 
      assetId=f'projects/wri-datalab/urban_land_use/urban_extent/{asset_name}')

print(task.start())
print(task.status())



