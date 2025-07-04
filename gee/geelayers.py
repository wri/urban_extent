import ee
import config
ee.Initialize()


#
# GET DATA
#
# Subset city points
if config.USE_COMPLETED_FILTER:
    COMPLETED_CITIES = ee.ImageCollection(config.IC_ID).filter(ee.Filter.equals('builtup_year', config.mapYear))
    COMPLETED_CITIES_LIST = COMPLETED_CITIES.aggregate_array(config.CITY_ID_COL).getInfo()
    CITY_LIST = config.CITY_DATA_POINT.aggregate_array(config.CITY_ID_COL).getInfo()
    COMPLETED_FILTER = [item for item in CITY_LIST if item not in COMPLETED_CITIES_LIST]
    CITY_DATA = config.CITY_DATA_POINT.filter(ee.Filter.inList(config.CITY_ID_COL, COMPLETED_FILTER))
else:
    CITY_DATA = config.CITY_DATA_POINT


# Built up area mask
# based on public GHS data using BuiltAreaThresh
GHSLyear = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{config.mapYear}").gte(config.BuiltAreaThresh).selfMask().select('built_surface').rename(['bu'])

# obtain projection, CRS and Transform for input layer
_proj = GHSLyear.projection().getInfo()

# "ESRI:54009" # for use with GHSL2023release image which doesn't have CRS in metadata.
GHSL_CRS = "EPSG:3857"
GHSL_TRANSFORM = _proj['transform']
# print("GHSL PROJ:", GHSL_CRS, GHSL_TRANSFORM)

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
