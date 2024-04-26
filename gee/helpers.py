import ee
ee.Initialize()

import config
import geelayers

#
# MAIN
#
def get_circle_data(feat):
    feat = ee.Feature(feat)
    cname = feat.get('UC_NM_MN')
    cID = ee.Number(feat.get('ID_HDC_G0')).toInt()
    centroid = feat.geometry()
    crs = get_crs(centroid)
    region = ee.String(feat.get('GRGN_L2')).trim()
    pop = feat.getNumber('P15')
    est_area = get_area(pop, region)
    est_influence_distance = get_influence_distance(est_area)
    scaled_area = est_area.multiply(config.STUDY_AREA_SCALE_FACTOR)
    radius = get_radius(scaled_area)
    study_bounds = centroid.buffer(radius, config.MAX_ERR)
    if config.USE_COM:
        center_of_mass = ee.Geometry(get_com(study_bounds))
        bu_centroid_xy = ee.List(nearest_non_null(center_of_mass))
        study_bounds = center_of_mass.buffer(radius, config.MAX_ERR)
        study_center = center_of_mass
    elif config.USE_INSPECTED_CENTROIDS:
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
            'study_area_scale_factor': config.STUDY_AREA_SCALE_FACTOR,
            'use_center_of_mass': str(config.USE_COM),
            'use_inspected_centroid': str(config.USE_INSPECTED_CENTROIDS),
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
    return ee.Feature(feats.geometry()).copyProperties(data)


# def get_super_feat(feat):
#     feat = get_circle_data(feat)
#     feat = vectorize(feat)
#     return feat


# #
# # ESTIMATED GROWTH BUFFER
# #
# def _get_beta(rho,alpha,delta):
#     num=ee.Number(rho).multiply(ee.Number(alpha).sqrt().subtract(1))
#     return ee.Number(2).multiply(delta).divide(num)


# def growth_buffer(geom,target_frac,overshoot):
#     geom=ee.Geometry(geom)
#     overshoot=overshoot or 0
#     alpha=ee.Number(target_frac).add(1).add(overshoot)
#     a0=geom.area(config.MAX_ERR)
#     p0=geom.perimeter(config.MAX_ERR)
#     # compute rho=area/perimeter
#     rho0=a0.divide(p0)
#     # buffer to give alpha if circle
#     bC=alpha.sqrt().subtract(1).multiply(rho0)
#     # buffer geom by and calculate delta=rho(after buffer)/rho(init)
#     geomC=geom.buffer(bC)
#     aC=geomC.area(1)
#     pC=geomC.perimeter(1)
#     rhoC=aC.divide(pC)
#     deltaC=rhoC.subtract(rho0)
#     #
#     alphaC=aC.divide(a0)
#     beta=_get_beta(rho0,alphaC,deltaC)
#     # compute delta (this gives the change in terms of rho)
#     deltaT=rho0.multiply(beta).multiply(alpha.sqrt().subtract(1)).divide(2)
#     # convert change in terms of rho back to a "buffer"
#     # - this assumes bC is close to right and changes slowly
#     bT=deltaT.multiply(bC).divide(deltaC)
#     return bT


#
# FLATTEN FEATURES TO POLYGONS
#
def _filter_and_geom_type(f, valid_check):
    return ee.Algorithms.If(valid_check(f), _geom_type(f), None)


def _geom_type(f):
    return ee.Feature(f).set({'geomType': f.geometry().type()})


def flatten_geometry_collection(feat):
    feat = ee.Feature(feat)
    geom = feat.geometry()
    return ee.FeatureCollection(geom.geometries().map(lambda g: feat.setGeometry(g)))


def flatten_multipolygon(feat):
    geom = ee.Feature(feat).geometry()
    return ee.FeatureCollection(geom.coordinates().map(lambda coords: ee.Feature(ee.Geometry.Polygon(coords))))


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


def fill_holes_ALGO(feat, max_fill):
    def _filler(coords):
        poly = ee.Geometry.Polygon(coords)
        return ee.Algorithms.If(poly.area(config.MAX_ERR).gt(max_fill), coords)
    feat = ee.Feature(feat)
    ncoords = feat.geometry().coordinates().map(_filler, True)
    return ee.Algorithms.If(ncoords.size(), feat.setGeometry(ee.Geometry.Polygon(ncoords)))


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


def polygon_feat_boundry(feat):
    feat = ee.Feature(feat)
    geom = ee.Geometry.Polygon(feat.geometry().coordinates().get(0))
    return ee.Feature(geom)


def set_geom_type(feat):
    feat = ee.Feature(feat)
    return feat.set('geomType', feat.geometry().type())


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


def buffered_feat(feat):
    feat = ee.Feature(feat)
    area = feat.area(config.MAX_ERR)
    return buffered_feat_area(feat, area)


def buffered_feat_area(feat, area):
    feat = ee.Feature(feat)
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
