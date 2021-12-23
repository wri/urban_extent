import ee
import helpers as h
ee.Initialize()

#
# CONSTANTS
#
MAX_AREA=2e6
MAX_NNN_DISTANCE=1000
SCALE=38

CITY_CENTROIDS_ID='projects/wri-datalab/AUE/city_data-2010pop100k'
BUILT_UP_ID='JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1'



#
# ASSETS
#
cities=ee.FeatureCollection(CITY_CENTROIDS_ID)
builtup_im=ee.Image(BUILT_UP_ID)



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


#
# MAIN
#

# *****************

#
# 1. Select City, Get Centroid
#
city=cities.first()
centroid=city.geometry()
print(city.toDictionary().getInfo(),centroid.getInfo())


#
# 2. URBAN/SUBURBAN IMAGE
# => usubu: 0 rural, 1 suburban, 2 urban
# => city_center: nearest non-null centroid
#
bu=builtup_im.select(['built']).gte(3).selfMask()
usubu_rededucer=ee.Reducer.mean()
usubu_kernel=ee.Kernel.circle(
  radius=584, 
  units='meters', 
  normalize=True,
  magnitude=1
)
usubuc=bu.unmask(0).reduceNeighborhood(
  reducer=usubu_rededucer, 
  kernel=usubu_kernel, 
  skipMasked=True, 
).updateMask(bu.gte(0))

usubu=ee.Image(0).where(usubuc.gte(0.25).And(usubuc.lt(0.5)),1).where(usubuc.gte(0.5),2)
city_center=nearest_non_null(centroid,usubu.selfMask())






# 4. Select all of built-up pixels that are contiguous to p0, and merge these pixels to create study area s1. 
# >>> already since no rural pix: Merge the contiguous suburban and urban pixels in s1 to create interim cluster t1. 

MIN_CC=5
geom=city_center.buffer(500*1000)
cc=bu.connectedPixelCount(MIN_CC,True).reproject(bu.projection()).eq(MIN_CC)
feats=cc.selfMask().reduceToVectors(
  reducer=ee.Reducer.countEvery(),
  geometry=geom,
  maxPixels=1e11
)
s1=feats.filterBounds(city_center).geometry()



# 5. Incorporate urbanized open spaces by 
# - adding a 100 meter fringe open space buffer to interim cluster t1, === buffer t1 100 meter
# - filling holes


t1=ee.FeatureCollection(h.flatten_to_polygons(s1))
t1=t1.map(fill_small,True)
t1=t1.geometry().buffer(100)

# 9. Around cluster c1, create a buffer equal to 1/4 the area of cluster c1. 

buff=h.growth_buffer(t1,0.25,0.01)
t2=t1.buffer(buff)
buffer_area=t2.difference(t1)


# 
#  GROWTH CHECK
# 
a1=t1.area(1)
a2=t2.area(1)
ab=buffer_area.area(1)
print(ee.Dictionary({
    'buffer': buff,
    'a1':a1,
    'a2':a2,
    'buffer_area': ab,
    'rb1':ab.divide(a1),
    'r21':a2.divide(a1)
}).getInfo())


#
# EXTENDED AREA
#
s2=feats.filterBounds(buffer_area).geometry()



#
# ISOLOTATE NEW POLYGONS
#
s3=s2.difference(s1,1)
urban=usubu.eq(2).selfMask()

def geom_contains_pixels(geom,im):
  return im.rename(['count']).reduceRegion(
    reducer=ee.Reducer.count(),
    geometry=ee.Geometry(geom),
    scale=SCALE
  ).getNumber('count').gt(0)

def has_urban_pixel(feat):
  return geom_contains_pixels(ee.Feature(feat).geometry(),urban)

t3g=ee.FeatureCollection(h.flatten_to_polygons(s3,has_urban_pixel))



task=ee.batch.Export.table.toAsset(
  collection=ee.FeatureCollection([ee.FeatureCollection([t1]),t3g]).flatten(), 
  description='testing123', 
  assetId='projects/wri-datalab/testing_2')

print(task.start())
print(task.status())

t3=ee.FeatureCollection(h.flatten_to_polygons(s3))


print(ee.Dictionary({
    't3size': t3.size(),
    't3gsize': t3g.size(),
}).getInfo())


