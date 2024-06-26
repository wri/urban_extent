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


# dw=ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
# not_water=dw.select(['label']).filterDate('2018-01-01','2018-07-01').reduce(ee.Reducer.mode()).neq(0)
inlandwater=ee.ImageCollection("GLCF/GLS_WATER").reduce(ee.Reducer.firstNonNull())
not_water=inlandwater.neq(2)


# CITY_NAMES=['Medan','Shenzhen, Guangdong']
# CITY_NAMES=['Shenzhen, Guangdong']
# CITY_NAMES=['Medan']
# asset_name=f'ue_ghsl_{KM_RADIUS}-{SCALE}'+'MedanShenzhen'


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

asset_name=f'ue_wsl-water_msk_r{KM_RADIUS}_s{SCALE}_n{BS}-{N+1}'

CITY_NAMES=['Alexandria']
asset_name=f'ue_joint-Alexandria_pix_inw_mb_{MINBUFF}_r{KM_RADIUS}_s{SCALE}_n{BS}-{N+1}'


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
      geometry=centroid.buffer(max_distance), 
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
    geom=city_center.buffer(KM_RADIUS*1000)
    # cc=bu.connectedPixelCount(MIN_CC,True).reproject(bu.projection()).eq(MIN_CC)
    cc=bu.connectedPixelCount(MIN_CC,True).eq(MIN_CC)
    feats=cc.selfMask().reduceToVectors(
      reducer=ee.Reducer.countEvery(),
      scale=SCALE,
      geometry=geom,
      maxPixels=1e11
    )
    s1=feats.filterBounds(city_center)#.geometry()



    # 5. Incorporate urbanized open spaces by 
    # - adding a 100 meter fringe open space buffer to interim cluster t1, === buffer t1 100 meter
    # - filling holes


    t1=ee.FeatureCollection(h.flatten_to_polygons(s1))
    t1=t1.map(fill_small,True)
    t1=t1.geometry().buffer(100)

    # 9. Around cluster c1, create a buffer equal to 1/4 the area of cluster c1. 

    buff1=h.growth_buffer(t1,0.25,0.01)
    buff=ee.Number(buff1).max(MINBUFF)
    t2=t1.buffer(buff)
    buffer_area=t2.difference(t1)


    # 
    #  GROWTH CHECK
    # 
    a1=t1.area(1)
    a2=t2.area(1)
    ab=buffer_area.area(1)
    # print(ee.Dictionary({
    #     'buffer': buff,
    #     'a1':a1,
    #     'a2':a2,
    #     'buffer_area': ab,
    #     'rb1':ab.divide(a1),
    #     'r21':a2.divide(a1)
    # }).getInfo())


    #
    # EXTENDED AREA
    #
    s2=feats.filterBounds(buffer_area).geometry()



    #
    # ISOLOTATE NEW POLYGONS
    #
    s3=s2.difference(s1,1)
    urban=usubu.eq(2).selfMask()


    def has_urban_pixel(feat):
      return geom_contains_pixels(ee.Feature(feat).geometry(),urban)

    t3g=ee.FeatureCollection(h.flatten_to_polygons(s3,has_urban_pixel))
    data={
        'buffer': buff
    }
    #
    # COMBINE FEATURES
    #
    # print('bOOM')
    # print(ee.Dictionary(data).getInfo())
    feat=ee.FeatureCollection([ee.FeatureCollection([t1]),t3g]).flatten()
    # feat=ee.FeatureCollection([ee.FeatureCollection([t1])]).flatten()
    # feat=s1
    return ee.Feature(feat.geometry().dissolve(1)).copyProperties(city).set(data)

# city_extent(CITY_NAMES[0])

features=ee.FeatureCollection(ee.List(CITY_NAMES).map(city_extent))

task=ee.batch.Export.table.toAsset(
      collection=features, 
      description=asset_name, 
      assetId=f'projects/wri-datalab/urban_land_use/urban_extent/{asset_name}')

print(task.start())
print(task.status())



