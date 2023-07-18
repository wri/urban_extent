import ee
from pprint import pprint

MAX_ERR=1

#
# ESTIMATED GROWTH BUFFER
#
def _get_beta(rho,alpha,delta):
    num=ee.Number(rho).multiply(ee.Number(alpha).sqrt().subtract(1))
    return ee.Number(2).multiply(delta).divide(num)


def growth_buffer(geom,target_frac,overshoot):
    geom=ee.Geometry(geom)
    overshoot=overshoot or 0
    alpha=ee.Number(target_frac).add(1).add(overshoot)
    a0=geom.area(MAX_ERR)
    p0=geom.perimeter(MAX_ERR)
    # compute rho=area/perimeter 
    rho0=a0.divide(p0)
    # buffer to give alpha if circle 
    bC=alpha.sqrt().subtract(1).multiply(rho0)
    # buffer geom by and calculate delta=rho(after buffer)/rho(init)
    geomC=geom.buffer(bC)
    aC=geomC.area(1)
    pC=geomC.perimeter(1)
    rhoC=aC.divide(pC)
    deltaC=rhoC.subtract(rho0)
    # 
    alphaC=aC.divide(a0)
    beta=_get_beta(rho0,alphaC,deltaC)
    # compute delta (this gives the change in terms of rho)
    deltaT=rho0.multiply(beta).multiply(alpha.sqrt().subtract(1)).divide(2)
    # convert change in terms of rho back to a "buffer" 
    # - this assumes bC is close to right and changes slowly
    bT=deltaT.multiply(bC).divide(deltaC)
    return bT



#
# FLATTEN FEATURES TO POLYGONS
#
def _filter_and_geom_type(f,valid_check):
    return ee.Algorithms.If(valid_check(f),_geom_type(f),None)


def _geom_type(f):
    return ee.Feature(f).set({ 'geomType': f.geometry().type() })


def flatten_geometry_collection(feat):
    feat=ee.Feature(feat)
    geom=feat.geometry()
    return ee.FeatureCollection(geom.geometries().map(lambda g: feat.setGeometry(g)))


def flatten_multipolygon(feat):
    geom=ee.Feature(feat).geometry()
    return ee.FeatureCollection(geom.coordinates().map(lambda coords: ee.Feature(ee.Geometry.Polygon(coords))))


def fill_polygon(feat):
    geom=ee.Feature(feat).geometry()
    return f.setGeometry(ee.Geometry.Polygon(geom.coordinates().get(0)))


def flatten_to_polygons(feats,valid_check=None):
    feats=ee.FeatureCollection(feats)
    feats=feats.map(_geom_type)
    gc_filter=ee.Filter.eq('geomType', 'GeometryCollection')
    mpoly_filter=ee.Filter.eq('geomType', 'MultiPolygon')
    gc_data = feats.filter(gc_filter).map(flatten_geometry_collection).flatten()
    mpoly_data = feats.filter(mpoly_filter).map(flatten_multipolygon).flatten()
    feats=feats.filter(ee.Filter.Or(gc_filter,mpoly_filter).Not()).merge(gc_data).merge(mpoly_data)
    if valid_check is None:
        feats=feats.map(_geom_type)
    else:
        feats=feats.map(lambda f: _filter_and_geom_type(f,valid_check),True)
    return feats.filter(ee.Filter.eq('geomType', 'Polygon'))



#
# FILL POLYGONS
#
def fill_polygons(feats):
    feats=flatten_to_polygons(feats).map(fill_polygon)
    return feats.geometry().dissolve()


def fill_holes_ALGO(feat,max_fill):
    def _filler(coords):
        poly=ee.Geometry.Polygon(coords)
        return ee.Algorithms.If(poly.area(MAX_ERR).gt(max_fill),coords)
    feat=ee.Feature(feat)
    ncoords=feat.geometry().coordinates().map(_filler,True)
    return ee.Algorithms.If( ncoords.size(),feat.setGeometry(ee.Geometry.Polygon(ncoords)) )



def fill_holes(feat,max_fill):
    coords_list=feat.geometry().coordinates()
    outer=coords_list.slice(0,1)
    inner=coords_list.slice(1)
    def _coords_feat(coords):
        poly=ee.Geometry.Polygon(coords)
        return ee.Feature(poly,{
            'area':poly.area(MAX_ERR),
            'coords': coords
        })
    coords_fc=ee.FeatureCollection(inner.map(_coords_feat))
    coords_fc=coords_fc.filter(ee.Filter.gte('area',max_fill))
    def _get_coords(feat):
        return ee.Feature(feat).get('coords')
    coords_list=coords_fc.toList(coords_fc.size().add(1)).map(_get_coords)
    coords_list=outer.cat(coords_list)
    return feat.setGeometry(ee.Geometry.Polygon(coords_list))


#  fixes for built-up excluded during hole filling

def add_coord_length(feat):
  feat=ee.Feature(feat)
  geom=feat.geometry()
  coord_length=geom.coordinates().size()
  return feat.set({
      'coord_length': coord_length
    })

def hole_filling_method(feats,max_fill):
    feats=feats.map(add_coord_length)
    flat_feats=feats.filter(ee.Filter.lte('coord_length',1))
    complex_feats=feats#.filter(ee.Filter.gt('coord_length',1))
    def fill_small(feat):
        return fill_holes(feat,max_fill)
    complex_feats=complex_feats.map(fill_small)
    feats=ee.FeatureCollection([
    #    flat_feats,
       complex_feats
    ]).flatten()  
    return feats  

def flatten_to_polygons_and_fill_holes(feats,max_fill):
    feats=ee.FeatureCollection(feats)
    feats=feats.map(_geom_type)
    gc_filter=ee.Filter.eq('geomType', 'GeometryCollection')
    mpoly_filter=ee.Filter.eq('geomType', 'MultiPolygon')
    other_filter=ee.Filter.Or(gc_filter,mpoly_filter).Not()
    gc_data = feats.filter(gc_filter).map(flatten_geometry_collection).flatten()
    mpoly_data = feats.filter(mpoly_filter).map(flatten_multipolygon).flatten()
    other_data = feats.filter(other_filter)

    gc_data=hole_filling_method(gc_data,max_fill)
    mpoly_data=hole_filling_method(mpoly_data,max_fill)
    other_data=hole_filling_method(other_data,max_fill)

    feats=other_data.merge(gc_data).merge(mpoly_data)
    return feats














