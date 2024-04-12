import ee
ee.Initialize()

import geemap.foliumap as geemap
import config

#
# GET DATA
#

# Old output built-up density
#  based GHSL data with built-up threshold of 10%
## All
GHSL = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/builtup_density_GHSL_BUthresh10pct')
## 2020
GHSL_2020 = GHSL.filter(ee.Filter.stringContains('system:index', '2020'))

# New City data
## Polygons
CITY_DATA_POLY = ee.FeatureCollection('projects/wri-datalab/AUE/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2')
## Centroids
### Function to convert each polygon feature to a point feature based on 'lat' and 'long' attributes
def polygon_to_point(feature):
    lat = ee.Number(feature.get('GCPNT_LAT'))
    long = ee.Number(feature.get('GCPNT_LON'))
    point = ee.Geometry.Point([long, lat])
    return ee.Feature(point, feature.toDictionary())
### Map the conversion function over the polygon FeatureCollection
CITY_DATA = CITY_DATA_POLY.map(polygon_to_point)


if config.USE_COMPLETED_FILTER:
    COMPLETED_IDS = ee.ImageCollection(config.IC_ID).aggregate_array('ID_HDC_G0')
    COMPLETED_FILTER = ee.Filter.And(ee.Filter.inList('ID_HDC_G0', COMPLETED_IDS), ee.Filter.equals('builtup_year', config.mapYear))
    COMPLETED_CITIES_LIST = ee.ImageCollection(config.IC_ID).filter(COMPLETED_FILTER).aggregate_array('ID_HDC_G0')
    CITY_DATA = CITY_DATA.filter(ee.Filter.inList('ID_HDC_G0', COMPLETED_CITIES_LIST).Not())
else:
    CITY_DATA = CITY_DATA



# Built up area mask
# based on public GHS data using BuiltAreaThresh
GHSLyear = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{config.mapYear}").gte(config.BuiltAreaThresh).selfMask().select('built_surface').rename(['bu'])

# obtain projection, CRS and Transform for input layer
_proj = GHSLyear.projection().getInfo()

# "ESRI:54009" # for use with GHSL2023release image which doesn't have CRS in metadata.
GHSL_CRS = "EPSG:3857"
GHSL_TRANSFORM = _proj['transform']
print("GHSL PROJ:", GHSL_CRS, GHSL_TRANSFORM)

#
# Select built-up IMAGE
#
BU = GHSLyear

# create band ("builtup") with binary builtup value
IS_BUILTUP = BU.gt(0).rename(['builtup'])

# create band ("density") with the percent of pixels that are built-up within radius of each pixel
_usubu_rededucer = ee.Reducer.mean()
_usubu_kernel = ee.Kernel.circle(
    radius=config.DENSITY_RADIUS,
    units=config.DENSITY_UNIT,
    normalize=True,
    magnitude=1
)
_density = IS_BUILTUP.unmask(0).reduceNeighborhood(
    reducer=_usubu_rededucer,
    kernel=_usubu_kernel,
    skipMasked=True,
)
# create band ("builtup_class") with built-up classification (urban, suburban, rural) for each built-up pixel based on its "density" value
_usubu = ee.Image(0).where(_density.gte(config.SUBURBAN_BOUND).And(_density.lt(config.URBAN_BOUND)), 1).where(_density.gte(config.URBAN_BOUND), 2).rename(['builtup_class'])
_density = _density.multiply(100).rename(['density'])
BU_DENSITY_CAT = _usubu.addBands([_density, IS_BUILTUP]).toUint8()

# create image of all urban or suburban builtup pixels that have at least MINPIXS neighbors that are also urban or suburban builtup pixels
BU_CONNECTED = IS_BUILTUP.multiply(_usubu.gt(0)).selfMask().connectedPixelCount(config.MINPIXS).eq(config.MINPIXS).selfMask()
BU_LATLON = BU_CONNECTED.addBands(ee.Image.pixelLonLat())




def interactive_map():

    Map = geemap.Map(center=[40,-100], zoom=4)

    # Map.addLayer(ee_object, vis_params, name, shown, opacity)
    # Urban Extent layers
    Map.addLayer(CITY_DATA_POLY, {}, 'New City Data Polygons', True)
    Map.addLayer(CITY_DATA, city_points_vis, 'New City Data Points', True)
    Map.addLayer(GHSL, {}, 'Old Builtup Density', False)
    Map.addLayer(GHSL_2020, {}, 'Old Builtup Density 2020', False)
    Map.addLayer(BU, {}, 'New Built up Surface input', False)
    Map.addLayer(IS_BUILTUP, {}, 'New Built up Surface binary', False)
    Map.addLayer(BU_DENSITY_CAT, {}, 'Builtup Density Categories', False)
    # Add 2 other bands from BU_DENSITY_CAT
    Map.addLayer(BU_LATLON, {}, 'Connected Builtup Pixels LatLon', False)
    # Add 1 other bands from BU_LATLON


    Map.addLayerControl()
    Map.setCenter(-71.0589, 42.3601, 8)
    return Map

# Get some example datasets
dem = ee.Image('USGS/SRTMGL1_003')
landcover = ee.Image("ESA/GLOBCOVER_L4_200901_200912_V2_3").select('landcover')
landsat7 = ee.Image('LANDSAT/LE7_TOA_5YEAR/1999_2003')
states = ee.FeatureCollection("TIGER/2018/States")

# Custom vis_params
dem_vis = {
'min': 0,
'max': 4000,
'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']}

landsat_vis = {
    'min': 20,
    'max': 200,
    'bands': ['B4', 'B3', 'B2']
}

city_points_vis = {
    'color': 'yellow',
    'pointSize': 25,
    'pointShape': 'circle',
    'width': 1
}
