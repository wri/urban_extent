import os, geemap, ee, shapely, dask
import pandas as pd
import geopandas as gpd
ee.Authenticate()
ee.Initialize()

BASE_PATH = "C:/Users/Administrator/urbanexpansion"
WANT_RINGS = False


GHSL_BU_upload = ee.Image("projects/wri-datalab/GHSL/GHS_BUILT_S_MT_2023_100_BUTOT_MEDIAN")
GHSL_BU_cat = ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S")
popGHSLgee = ee.ImageCollection("JRC/GHSL/P2023A/GHS_POP")
popGHSLR2023AWSG84 = ee.ImageCollection("users/emackres/GHS_POP_GLOBE_R2023A_4326_3ss")
UCDB = ee.FeatureCollection("projects/wri-datalab/AUE/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2")


def indextoID(im):
    im = im.set('system:id',im.get('system:index')).rename(['population_count'])
    return im
popGHSLgee = popGHSLgee.map(indextoID)
popGHSLR2023AWSG84 = popGHSLR2023AWSG84.map(indextoID)

def poplayer(yr):
    popGHSL = popGHSLR2023AWSG84 
    popGHSL = popGHSL.select('population_count')
    popCountGHSL = popGHSL.filter(ee.Filter.eq('system:id', ee.Number(yr).format())).first()
    return popCountGHSL


UE1980 = ee.FeatureCollection("projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_1980")
UE1990 = ee.FeatureCollection("projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_1990")
UE2000 = ee.FeatureCollection("projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_2000")
# UE2005 = ee.FeatureCollection("projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_2005")
UE2010 = ee.FeatureCollection("projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_2010")
# UE2015 = ee.FeatureCollection("projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_2015")
UE2020 = ee.FeatureCollection("projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_2020")

def func_xfo(feat):
    currentyear = feat.get('year')
    return feat.set('builtup_year',currentyear)

renameyear = func_xfo

UE1980 = UE1980.map(renameyear)
UE1990 = UE1990.map(renameyear)
UE2000 = UE2000.map(renameyear)
# UE2005 = UE2005.map(renameyear)
UE2010 = UE2010.map(renameyear)
# UE2015 = UE2015.map(renameyear)
UE2020 = UE2020.map(renameyear)


urbextent_data = {
    1980: UE1980,
    1990: UE1990,
    2000: UE2000,
    2010: UE2010,
    2020: UE2020
}

urbextent_data_ee = ee.Dictionary({
    1980: UE1980,
    1990: UE1990,
    2000: UE2000,
    2010: UE2010,
    2020: UE2020
})

YEARS = (1980, 1990, 2000, 2010, 2020)
YEARINTERVAL = 10

built = GHSL_BU_cat.select('built_surface')

def builtyear(builtlayer, yr):
    builtlayer = builtlayer.filter(ee.Filter.eq('system:index', ee.Number(yr).format())).first()
    # builtlayer = builtlayer.gte(1000) # use only if wanting to threshold pixels to be counted as builtup
    builtlayer = builtlayer.selfMask().rename(['bu'])
    return builtlayer


# Calculate builtup area

def calcBuilt(feat, yr):
    builtArea = builtyear(built,yr).multiply(0.000001).rename(f'BuiltKM2_GHSL_{yr}')
    builtAreaproj = builtArea.projection()
    builtAreascale = builtArea.projection().nominalScale()
    builtAreasum = builtArea.reduceRegion(ee.Reducer.sum(),feat,builtAreascale,builtAreaproj).get(f'BuiltKM2_GHSL_{yr}')
    return builtAreasum

# def calcLandScanPop(geom, yr):
#     def get_pop(p_ic):
#         popproj = p_ic.first().projection()
#         popscale = p_ic.first().projection().nominalScale()
#         popdata_list = p_ic.toList(100)
    
#         def getSums(img, sumlist):
#             sumlist = ee.List(sumlist).add(ee.Image(img).reduceRegion(ee.Reducer.sum(), geom, popscale, popproj).get("population"))
#             return sumlist

#         poplist = popdata_list.iterate(getSums, [])
#         return ee.List(poplist).reduce(ee.Reducer.sum())

#     landscanmosaic_ic = ee.ImageCollection('projects/sat-io/open-datasets/ORNL/LANDSCAN_MOSAIC').filterBounds(geom).select("population")
#     result = ee.Algorithms.If(landscanmosaic_ic.size().gt(0), get_pop(landscanmosaic_ic), 0)

def calcGHSLPop(feat, yr):
    popGHSL = popGHSLgee 
    popGHSL = popGHSL.select('population_count')
    popCountGHSL = popGHSL.filter(ee.Filter.eq('system:id', ee.Number(yr).format())).first().rename(f'Pop_GHSL_{yr}')
    popCountGHSLproj = popCountGHSL.projection()
    popCountGHSLscale = popCountGHSL.projection().nominalScale()
    popCountGHSL = popCountGHSL.updateMask(popCountGHSL.neq(-200))
    # popCountsum = popCountGHSL.reduceRegion(ee.Reducer.sum(), feat, popCountGHSLscale, popCountGHSLproj).get(f'Pop_GHSL_{yr}')
    popCountsum = popCountGHSL.reduceRegion(ee.Reducer.sum(), feat, popCountGHSLscale, popCountGHSLproj).get(f'Pop_GHSL_{yr}')
    return popCountsum

def calcWorldpopPop(constrained, geom, yr):
    popdata_ic = None
    if constrained:
        if yr < 2015:# 2020:
            return -9999
        popdata_ic = ee.ImageCollection("projects/sat-io/open-datasets/WORLDPOP/pop")
        yr = str(yr)
    else:
        if yr < 2000:
            return -9999
        popdata_ic = ee.ImageCollection("WorldPop/GP/100m/pop")
    
    popdata_ic = popdata_ic.filter(ee.Filter.eq("year", yr)).filterBounds(geom).select("population")

    def get_pop(p_ic):
        popproj = p_ic.first().projection()
        popscale = p_ic.first().projection().nominalScale()
        popdata_list = p_ic.toList(100)
    
        def getSums(img, sumlist):
            sumlist = ee.List(sumlist).add(ee.Image(img).reduceRegion(ee.Reducer.sum(), geom, popscale, popproj).get("population"))
            return sumlist

        poplist = popdata_list.iterate(getSums, [])
        return ee.List(poplist).reduce(ee.Reducer.sum())
    
    result = ee.Algorithms.If(popdata_ic.size().gt(0), get_pop(popdata_ic), 0)  # No Worldpop imgs found if expansion region has zero area
    return result


# set risk threshold params
SLOPETHRESHOLD = 10 # slope in degrees used as threhold for "high slope". "[Landslide] susceptibility grows quickly between 10° and 30° slopes." (https://link.springer.com/article/10.1007/s11069-017-2757-y#Sec9)
HANDTHRESHOLD = 1
    
#Run calculations for slope risk
def calcSlopeRisk(geom, yr):

    # builtup layer for risk calcs
    builtup = builtyear(built, yr)
    # Using GHSL m2 in 100m pixel for area 
    builtArea = builtup.multiply(0.000001).rename('BuiltKM2_GHSL')
    # OR using GEE pixelArea() for area
    #builtArea = ee.Image.pixelArea().updateMask(builtup).multiply(0.000001)
    builtAreaproj = builtup.projection()
    builtAreascale = builtup.projection().nominalScale()
    
    ## Load slope data 
    dataset = ee.Image("NASA/NASADEM_HGT/001")
    elevation = dataset.select('elevation')
    proj = elevation.select(0).projection()
    slope_scale = proj.nominalScale()
    slope = ee.Terrain.slope(elevation) #.setDefaultProjection(proj));
    steep_slopes = slope.updateMask(slope.gte(SLOPETHRESHOLD))
    steepbuiltup = builtArea.updateMask(steep_slopes).rename('SteepBuiltup')
    steepbuiltupAreaSum = steepbuiltup.reduceRegion(ee.Reducer.sum(), geom, builtAreascale, builtAreaproj).get('SteepBuiltup')
    return steepbuiltupAreaSum
  
# Run calculations for pluvial flood risk
def calcFloodRisk(geom, yr):

    # builtup layer for risk calcs
    builtup = builtyear(built, yr)
    # Using GHSL m2 in 100m pixel for area 
    builtArea = builtup.multiply(0.000001).rename('BuiltKM2_GHSL')
    # OR using GEE pixelArea() for area
    #builtArea = ee.Image.pixelArea().updateMask(builtup).multiply(0.000001)
    builtAreaproj = builtup.projection()
    builtAreascale = builtup.projection().nominalScale()
    
#  height above nearest drainage
    hand30_1000 = ee.Image('users/gena/GlobalHAND/30m/hand-1000')
    hand = hand30_1000.focal_mean(0.1) 
    HANDthresh = hand.lte(HANDTHRESHOLD).focal_max(1).focal_mode(2, 'circle', 'pixels', 5)#//.mask(swbdMask)
    HANDthresh = HANDthresh.mask(HANDthresh)
    floodbuiltup = builtArea.updateMask(HANDthresh).rename('FloodProneBuiltup')
    floodbuiltupAreaSum = floodbuiltup.reduceRegion(ee.Reducer.sum(), geom, builtAreascale, builtAreaproj).get('FloodProneBuiltup')
    return floodbuiltupAreaSum

# Run calculations for protected area risk
def calcProtectedRisk(geom, yr):

    # builtup layer for risk calcs
    builtup = builtyear(built, yr)
    # Using GHSL m2 in 100m pixel for area 
    builtArea = builtup.multiply(0.000001).rename('BuiltKM2_GHSL')
    # OR using GEE pixelArea() for area
    #builtArea = ee.Image.pixelArea().updateMask(builtup).multiply(0.000001)
    builtAreaproj = builtup.projection()
    builtAreascale = builtup.projection().nominalScale()
    
    WDPA = ee.FeatureCollection('WCMC/WDPA/current/polygons')
    WDPAimage = ee.Image().float().paint(WDPA, 'REP_AREA')
    protectedbuiltup = builtArea.updateMask(WDPAimage).rename('ProtectedBuiltup')
    protectedbuiltupAreaSum = protectedbuiltup.reduceRegion(ee.Reducer.sum(), geom, builtAreascale,builtAreaproj).get('ProtectedBuiltup')
    return protectedbuiltupAreaSum


def one_feature(current_feature):
    result_feature = ee.Feature(geom=current_feature.geometry())
    year = ee.Number(current_feature.get("year"))
    result_feature = result_feature.set("geometry_year", year)
    result_feature = result_feature.set("geometry_type", "tenyear_expansionregion")
    city_id = current_feature.get('city_id')
    city_name = current_feature.get('city_name')
    city_id_large = current_feature.get('city_id_large')
    city_name_large = current_feature.get('city_name_large')
    country_name = current_feature.get('country_name')
    country_name_large = current_feature.get('country_name_large')
    country_ISO = current_feature.get('country_ISO')
    country_ISO_large = current_feature.get('country_ISO_large')
    ungeoscheme_reg1 = current_feature.get('ungeoscheme_reg1')
    ungeoscheme_reg2 = current_feature.get('ungeoscheme_reg2')
    ungeoscheme_reg3 = current_feature.get('ungeoscheme_reg3')
    ungeoscheme_LDC = current_feature.get('ungeoscheme_LDC')
    ungeoscheme_LLDC = current_feature.get('ungeoscheme_LLDC')
    ungeoscheme_SIDS = current_feature.get('ungeoscheme_SIDS')
    study_centroid_latlon = current_feature.get('study_centroid_latlon')
    result_feature = result_feature.set({
        "city_id": city_id,
        "city_name": city_name,
        "city_id_large": city_id_large,
        "city_name_large": city_name_large,
        "country_name": country_name,
        "country_name_large": country_name_large,
        "country_ISO": country_ISO,
        "country_ISO_large": country_ISO_large,
        "un_geoscheme_reg1": ungeoscheme_reg1,
        "un_geoscheme_reg2": ungeoscheme_reg2,
        "un_geoscheme_reg3": ungeoscheme_reg3,
        "un_geoscheme_LDC": ungeoscheme_LDC,
        "un_geoscheme_LLDC": ungeoscheme_LLDC,
        "un_geoscheme_SIDS": ungeoscheme_SIDS,
        "study_centroid_latlon": study_centroid_latlon
    })

    previous_featurecollection = ee.FeatureCollection(urbextent_data_ee.get(year.subtract(ee.Number(YEARINTERVAL)))).filter(ee.Filter.eq("city_id_large", city_id_large))
    current_geom = ee.Geometry(ee.Algorithms.If(previous_featurecollection.size().gt(0), current_feature.geometry().difference(previous_featurecollection.first().geometry()), current_feature.geometry()))
    result_feature = result_feature.setGeometry(current_geom)

    area = current_geom.area().multiply(0.000001)
    result_feature = result_feature.set("areaSQKM", area)
    for inneryear in YEARS:
        builtup_area = calcBuilt(current_geom, inneryear)
        populationGHSL = ee.Number(calcGHSLPop(current_geom, inneryear)).round()
        sloperisk_area = calcSlopeRisk(current_geom, inneryear)
        floodrisk_area = calcFloodRisk(current_geom, inneryear)
        protectedrisk_area = calcProtectedRisk(current_geom, inneryear)
        result_feature = result_feature.set(f"builtupareaSQKM_{inneryear}", builtup_area)
        result_feature = result_feature.set(f"populationGhslPERSONS_{inneryear}", populationGHSL)
        result_feature = result_feature.set(f"sloperiskareaSQKM_{inneryear}", sloperisk_area)
        result_feature = result_feature.set(f"floodriskareaSQKM_{inneryear}", floodrisk_area)
        result_feature = result_feature.set(f"protectedbuiltareaSQKM_{inneryear}", protectedrisk_area)
        if inneryear >= 2000:
            populationWPU = ee.Number(calcWorldpopPop(False, current_geom, inneryear)).round()
            result_feature = result_feature.set(f"populationWorldPopUnconstrainedPERSONS_{inneryear}", populationWPU)
        if inneryear >= 2015:
            populationWPC = ee.Number(calcWorldpopPop(True, current_geom, inneryear)).round()
            result_feature = result_feature.set(f"populationWorldPopConstrainedPERSONS_{inneryear}", populationWPC)

    # populationWPC = ee.Number(calcWorldpopPop(True, current_geom, 2020)).round()
    # result_feature = result_feature.set(f"populationWorldPopConstrainedPERSONS_2020", populationWPC)
    return ee.Algorithms.If(area.gt(0), result_feature, None)

def one_feature_firstyear(current_feature):
    result_feature = ee.Feature(geom=current_feature.geometry())
    year = ee.Number(current_feature.get("year"))
    result_feature = result_feature.set("geometry_year", year)
    result_feature = result_feature.set("geometry_type", "urban_extent")
    city_id = current_feature.get('city_id')
    city_name = current_feature.get('city_name')
    city_id_large = current_feature.get('city_id_large')
    city_name_large = current_feature.get('city_name_large')
    country_name = current_feature.get('country_name')
    country_name_large = current_feature.get('country_name_large')
    country_ISO = current_feature.get('country_ISO')
    country_ISO_large = current_feature.get('country_ISO_large')
    ungeoscheme_reg1 = current_feature.get('ungeoscheme_reg1')
    ungeoscheme_reg2 = current_feature.get('ungeoscheme_reg2')
    ungeoscheme_reg3 = current_feature.get('ungeoscheme_reg3')
    ungeoscheme_LDC = current_feature.get('ungeoscheme_LDC')
    ungeoscheme_LLDC = current_feature.get('ungeoscheme_LLDC')
    ungeoscheme_SIDS = current_feature.get('ungeoscheme_SIDS')
    study_centroid_latlon = current_feature.get('study_centroid_latlon')
    result_feature = result_feature.set({
        "city_id": city_id,
        "city_name": city_name,
        "city_id_large": city_id_large,
        "city_name_large": city_name_large,
        "country_name": country_name,
        "country_name_large": country_name_large,
        "country_ISO": country_ISO,
        "country_ISO_large": country_ISO_large,
        "un_geoscheme_reg1": ungeoscheme_reg1,
        "un_geoscheme_reg2": ungeoscheme_reg2,
        "un_geoscheme_reg3": ungeoscheme_reg3,
        "un_geoscheme_LDC": ungeoscheme_LDC,
        "un_geoscheme_LLDC": ungeoscheme_LLDC,
        "un_geoscheme_SIDS": ungeoscheme_SIDS,
        "study_centroid_latlon": study_centroid_latlon
    })

    current_geom = current_feature.geometry()
    area = current_geom.area().multiply(0.000001)
    result_feature = result_feature.set("areaSQKM", area)
    for inneryear in YEARS:
        builtup_area = calcBuilt(current_geom, inneryear)
        result_feature = result_feature.set(f"builtupareaSQKM_{inneryear}", builtup_area)
        populationGHSL = ee.Number(calcGHSLPop(current_geom, inneryear)).round()
        result_feature = result_feature.set(f"populationGhslPERSONS_{inneryear}", populationGHSL)
        sloperisk_area = calcSlopeRisk(current_geom, inneryear)
        result_feature = result_feature.set(f"sloperiskareaSQKM_{inneryear}", sloperisk_area)
        floodrisk_area = calcFloodRisk(current_geom, inneryear)
        result_feature = result_feature.set(f"floodriskareaSQKM_{inneryear}", floodrisk_area)
        protectedrisk_area = calcProtectedRisk(current_geom, inneryear)
        result_feature = result_feature.set(f"protectedbuiltareaSQKM_{inneryear}", protectedrisk_area)
        if inneryear >= 2000:
            populationWPU = ee.Number(calcWorldpopPop(False, current_geom, inneryear)).round()
            result_feature = result_feature.set(f"populationWorldPopUnconstrainedPERSONS_{inneryear}", populationWPU)
        if inneryear >= 2015:
            populationWPC = ee.Number(calcWorldpopPop(True, current_geom, inneryear)).round()
            result_feature = result_feature.set(f"populationWorldPopConstrainedPERSONS_{inneryear}", populationWPC)
    return result_feature



ics = ee.List([])
for year in YEARS:
    print(f"Starting {year}")
    urbext_fc = urbextent_data[year]
    results_fc = urbext_fc.map(one_feature_firstyear, dropNulls=True)
    if year > YEARS[0]:
        results_fc_rings = urbext_fc.map(one_feature, dropNulls=True)
        results_fc = ee.FeatureCollection([results_fc, results_fc_rings]).flatten().filter(ee.Filter.notNull(["city_id"])) # Filter removes zero-area rings
    
    # Export data to CSV saved in Google Drive
    # task = ee.batch.Export.table.toDrive(
    #     collection=results_fc.map(lambda f: f.setGeometry(None)),
    #     description=f"urbanextents_pops_areas_risk_{year}__CSV",
    #     fileFormat='CSV'
    # )
    # task.start()

    #Export data to GEE asset
    task = ee.batch.Export.table.toAsset(
        collection=results_fc,
        description=f"urbanextents_pops_areas_risk_{year}__ASSET",
        assetId=f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_pops_areas_risk_{year}' # Specify the output asset path
    )
    task.start()

    ics = ics.add(results_fc)


#### Run code below to save all years as one CSV or FeatureCollection

# all_ic = ee.FeatureCollection(ics).flatten()
        
# task = ee.batch.Export.table.toAsset(
#     collection=all_ic,
#     description=f"urbanextents_pops_areas_risk_ALL__ASSET",
#     assetId=f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_pops_areas_risk' # Specify the output asset path
# )
# task.start()
# task = ee.batch.Export.table.toDrive(
#     collection=all_ic.map(lambda f: f.setGeometry(None)),
#     description=f"urbanextents_pops_areas_risk",
#     # asset_id="urbanextents_pops_areas_risk",
#     fileFormat='CSV'
# )
# task.start()




# os.chdir('C:/Users/tgwon/wri/urbanexpansion')
# dfs = [pd.read_csv(f"urbext_pops_areas_{year}_PARIS.csv") for year in YEARS]
# all_results = pd.concat(dfs, axis=0)
# all_results = all_results[all_results.columns[1:-1]]
# all_results.to_csv("urbanexpansion_pops_areas_allyears_PARIS.csv")