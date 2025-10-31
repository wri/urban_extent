import time
import pandas as pd
import re
import ee
from unidecode import unidecode

import helpers
import geelayers
import config


# ee.Authenticate(force=True)
ee.Initialize()

# Create a function called get_super_feat
def get_urban_extents(IDS, CITIES_LIST, cities_track):
    TASKS = []

    for i, ident in enumerate(IDS):
        if ident in CITIES_LIST:
            # get on city centroid feature
            feat = ee.Feature(config.CITY_DATA_POINT.filter(ee.Filter.eq(config.CITY_ID_COL, ident)).first())
            # feat.getInfo()
            city_name = feat.getString(config.CITY_NAME_COL).slice(0, 80).getInfo()
            print(f'{i}: {city_name} [{ident}]')
            # get feature for city boundary as defined by vectorize function
            # feat = ee.Feature(helpers.get_super_feat(feat))
            city_track = cities_track.loc[ident]
            circle_feat = helpers.get_circle_data_simple(feat, city_track)  # get_circle_data
            feat = helpers.vectorize(circle_feat)
            feat = feat.set({'scale_factor_set': ee.Algorithms.If(ee.Feature(circle_feat).contains(ee.Feature(feat)), 'True', 'False')})
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
    if len(TASKS) > 1:
        print('ALL TASKS SUBMITTED')
    return TASKS


###### Scale factor check
def post_check_task_scale(TASKS, cities_track):
    complete_tasks = []
    failed_tasks = []
    for i in range(len(TASKS) - 1, -1, -1):
        cID = int(TASKS[i].status()['description'].split('-')[-2])
        if TASKS[i].status()['state'] == 'RUNNING':
            continue
        elif TASKS[i].status()['state'] == 'READY':
            continue
        elif TASKS[i].status()['state'] == 'FAILED':
            if cities_track.loc[cID, 'NO_RUNS'] < 1:
                cities_track.loc[cID, 'NO_RUNS'] = cities_track.loc[cID, 'NO_RUNS'] + 1
                TASKS = TASKS + get_urban_extents(IDS, [cID], cities_track)
                del TASKS[i]
            else:
                failed_tasks.append(TASKS[i])
                del TASKS[i]
        elif TASKS[i].status()['state'] == 'COMPLETED':
            complete_tasks.append(TASKS[i])
            del TASKS[i]

   # Check if scale factor is set for COMPLETED cities
    done_image_ids = ee.ImageCollection(config.IC_ID).filter(ee.Filter.eq('scale_factor_set', 'True')).aggregate_array('system:index').getInfo()
    for task in complete_tasks:
        cID = int(task.status()['description'].split('-')[-2])
        if task.status()['description'] not in done_image_ids:
            if cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] < 10000:
                ee.data.deleteAsset(config.IC_ID + '/' + task.status()['description'])
                cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] = round(cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] * 2)
                cities_track.loc[cID, 'NO_RUNS'] = 0
                TASKS = TASKS + get_urban_extents(IDS, [cID], cities_track)
            else:
                city_point = ee.Feature(ee.FeatureCollection(config.CITY_DATA_POINT).filter(ee.Filter.eq(config.CITY_ID_COL, cID)).first())
                count_image = ee.ImageCollection(config.IC_ID).filterBounds(city_point.geometry()).aggregate_array('system:index').getInfo()
                if len(count_image) > 1:
                    cities_track.loc[cID, 'DONE'] = True
                else:
                    cities_track.loc[cID, 'NEED_MAP_CHECK'] = True
        else:
            cities_track.loc[cID, 'DONE'] = True

    # Determine if need centroid check for failed tasks
    cIDs = [int(t.status()['description'].split('-')[-2])
            for t in failed_tasks]
    cIDs = list(set(cIDs))
    points_fc = ee.FeatureCollection(config.CITY_DATA_POINT).filter(ee.Filter.inList(config.CITY_ID_COL, cIDs))
    points_buffer = points_fc.map(lambda f: f.buffer(1800))

    # Count built‐up pixels in one go
    non_na_pixels = geelayers.BU_CONNECTED.select('builtup').reduceRegions(
        collection=points_buffer,
        reducer=ee.Reducer.count(),
        scale=100
    )

    results = non_na_pixels.getInfo()['features']
    for feat in results:
        props = feat['properties']
        cID = int(props[config.CITY_ID_COL])
        count = int(props.get('count', 0))
        cities_track.loc[cID, 'NEED_CENTROID_CHECK'] = bool(count > 10)
        if not bool(count > 10):
            cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] = 4

        # if cities_track.loc[cID, 'NEED_CENTROID_CHECK']:
        #     cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] = round(cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] / 2)
        #     if cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] >= 4:
        #         get_urban_extents(IDS, [cID], cities_track)
        #         cities_track.loc[cID, 'NEED_MAP_CHECK'] = True
        #         cities_track.loc[cID, 'DONE'] = False
        #     else:
        #         cities_track.loc[cID, 'STUDY_AREA_SCALE_FACTOR'] = 4

    return TASKS, cities_track


#
# RUN
#
IDS = geelayers.CITY_DATA.sort(config.CITY_POP_COL, False).aggregate_array(config.CITY_ID_COL).getInfo()
# FULL_IDS = config.CITY_DATA_POINT.sort(config.CITY_POP_COL, False).aggregate_array(config.CITY_ID_COL).getInfo()
cities_track = pd.read_csv(config.CITY_TRACKER, encoding='latin1', low_memory=False)
cities_track.set_index(config.CITY_ID_COL, inplace=True)

# filter out checked cities
filtered_cities = cities_track[(cities_track['NEED_CENTROID_CHECK'] != False) & (cities_track['NEED_CENTROID_CHECK'] != True) & (cities_track['DONE'] != True)]
# filtered_cities = cities_track[cities_track['NEED_MAP_CHECK']==True]
# filtered_cities = cities_track[cities_track['DONE']==False]
# filtered_cities = cities_track[(cities_track['STUDY_AREA_SCALE_FACTOR'] == 1) & (cities_track['DONE'] != True)]
# filtered_cities = cities_track[cities_track.index==12429]  # Atlanta

total_mins = 0
TASKS = get_urban_extents(IDS, filtered_cities.index.tolist(), cities_track)

while len(TASKS) > 0:
    if total_mins == 0:
        temp = len(TASKS)
        print('No of submitted tasks: ' + str(len(TASKS)))
    TASKS, cities_track = post_check_task_scale(TASKS, cities_track)  # post_check_task
    if len(TASKS) < temp:
        cities_track.to_csv(config.CITY_TRACKER, encoding='utf-8')
        temp = len(TASKS)
    print('No of tasks to check: ' + str(len(TASKS)))
    print('No of tasks need centroid check: ' + str(cities_track['NEED_CENTROID_CHECK'].sum()))
    print('No of tasks need map check: ' + str(cities_track['NEED_MAP_CHECK'].sum()))
    print('Total waiting time: ' + str(total_mins) + ' mins')
    print('Check again in 15 secends...\n')
    time.sleep(1 * 15)
    total_mins = round(total_mins + 0.25, 2)
print('Success!')

cities_track.to_csv(config.CITY_TRACKER, encoding='utf-8')
print('Number of cities in the centroid database: ' + str(ee.FeatureCollection(config.CITY_DATA_POINT).size().getInfo()))
print('Number of cities in the GEE collection: ' + str(ee.ImageCollection(config.IC_ID).size().getInfo()))


# # ###### Remove images
# image_ids = ee.ImageCollection(config.IC_ID).filter(ee.Filter.eq('scale_factor_set', 'False')).aggregate_array('system:index').getInfo()
# image_ids = ee.ImageCollection(config.IC_ID).filter(ee.Filter.stringContains('system:index', '7416')).aggregate_array('system:index').getInfo()
# image_ids = ee.ImageCollection(config.IC_ID).filter(ee.Filter.eq('ORIG_FID', 104253)).aggregate_array('system:index').getInfo()
# image_ids = ee.ImageCollection(config.IC_ID).filter(ee.Filter.gt('study_area_scale_factor', 20000)).aggregate_array('system:index').getInfo()

# print(image_ids)
# len(image_ids)
# # Delete images
# for image_id in image_ids:
#     ee.data.deleteAsset(config.IC_ID+'/'+image_id)
#     print("Deleted:", image_id)
