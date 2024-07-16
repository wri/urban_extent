import re
from unidecode import unidecode
import ee
# ee.Authenticate(force=True)
ee.Initialize()

import config
import geelayers
import helpers


# Create a function called get_super_feat
def get_urban_extents(IDS, CITIES_LIST, cities_track):
    TASKS = []

    for i, ident in enumerate(IDS):
        if ident in CITIES_LIST:
            # get on city centroid feature
            feat = ee.Feature(geelayers.CITY_DATA_POINT.filter(ee.Filter.eq('ID_HDC_G0', ident)).first())
            # feat.getInfo()
            city_name = feat.getString('UC_NM_MN').getInfo()
            print(f'{i}: {city_name} [{ident}]')
            # get feature for city boundary as defined by vectorize function
            # feat = ee.Feature(helpers.get_super_feat(feat))
            city_track = cities_track.loc[ident]
            circle_feat = helpers.get_circle_data_simple(feat, city_track)# get_circle_data
            feat = helpers.vectorize(circle_feat)
            feat = feat.set({'scale_factor_set':ee.Algorithms.If(ee.Feature(circle_feat).contains(ee.Feature(feat)),'True','False')})
            # print_info(super_feat=feat.toDictionary())
            print('='*100)
            asset_name = unidecode(f'{city_name}-{ident}-{config.mapYear}')
            asset_name = re.sub(r'[^A-Za-z0-9\-\_]+', '', asset_name)
            bu = ee.Image(geelayers.BU_DENSITY_CAT.copyProperties(feat))
            geom = feat.geometry()
            # Export image to output ImageCollection with 3 builtup information bands for area within the city boundary
            task = ee.batch.Export.image.toAsset(
                image=bu,
                description=asset_name,
                assetId=f'{config.IC_ID}/{asset_name}',
                pyramidingPolicy=config.PPOLICY,
                region=geom,
                crs=geelayers.GHSL_CRS,
                crsTransform=geelayers.GHSL_TRANSFORM,
                maxPixels=1e13,
            )
            if config.DRY_RUN:
                print('-- dry_run:', asset_name)
            else:
                task.start()
                TASKS.append(task)
                print('TASK SUBMITTED:', asset_name, task.status(), '\n')
    print('ALL TASKS SUBMITTED')
    return TASKS


###### Remove images
# image_ids = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/builtup_density_JRCs_checked_point_1980').filter(ee.Filter.eq('scale_factor_set', 'False')).aggregate_array('system:index').getInfo()
# image_ids = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/builtup_density_JRCs_checked_point_1980').filter(ee.Filter.stringContains('system:index', '13133')).aggregate_array('system:index').getInfo()
# image_ids = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/builtup_density_JRCs_africa_1980').filter(ee.Filter.stringContains('system:index', '3764')).aggregate_array('system:index').getInfo()
# image_ids = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/builtup_density_JRCs_africa_2010').filter(ee.Filter.eq('scale_factor_set', 'False')).aggregate_array('system:index').getInfo()

# len(image_ids)
# # Delete images
# for image_id in image_ids:
#     ee.data.deleteAsset('projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/builtup_density_JRCs_checked_point_1980/'+image_id)
#     # ee.data.deleteAsset('projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/builtup_density_JRCs_africa_1980/'+image_id)
#     print("Deleted:", image_id)


# image_ids = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/builtup_density_JRCs_50').filter(ee.Filter.eq('study_area_scale_factor', 320)).aggregate_array('system:index').getInfo()
# len(image_ids)



####### Scale factor check
def post_check_task_scale(TASKS, cities_track):
    for i in range(len(TASKS) - 1, -1, -1):
        cID = int(TASKS[i].status()['description'].split('-')[-2])
        if TASKS[i].status()['state']=='RUNNING':
            continue
        elif TASKS[i].status()['state']=='READY':
            continue
        elif TASKS[i].status()['state']=='FAILED':
            if cities_track.loc[cID, 'NO_RUNS'] < 1:    
                cities_track.loc[cID, 'NO_RUNS'] = cities_track.loc[cID, 'NO_RUNS'] + 1
                TASKS = TASKS + get_urban_extents(IDS, [cID], cities_track) 
                del TASKS[i]
            else:
                non_na_pixels = geelayers.BU_CONNECTED.reduceRegion(
                        reducer=ee.Reducer.count(),
                        geometry=ee.Feature(ee.FeatureCollection(geelayers.CITY_DATA_POLY).filter(ee.Filter.eq('ID_HDC_G0',cID)).first()).geometry(),
                        scale=100,
                        maxPixels=1e9
                    ).get('builtup')
                cities_track.loc[cID, 'NEED_CENTROID_CHECK'] = bool(ee.Number(non_na_pixels).gt(0).getInfo())
                # cities_track.loc[cID, 'NEED_CENTROID_CHECK'] = True
                del TASKS[i]
        elif TASKS[i].status()['state']=='COMPLETED':
            done_image_ids = ee.ImageCollection(config.IC_ID).filter(ee.Filter.eq('scale_factor_set', 'True')).aggregate_array('system:index').getInfo()
            if TASKS[i].status()['description'] not in done_image_ids:
                if cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] < 2560: 
                    ee.data.deleteAsset(config.IC_ID + '/' + TASKS[i].status()['description'])
                    cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] = cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] * 2
                    cities_track.loc[cID, 'NO_RUNS'] = 0
                    TASKS = TASKS + get_urban_extents(IDS, [cID], cities_track)
                    del TASKS[i]
                else:
                    city_point = ee.Feature(ee.FeatureCollection(geelayers.CITY_DATA_POINT).filter(ee.Filter.eq('ID_HDC_G0',cID)).first()) 
                    count_image = ee.ImageCollection(config.IC_ID).filterBounds(city_point.geometry()).aggregate_array('system:index').getInfo()
                    if len(count_image) > 1:
                        cities_track.loc[cID, 'DONE'] = True
                    else:
                        cities_track.loc[cID, 'NEED_MAP_CHECK'] = True
                    del TASKS[i]
            else:
                cities_track.loc[cID, 'DONE'] = True
                del TASKS[i]
    return TASKS, cities_track

import time
import pandas as pd

IDS = geelayers.CITY_DATA.sort('P15', False).aggregate_array('ID_HDC_G0').getInfo()
# FULL_IDS = geelayers.CITY_DATA_POINT.sort('P15', False).aggregate_array('ID_HDC_G0').getInfo()
cities_track = pd.read_csv('data/checked_cities_track_todo_2020.csv', encoding='latin1', low_memory=False)
cities_track.set_index('ID_HDC_G0', inplace=True)
# filter out checked cities
filtered_cities = cities_track[cities_track['NEED_CENTROID_CHECK']!=False]

total_mins = 0
TASKS = get_urban_extents(IDS, filtered_cities.index.tolist(), cities_track) 

while len(TASKS) > 0:
    if total_mins == 0:
        print('No of submitted tasks: ' + str(len(TASKS)))
    TASKS, cities_track = post_check_task_scale(TASKS, cities_track) ########post_check_task
    print('No of tasks to check: ' + str(len(TASKS)))
    print('No of tasks need centroid check: ' + str(cities_track['NEED_CENTROID_CHECK'].sum()))
    print('No of tasks need map check: ' + str(cities_track['NEED_MAP_CHECK'].sum()))
    print('Total waiting time: ' + str(total_mins) + ' mins')
    print('Check again in 20 secends...\n')
    time.sleep(1 * 20)
    total_mins = total_mins + 0.5
print('Success!')

cities_track.to_csv('data/checked_cities_track_todo_2020.csv', encoding='latin1')
