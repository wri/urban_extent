from collections import defaultdict
import ee
import geemap
import networkx as nx

# ee.Authenticate()
ee.Initialize()

scale = 100

YEARS = [1980, 1990, 2000, 2005, 2010, 2015, 2020]
REF_YEAR = 2020

urbext_ref = ee.FeatureCollection(f'projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/GHSL_BUthresh10pct_JRCs_africa_{REF_YEAR}')
urbext_data_ref = geemap.ee_to_df(urbext_ref)
#Create overlap graph
nodes = []
for i in range(len(urbext_data_ref)):
    ua = urbext_data_ref.iloc[i]
    nodes.append(ua['ID_HDC_G0'])
print('nodes complete')
edges = []
for i in range(len(urbext_data_ref)):
    ua = urbext_data_ref.iloc[i]
    ua_f = urbext_ref.filter(ee.Filter.eq('ID_HDC_G0', int(ua['ID_HDC_G0']))).first()
    intersects_fc = urbext_ref.filter(ee.Filter.intersects('.geo', ua_f.geometry()))
    ids = intersects_fc.aggregate_array('ID_HDC_G0').getInfo()
    for c_id in ids:
        edges.append((ua['ID_HDC_G0'], c_id))
    print(i, end=' ')
G = nx.Graph()
G.add_nodes_from(nodes)
G.add_edges_from(edges)

# Find the various connected components -- sets of nodes joined by overlaps
components_ref = list(nx.connected_components(G))
component_lists_ref = [[int(j) for j in list(i)] for i in components_ref]
for i in range(len(component_lists_ref)):
    component_lists_ref[i].sort()
print('\n\nDone building reference ID list\n')

for year in YEARS:
    urbext_year = ee.FeatureCollection(f'projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/GHSL_BUthresh10pct_JRCs_africa_{year}')
    urbext_data_year = geemap.ee_to_df(urbext_year)
    #Create overlap graph
    nodes = []
    for i in range(len(urbext_data_year)):
        ua = urbext_data_year.iloc[i]
        nodes.append(ua['ID_HDC_G0'])
    print(f'nodes complete for {year}')
    edges = []
    for i in range(len(urbext_data_year)):
        ua = urbext_data_year.iloc[i]
        ua_f = urbext_year.filter(ee.Filter.eq('ID_HDC_G0', int(ua['ID_HDC_G0']))).first()
        intersects_fc = urbext_year.filter(ee.Filter.intersects('.geo', ua_f.geometry()))
        ids = intersects_fc.aggregate_array('ID_HDC_G0').getInfo()
        for c_id in ids:
            edges.append((ua['ID_HDC_G0'], c_id))
        if i % 50 == 0:
            print(i, end=' ')
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # Find the various connected components -- sets of nodes joined by overlaps
    components = list(nx.connected_components(G))
    component_lists = [[int(j) for j in list(i)] for i in components]
    for i in range(len(component_lists)):
        component_lists[i].sort()

    def makeFeature(idlist, ref_idstring, ref_year):
        idstring = '_'.join([str(i) for i in idlist])
        old_features = urbext_year.filter(ee.Filter.inList('ID_HDC_G0', ee.List(idlist)))
        def getFeatureString(features, varname):
            result_list = features.aggregate_array(varname).getInfo()
            result_list = list(set(result_list))
            result_list.sort()
            return '_'.join(result_list)
        namestring = getFeatureString(old_features, 'UC_NM_MN')
        countryisostring = getFeatureString(old_features, 'CTR_MN_ISO')
        countrynamestring = getFeatureString(old_features, 'CTR_MN_NM')
        region2string = getFeatureString(old_features, 'GRGN_L2')
        region1string = getFeatureString(old_features, 'GRGN_L1')
        return idstring, ee.Feature(old_features.geometry().dissolve(), ee.Dictionary({'city_ids': idstring, 'year': year, 'city_name': namestring, 'country_ISO': countryisostring, 'country_name': countrynamestring, 'region2': region2string, 'region1': region1string, 'reference_idstring': ref_idstring, 'reference_year': ref_year}))

    # Store new features in dict, keyed by idstring
    new_features_dict = defaultdict(list)
    for idx, idlist in enumerate(component_lists):
        founds = []
        for c_idx in range(len(component_lists_ref)):
            for idd in idlist:
                if idd in component_lists_ref[c_idx]:
                    founds.append(c_idx)
        founds = list(set(founds))
        founds.sort()
        ref_idstrings = []
        for i in founds:
            ref_idstrings.append('_'.join([str(j) for j in component_lists_ref[i]]))
        ref_idstring = '__'.join(ref_idstrings)
        
        idstring, nf = makeFeature(idlist, ref_idstring, REF_YEAR)
        new_features_dict[idstring].append(nf)
        if idx % 50 == 0:
            print(idx, end=' ')

    # Merge features w same idstring into multipolygon features
    new_features_list = []
    for idstring in new_features_dict:
        nf = ee.FeatureCollection(new_features_dict[idstring]).union().first()
        nf = nf.copyProperties(new_features_dict[idstring][0])
        new_features_list.append(nf)

    nf_year = ee.FeatureCollection(new_features_list)

    exportTask = ee.batch.Export.table.toAsset(
        collection = nf_year,
        description = f'urbext_unions_{year}',
        assetId = f'projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/urbanextents_unions_{year}'
    )
    exportTask.start()