import ee
ee.Initialize()

import config
import geelayers

##### helpers.py
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


def flatten_geometry_collection(feat):
    feat = ee.Feature(feat)
    geom = feat.geometry()
    return ee.FeatureCollection(geom.geometries().map(lambda g: feat.setGeometry(g)))


def flatten_multipolygon(feat):
    geom = ee.Feature(feat).geometry()
    return ee.FeatureCollection(geom.coordinates().map(lambda coords: ee.Feature(ee.Geometry.Polygon(coords))))


def set_geom_type(feat):
    feat = ee.Feature(feat)
    return feat.set('geomType', feat.geometry().type())


def polygon_feat_boundry(feat):
    feat = ee.Feature(feat)
    geom = ee.Geometry.Polygon(feat.geometry().coordinates().get(0))
    return ee.Feature(geom)


def fill_polygons(feats):
    feats = feats.map(set_geom_type)
    gc_filter = ee.Filter.eq('geomType', 'GeometryCollection')
    mpoly_filter = ee.Filter.eq('geomType', 'MultiPolygon')
    poly_filter = ee.Filter.eq('geomType', 'Polygon')
    gc_data = feats.filter(gc_filter).map(
        flatten_geometry_collection).flatten()
    mpoly_data = feats.filter(mpoly_filter).map(flatten_multipolygon).flatten()
    poly_data = feats.filter(poly_filter)
    feats = ee.FeatureCollection([
        poly_data,
        gc_data,
        mpoly_data]).flatten()
    feats = feats.map(set_geom_type).filter(poly_filter)
    feats = feats.map(polygon_feat_boundry)
    return feats


def fill_holes_ALGO(feat, max_fill):
    def _filler(coords):
        poly = ee.Geometry.Polygon(coords)
        return ee.Algorithms.If(poly.area(config.MAX_ERR).gt(max_fill), coords)
    feat = ee.Feature(feat)
    ncoords = feat.geometry().coordinates().map(_filler, True)
    return ee.Algorithms.If(ncoords.size(), feat.setGeometry(ee.Geometry.Polygon(ncoords)))


#  fixes for built-up excluded during hole filling

def add_coord_length(feat):
    feat = ee.Feature(feat)
    geom = feat.geometry()
    coord_length = geom.coordinates().size()
    return feat.set({
        'coord_length': coord_length
    })


def hole_filling_method(feats, max_fill):
    feats = feats.map(add_coord_length)
    flat_feats = feats.filter(ee.Filter.lte('coord_length', 1))
    complex_feats = feats  # .filter(ee.Filter.gt('coord_length',1))

    def fill_small(feat):
        return fill_holes(feat, max_fill)
    complex_feats = complex_feats.map(fill_small)
    feats = ee.FeatureCollection([
        #    flat_feats,
        complex_feats
    ]).flatten()
    return feats


def flatten_to_polygons_and_fill_holes(feats, max_fill):
    feats = ee.FeatureCollection(feats)
    feats = feats.map(_geom_type)
    gc_filter = ee.Filter.eq('geomType', 'GeometryCollection')
    mpoly_filter = ee.Filter.eq('geomType', 'MultiPolygon')
    other_filter = ee.Filter.Or(gc_filter, mpoly_filter).Not()
    gc_data = feats.filter(gc_filter).map(flatten_geometry_collection).flatten()
    mpoly_data = feats.filter(mpoly_filter).map(flatten_multipolygon).flatten()
    other_data = feats.filter(other_filter)

    gc_data = hole_filling_method(gc_data, max_fill)
    mpoly_data = hole_filling_method(mpoly_data, max_fill)
    other_data = hole_filling_method(other_data, max_fill)

    feats = other_data.merge(gc_data).merge(mpoly_data)
    return feats


def fill_holes(feat, max_fill):
    coords_list = feat.geometry().coordinates()
    outer = coords_list.slice(0, 1)
    inner = coords_list.slice(1)

    def _coords_feat(coords):
        poly = ee.Geometry.Polygon(coords)
        return ee.Feature(poly, {
            'area': poly.area(config.MAX_ERR),
            'coords': coords
        })
    coords_fc = ee.FeatureCollection(inner.map(_coords_feat))
    coords_fc = coords_fc.filter(ee.Filter.gte('area', max_fill))

    def _get_coords(feat):
        return ee.Feature(feat).get('coords')
    coords_list = coords_fc.toList(coords_fc.size().add(1)).map(_get_coords)
    coords_list = outer.cat(coords_list)
    return feat.setGeometry(ee.Geometry.Polygon(coords_list))


##### urban_extents_from_super_rasters.py


# ROOT= 'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Mar2025'
# # 'projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024' #'users/emackres'
# SUFFIX= 'JRCs' #'GHSL_BUthresh10pct' #'Kigali_GHSL_GHSLthresh10pct' #'GHSL_GHSLthresh10pct' #'GHSL_GHSLthresh5pct' #'WSFevo' 'GHSL2023_2015'  'WSFevo_2015' 'GHSL_WSFunion_2015'
# SR_ID=f'{ROOT}/builtup_density_{SUFFIX}_{config.mapYear}'


# DEST_NAME=f'{SUFFIX}_{config.mapYear}'#_{REGION_SHORT}'
# DEST_NAME=f'{SUFFIX}'#_{YEAR}'

# #
# # HELPERS
# #
# def get_influence_distance(area):
#   return ee.Number(area).sqrt().multiply(GROWTH_RATE)


# def fill_small(feat):
#   return h.fill_holes(feat,MAX_FILL)


#
# MAIN
#
# def add_coord_length(feat):
#   feat=ee.Feature(feat)
#   geom=feat.geometry()
#   coord_length=geom.coordinates().size()
#   geom_type=geom.type()
#   return feat.set({
#       'coord_length': coord_length
#     })


#
# EXPORT
#
# name=DEST_NAME
# count=SUPER_IC.size()
# split_pos=count.divide(2).toInt()
# limit_pos=count.subtract(LIMIT)

# if SPLIT_INDEX is not False:
#   name=f'{name}_split{SPLIT_INDEX}'
#   if SPLIT_INDEX==1:
#     SUPER_IC=SUPER_IC.limit(count.subtract(split_pos),'City__Name',False)  
#   else:
#     SUPER_IC=SUPER_IC.limit(split_pos,'City__Name',True)  


# if TEST_CITY:
#   name=f'TESTER_{TEST_CITY}'
#   SUPER_IC=SUPER_IC.filter(ee.Filter.eq('City__Name',TEST_CITY))
# else:
#   if LIMIT:
#     SUPER_IC=SUPER_IC.limit(LIMIT,'Pop_2010',False)#.filter(ee.Filter.inList('City__Name',['Shanghai, Shanghai']))
#     name=f'{name}-lim{LIMIT}'
#     # SUPER_IC=SUPER_IC.limit(limit_pos,'Pop_2010',True).sort('system:asset_size')
#     # name=f'{name}-lim{LIMIT}remainder'
#   else:
#     SUPER_IC=SUPER_IC.sort('Pop_2010')


# if VECTOR_BUFFER:
#   name=f'{name}-b{VECTOR_BUFFER}'
# if VECTOR_SCALE:
#   name=f'{name}-vs{VECTOR_SCALE}'
# if RASTER_BUFFER:
#   name=f'{name}-rb{RASTER_BUFFER}-smask'
