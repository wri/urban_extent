import ee
ee.Initialize()

import config
import geelayers


# MAIN

def get_circle_data(feat, city_track):
    feat = ee.Feature(feat)
    cname = feat.get('UC_NM_MN')
    cID = ee.Number(feat.get('ID_HDC_G0')).toInt()
    centroid = feat.geometry()
    crs = get_crs(centroid)
    region = ee.String(feat.get('GRGN_L2')).trim()
    pop = feat.getNumber('P15')
    est_area = get_area(pop, region)
    est_influence_distance = get_influence_distance(est_area)
    scaled_area = est_area.multiply(int(city_track['STUDY_AREA_SCALE_FACTOR']))
    radius = get_radius(scaled_area)
    study_bounds = centroid.buffer(radius, config.MAX_ERR)
    if city_track['USE_COM']:
        center_of_mass = ee.Geometry(get_com(study_bounds))
        bu_centroid_xy = ee.List(nearest_non_null(center_of_mass))
        study_bounds = center_of_mass.buffer(radius, config.MAX_ERR)
        study_center = center_of_mass
    elif city_track['USE_INSPECTED_CENTROIDS']:
        inspected_centroid = config.NEW_INSPECTED_CENTROIDS_IDS.get(cID)
        inspected_centroid = ee.Geometry(inspected_centroid)
        bu_centroid_xy = ee.List(nearest_non_null(inspected_centroid))
        study_bounds = inspected_centroid.buffer(radius, config.MAX_ERR)
        study_center = inspected_centroid
    else:
        bu_centroid_xy = ee.List(nearest_non_null(centroid))
        study_center = centroid
    bu_centroid = ee.Geometry.Point(bu_centroid_xy)
    return ee.Feature(
        study_bounds,
        {
            # 'city_center': centroid,
            'bu_city_center': bu_centroid,
            'bu_city_center_lon': bu_centroid.coordinates().get(0),
            'bu_city_center_lat': bu_centroid.coordinates().get(1),
            'crs': crs,
            'study_center': study_center,
            'study_center_lon': study_center.coordinates().get(0),
            'study_center_lat': study_center.coordinates().get(1),
            'est_area': est_area,
            'scaled_area': scaled_area,
            'study_radius': radius,
            'est_influence_distance': est_influence_distance,
            'study_area_scale_factor': int(city_track['STUDY_AREA_SCALE_FACTOR']),
            'use_center_of_mass': str(city_track['USE_COM']),
            'use_inspected_centroid': str(city_track['USE_INSPECTED_CENTROIDS']),
            'builtup_year': config.mapYear
        }).copyProperties(feat)
