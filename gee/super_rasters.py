import os
import re
from unidecode import unidecode
import ee
# ee.Authenticate()
ee.Initialize()

import config
import cities
import geelayers
import helpers


# Create a function called get_super_feat
def get_urban_extents(IDS, CITIES_LIST):

    FAILURES = {}
    TASKS = []

    for i, ident in enumerate(IDS):
        # if i > 9706 and i < 9712:
        if ident in CITIES_LIST:
        # if ident == 3557:
            # get on city centroid feature
            feat = ee.Feature(geelayers.CITY_DATA.filter(ee.Filter.eq('ID_HDC_G0', ident)).first())
            
            # feat = feat.setGeometry(ee.Geometry.Point([85.297, 25.935]))
            # feat.geometry().getInfo()
            city_name = feat.getString('UC_NM_MN').getInfo()
            print(f'{i}: {city_name} [{ident}]')
            # get feature for city boundary as defined by vectorize function
            feat = ee.Feature(helpers.get_super_feat(feat))
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
                maxPixels=1e13,  # 1e11
            )
            if config.DRY_RUN:
                print('-- dry_run:', asset_name)
            else:
                try:
                    task.start()
                    TASKS.append(task)
                    print('TASK SUBMITTED:', asset_name, task.status(), '\n')
                except Exception as e:
                    print('\n'*1)
                    print('*'*100)
                    print('*'*100)
                    print('\n'*1)
                    print(f'CITY_NAME: {city_name}')
                    print(f'CITY_ID: {ident}')
                    print(f'ASSET_NAME: {asset_name}')
                    print(f'ERROR: {e}')
                    print('\n'*1)
                    print('*'*100)
                    print('*'*100)
                    print('\n'*1)
                    FAILURES[task.status()['description']] = 'Submission failed.'
    print('SUBMITTED')
    print('NB_ERRORS:', len(FAILURES))
    return TASKS, FAILURES


IDS = geelayers.CITY_DATA.sort('P15', False).aggregate_array('ID_HDC_G0').getInfo()
CITIES_LIST = cities.id_hdc_g0_250
TASKS, FAILURES = get_urban_extents(IDS, CITIES_LIST)


# post task check
print('Total tasks submitted: ' + str(len(TASKS)))
READY = 0
RUNNING = 0
COMPLETED = 0
FAILED = 0
CANCELLED = 0
for task in TASKS:
    if task.status()['state']=='COMPLETED':
        COMPLETED = COMPLETED + 1
    elif task.status()['state']=='RUNNING':
        RUNNING = RUNNING + 1
    elif task.status()['state']=='READY':
        READY = READY + 1
    elif 'CANCEL' in task.status()['state']:
        CANCELLED = CANCELLED + 1
    elif task.status()['state']=='FAILED':
        FAILED = FAILED + 1
        FAILURES[task.status()['description']] = task.status()['error_message']

if RUNNING > 0 or READY > 0:
    print('Still running for cities.')
print('READY tasks: '+ str(READY))
print('RUNNING tasks: '+ str(RUNNING))
print('CANCELED tasks: '+ str(CANCELLED))
print('COMPLETED tasks: '+ str(COMPLETED))
print('FALIED tasks: '+ str(FAILED))


direct_rerun = []
alt_center = []
other_issue = []
for key, value in FAILURES.items():
    # Check if value contains substring 'aaaa'
    if 'Computation timed out' in value:
        direct_rerun.append(key)
    # Check if value contains substring 'bbb'
    elif 'The geometry for image clipping must not be empty' in value:
        alt_center.append(key)
    else:
        other_issue.append(key)
        
direct_rerun_ids = [item.split('-')[1] for item in direct_rerun]
alt_center_ids = [item.split('-')[1] for item in alt_center]

# Print the lists of keys
print("direct_rerun: ", direct_rerun_ids)
print("alt_center: ", alt_center_ids)
