import os
import re
from unidecode import unidecode
import ee
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

    print('COMPLETE')
    print('NB_ERRORS:', len(FAILURES))
    return TASKS, FAILURES


IDS = geelayers.CITY_DATA.sort('P15', False).aggregate_array('ID_HDC_G0').getInfo()
CITIES_LIST = cities.id_hdc_g0_50
TASKS, FAILURES = get_urban_extents(IDS, CITIES_LIST)

for task in TASKS:
    print(task.status())
    if task.status()['state']=='FAILED':
        FAILURES[task.status()['description']] = task.status()['error_message']
