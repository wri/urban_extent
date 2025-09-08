import geelayers
import config
import ee
ee.Initialize()


#
# MAIN
#
def get_circle_data_simple(feat, city_track):
    feat = ee.Feature(feat)
    # cname = feat.get('UC_NM_MN')
    # cID = ee.Number(feat.get('ID_HDC_G0')).toInt()
    centroid = feat.geometry()
    crs = get_crs(centroid)
    region = ee.String(feat.get(config.CITY_REG_COL)).trim()
    pop = feat.getNumber(config.CITY_POP_COL)

    est_area = get_area(pop, region)
    est_influence_distance = get_influence_distance(est_area)

    scale_factor = float(city_track['STUDY_AREA_SCALE_FACTOR'])
    scaled_area = est_area.multiply(scale_factor)
    radius = get_radius(scaled_area)
    study_bounds = centroid.buffer(radius, config.MAX_ERR)

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
            'study_area_scale_factor': scale_factor,
            # 'use_center_of_mass': str(city_track['USE_COM']),
            # 'use_inspected_centroid': str(city_track['USE_INSPECTED_CENTROIDS']),
            'builtup_year': config.mapYear
        }).copyProperties(feat)


def vectorize(data):
    data = ee.Feature(data)
    study_area = data.geometry()
    bu_centroid = ee.Geometry(data.get('bu_city_center'))
    # create vectors from BU_CONNECTED image where it overlaps with city study_area
    feats = geelayers.BU_CONNECTED.reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        crs=geelayers.GHSL_CRS,
        crsTransform=geelayers.GHSL_TRANSFORM,
        geometry=study_area,
        maxPixels=1e13,
        bestEffort=True
    )
    centroid_filter = ee.Filter.withinDistance(
        distance=config.CENTROID_SEARCH_RADIUS,
        leftField='.geo',
        rightValue=bu_centroid,
        maxError=config.MAX_ERR
    )
    # flatten multipolygons to polygons and fill holes in vector polygons
    feats = flatten_to_polygons(feats).map(fill_polygon)
    # buffer each vector feature by its influence distance (function of its area)
    feats = ee.FeatureCollection(feats.map(buffered_feat))
    # dissolve all vectors to merge overlapping influence area features
    geoms = feats.geometry(config.MAX_ERR).dissolve(config.MAX_ERR).geometries()
    feats = ee.FeatureCollection(geoms.map(geom_feat))
    # filter to retain only merged vector features that are within CENTROID_SEARCH_RADIUS of bu_centroid
    feats = feats.filter(centroid_filter)
    # fill holes in vector polygons
    feats = fill_polygons(feats)
    # return vector polygons as a single feature
    return ee.Feature(feats).copyProperties(data)


#
# FLATTEN FEATURES TO POLYGONS
#
def _filter_and_geom_type(f, valid_check):
    return ee.Algorithms.If(valid_check(f), _geom_type(f), None)


def _geom_type(f):
    return ee.Feature(f).set({'geomType': f.geometry().type()})


def fill_polygon(feat):
    geom = ee.Feature(feat).geometry()
    return feat.setGeometry(ee.Geometry.Polygon(geom.coordinates().get(0)))


def flatten_to_polygons(feats, valid_check=None):
    feats = ee.FeatureCollection(feats)
    feats = feats.map(_geom_type)
    gc_filter = ee.Filter.eq('geomType', 'GeometryCollection')
    mpoly_filter = ee.Filter.eq('geomType', 'MultiPolygon')
    gc_data = feats.filter(gc_filter).map(flatten_geometry_collection).flatten()
    mpoly_data = feats.filter(mpoly_filter).map(flatten_multipolygon).flatten()
    feats = feats.filter(ee.Filter.Or(gc_filter, mpoly_filter).Not()).merge(gc_data).merge(mpoly_data)
    if valid_check is None:
        feats = feats.map(_geom_type)
    else:
        feats = feats.map(lambda f: _filter_and_geom_type(f, valid_check), True)
    return feats.filter(ee.Filter.eq('geomType', 'Polygon'))


#
# FILL POLYGONS
#
def fill_polygons(feats):
    feats = flatten_to_polygons(feats).map(fill_polygon)
    return feats.geometry().dissolve()


#
# HELPERS
#
def get_area(pop, region):
    pop = ee.Number(pop).log()
    params = ee.Dictionary(config.FIT_PARAMS.get(region))
    slope = params.getNumber('slope')
    intercept = params.getNumber('intercept')
    log_area = slope.multiply(pop).add(intercept)
    return log_area.exp()


def get_radius(area):
    return ee.Number(area).divide(config.PI).sqrt()


def nearest_non_null(centroid):
    distance_im = ee.FeatureCollection([centroid]).distance(config.MAX_NNN_DISTANCE)
    bounds = ee.Geometry.Point(centroid.coordinates()).buffer(
        config.MAX_NNN_DISTANCE, config.MAX_ERR)
    nearest = distance_im.addBands(ee.Image.pixelLonLat()).updateMask(geelayers.BU).reduceRegion(
        reducer=ee.Reducer.min(3),
        geometry=bounds,
        crs=geelayers.GHSL_CRS,
        crsTransform=geelayers.GHSL_TRANSFORM
    )
    return [nearest.getNumber('min1'), nearest.getNumber('min2')]


def get_com(geom):
    pts = geelayers.BU_LATLON.sample(
        region=geom,
        scale=10,
        numPixels=config.NB_COM_SAMPLES,
        seed=config.COM_SEED,
        dropNulls=True,
        geometries=False
    )
    return ee.Algorithms.If(
        pts.size(),
        ee.Geometry.Point([
            pts.aggregate_mean('longitude'),
            pts.aggregate_mean('latitude')]),
        geom.centroid(10)
    )


def get_crs(point):
    coords = point.coordinates()
    lon = ee.Number(coords.get(0))
    lat = ee.Number(coords.get(1))
    zone = ee.Number(32700).subtract((lat.add(45).divide(90)).round().multiply(
        100)).add(((lon.add(183)).divide(6)).round())
    zone = zone.toInt().format()
    return ee.String('EPSG:').cat(zone)


def get_influence_distance(area):
    return ee.Number(area).sqrt().multiply(config.GROWTH_RATE)


def geom_feat(g):
    return ee.Feature(ee.Geometry(g))


def coords_feat(coords):
    return ee.Feature(ee.Geometry.Polygon(coords))


def flatten_geometry_collection(feat):
    feat = ee.Feature(feat)
    geoms = feat.geometry().geometries()
    return ee.FeatureCollection(geoms.map(geom_feat))


def flatten_multipolygon(feat):
    coords_list = ee.Feature(feat).geometry().coordinates()
    return ee.FeatureCollection(coords_list.map(coords_feat))


def buffered_feat(feat):
    feat = ee.Feature(feat)
    area = feat.area(config.MAX_ERR)
    return buffered_feat_area(feat, area)


def buffered_feat_area(feat, area):
    area = ee.Number(area)
    infl = get_influence_distance(area)
    return feat.buffer(infl, config.MAX_ERR).set('buffer', infl)


def buffered_feat_circle(image):
    # Create the point geometry from the latitude and longitude
    point = ee.Geometry.Point([image.get('study_center_lon'), image.get('study_center_lat')])
    # Create the circle buffer around the point with the specified radius
    circle = point.buffer(ee.Number(image.get('study_radius')))
    # Copy all the properties from the original feature
    circle = ee.Feature(circle, image.toDictionary())

    return circle
