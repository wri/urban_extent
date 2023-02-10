import ee
import helpers as h
import data
import math
ee.Initialize()


BS=25
N=4  # Nmax ~7

# SCALE=10
SCALE=38
#
# CONSTANTS
#
STUDY_AREAS_ID='projects/wri-datalab/urban_land_use/data/study_area_features-partial_124'

MAX_AREA=2e6
MAX_NNN_DISTANCE=1000
# KM_RADIUS=80
# MINBUFF=1000

# GROWTH_RATE=0.07
# GREEN_ZONE=None
# MAX_ERROR=1
# MAX_BUFFER_ERROR=10

# MIN_INFLUENCE_DISTANCE=1000
ASSET_PREFIX='sa_ue-p124'


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


* NO MAX  !!!-DONE
* MIN 1000  !!!-DONE
* REMOVE GREEN BUFFER  !!!-DONE

TODO:   ADD SENTENCE TO about green buffer to paper

"""


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

STUDY_AREAS=ee.FeatureCollection(STUDY_AREAS_ID)

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



# bu=bu.reproject(crs='epsg:4326',scale=SCALE)

asset_name=f'S1s100_carea_{ASSET_PREFIX}-r{KM_RADIUS}_s{SCALE}_n{BS}-{N+1}'
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



def geom_contains_pixel(geom,im):
  return im.rename(['contains_pixel']).reduceRegion(
    reducer=ee.Reducer.firstNonNull(),
    geometry=ee.Geometry(geom),
    scale=SCALE
  ).getNumber('contains_pixel').eq(1)



def get_influence_distance(area):
  d=area.sqrt().multiply(GROWTH_RATE)
  return d.max(MIN_INFLUENCE_DISTANCE)




#
# MAIN
#
def city_extent(city_name):
    city_filter=ee.Filter.eq('City Name',city_name)
    city=cities.filter(city_filter).first()
    sa=STUDY_AREAS.filter(city_filter)
    centroid=city.geometry()
    s1=sa.filterBounds(centroid)

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
      maxPixels=1e11,
    )

    center_filter=ee.Filter.intersects(leftField='.geo',rightValue=city_center,maxError=MAX_BUFFER_ERROR)
    s1=feats.filter(center_filter)
    # sN=feats.filter(center_filter.Not())

    if GREEN_ZONE:
      g1=s1.geometry().buffer(GREEN_ZONE,MAX_BUFFER_ERROR)
    else:
      g1=s1.geometry()
    g1=g1.simplify(100)
    a1=ee.Geometry(g1).area(MAX_ERROR)
    infl1=get_influence_distance(a1)
    s1=ee.Feature(g1)

    # sN=sN.filter(ee.Filter.withinDistance(
    #   distance=infl1.multiply(2), 
    #   leftField='.geo', 
    #   rightValue=g1, 
    #   maxError=MAX_BUFFER_ERROR
    # ))

    # sN_urban=urban.reduceRegions(
    #   collection=sN,
    #   reducer=ee.Reducer.firstNonNull(),
    #   scale=SCALE    
    # ).filter(ee.Filter.eq('IS_URBAN',1))

    # def _feature_data(feat):
    #   feat=ee.Feature(feat)
    #   g=feat.geometry()
    #   infl=get_influence_distance(g)
    #   distance=g1.distance(g,MAX_ERROR)
    #   include=distance.subtract(infl).subtract(infl1).lte(0)
    #   return feat.set({ 'include': include })

    # sN_urban=sN_urban.map(_feature_data).filter(ee.Filter.eq('include',1))
    # #
    # # combine features
    # #
    # feats=ee.FeatureCollection([s1,sN_urban]).flatten()
    return s1.set({
        'city_name': city_name,
        'influence_distance': infl1,
        'center_area': a1
      })


# test=city_extent(CITY_NAMES[0])
# print('DONE')
# print(test.getInfo())

features=ee.FeatureCollection(ee.List(CITY_NAMES).map(city_extent))
# features=ee.FeatureCollection(ee.List(CITY_NAMES).map(city_extent)).flatten()

task=ee.batch.Export.table.toAsset(
      collection=features, 
      description=asset_name, 
      assetId=f'projects/wri-datalab/urban_land_use/urban_extent/{asset_name}')

print(task.start())
print(task.status())



