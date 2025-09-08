import ee
import helpers as h
import re

import config


ee.Initialize()

#
# CONFIG
#
VECTOR_SCALE = None
INPUT_VECTOR_SCALE = VECTOR_SCALE
LIMIT = None
DRY_RUN = False
RASTER_BUFFER = False
VECTOR_BUFFER = None
TEST_CITY = None
ENSURE_FEATS = False
SPLIT_INDEX = False
ENSURE_FEATS = True


#
# CONSTANTS
#
MAX_FILL = 2e6
AREA_PROPS = ['rural_area', 'suburban_area', 'urban_area']
AREA_REDUCER = ee.Reducer.sum().combine(
    ee.Reducer.sum(), outputPrefix=f'suburban_area_').combine(
    ee.Reducer.sum(), outputPrefix=f'urban_area_')


if RASTER_BUFFER:
    RASTER_BUFFER_KERNEL = ee.Kernel.euclidean(RASTER_BUFFER, 'meters')
else:
    RASTER_BUFFER_KERNEL = None


#
# IMPORTS
#
SUPER_IC = ee.ImageCollection(config.IC_ID).filter(ee.Filter.eq('builtup_year', config.mapYear))
# .filter(ee.Filter.eq('Reg_Name',REGION))#.filter(ee.Filter.eq('City__Name','Kigali'))#


if VECTOR_SCALE:
    TRANSFORM = None
else:
    GHSL2023release = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{config.mapYear}")
    _proj = GHSL2023release.projection().getInfo()
    GHSL_CRS = "EPSG:3857"

    GHSL_TRANSFORM = _proj['transform']
    print("GHSL PROJ:", GHSL_CRS, GHSL_TRANSFORM)
    TRANSFORM = GHSL_TRANSFORM
    VECTOR_SCALE = None


def urban_extent(im):
    im = ee.Image(im)
    bu = im.select('builtup')
    bu_class = im.select('builtup_class')
    pa = ee.Image.pixelArea()
    bu_pixels = bu_class.gt(0).multiply(bu).selfMask()
    if RASTER_BUFFER:
        bu_pixels = bu_pixels.distance(
            kernel=RASTER_BUFFER_KERNEL,
            skipMasked=False).gte(0)
    pa = bu_pixels.selfMask().addBands([
        pa.multiply(bu_class.eq(0)),
        pa.multiply(bu_class.eq(1)),
        pa.multiply(bu_class.eq(2))
    ]).rename(['label']+AREA_PROPS)
    feats = pa.reduceToVectors(
        reducer=ee.Reducer.sum(),
        crs=GHSL_CRS,
        scale=VECTOR_SCALE,
        crsTransform=TRANSFORM,
        maxPixels=1e11,
        bestEffort=True
    )
    feats = feats.filter(ee.Filter.gt('urban_area', 0))
    data = feats.reduceColumns(
        reducer=AREA_REDUCER,
        selectors=AREA_PROPS
    )
    data = data.rename(['sum', 'suburban_area_sum', 'urban_area_sum'], AREA_PROPS)
    feats = h.flatten_to_polygons_and_fill_holes(feats, MAX_FILL)
    feat = ee.Feature(feats.geometry(config.MAX_ERR), data)
    if VECTOR_BUFFER:
        feat = feat.buffer(VECTOR_BUFFER, config.MAX_ERR)
    if ENSURE_FEATS:
        feat = feat.set('nb_input_features', feats.size())
    return feat.copyProperties(im)


urban_extents_fc = ee.FeatureCollection(SUPER_IC.map(urban_extent))
if ENSURE_FEATS:
    urban_extents_fc = urban_extents_fc.filter(
        ee.Filter.gt('nb_input_features', 0))


description = re.sub('[\.\,\/]', '--', f"JRCs_{config.mapYear}a")
asset_id = f'{config.ROOT}/global_GUPPD_Mar2025/GHSL_BUthresh10pct_JRCs_{config.mapYear}a'
print('\n'*1)
print(f'EXPORTING [{SUPER_IC.size().getInfo()}]:', asset_id)

task = ee.batch.Export.table.toAsset(
    collection=urban_extents_fc,
    description=description,
    assetId=asset_id)
if DRY_RUN:
    print('--dry_run')
else:
    task.start()
    print(task.status())
