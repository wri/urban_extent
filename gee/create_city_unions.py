from collections import defaultdict
import ee
import geemap
import numpy as np
import networkx as nx
import math

# ee.Authenticate()
ee.Initialize()

scale = 100

YEARS = [1980, 1990, 2000, 2010, 2020]
REF_YEAR = 2020
INPUT_SUFFIX = ""

urbext_ref = ee.FeatureCollection(f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/GHSL_BUthresh10pct_JRCs_{REF_YEAR}{INPUT_SUFFIX}')
# projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/GHSL_BUthresh10pct_JRCs_africa_{REF_YEAR}
urbext_data_ref = geemap.ee_to_df(urbext_ref)
# Create overlap graph
nodes = []
for i in range(len(urbext_data_ref)):
    ua = urbext_data_ref.iloc[i]
    nodes.append(ua['ORIG_FID'])
print('nodes complete')
edges = []
for i in range(len(urbext_data_ref)):
    ua = urbext_data_ref.iloc[i]
    ua_f = urbext_ref.filter(ee.Filter.eq('ORIG_FID', int(ua['ORIG_FID']))).first()
    intersects_fc = urbext_ref.filter(ee.Filter.intersects('.geo', ua_f.geometry()))
    ids = intersects_fc.aggregate_array('ORIG_FID').getInfo()
    for c_id in ids:
        edges.append((ua['ORIG_FID'], c_id))
    if i % 100 == 0:
        print(i, end=' ', flush=True)
G = nx.Graph()
G.add_nodes_from(nodes)
G.add_edges_from(edges)

# Find the various connected components -- sets of nodes joined by overlaps
components_ref = list(nx.connected_components(G))
component_lists_ref = [[int(j) for j in list(i)] for i in components_ref]
for i in range(len(component_lists_ref)):
    component_lists_ref[i].sort()
print('\n\nDone building reference ID list\n')

geoscheme = {}
with open('un_geoscheme.csv', 'r') as ifile:
    lines = ifile.readlines()
for line in lines:
    items = [i.strip() for i in line.split(',')]
    iso = items[5]
    geoscheme[iso] = {}
    geoscheme[iso]["ungeo_1"] = items[0]
    if items[1]:
        geoscheme[iso]["ungeo_2"] = items[1]
    else:
        geoscheme[iso]["ungeo_2"] = 'N/A'
    if items[2]:
        geoscheme[iso]["ungeo_3"] = items[2]
    else:
        geoscheme[iso]["ungeo_3"] = 'N/A'
    geoscheme[iso]['ungeo_LDC'] = 'LDC' in items[3:5]
    geoscheme[iso]['ungeo_LLDC'] = 'LLDC' in items[3:5]
    geoscheme[iso]['ungeo_SIDS'] = 'SIDS' in items[3:5]

for year in YEARS:
    urbext_year = ee.FeatureCollection(f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/GHSL_BUthresh10pct_JRCs_{year}{INPUT_SUFFIX}')
    urbext_data_year = geemap.ee_to_df(urbext_year)
    # Create overlap graph
    nodes = []
    for i in range(len(urbext_data_year)):
        ua = urbext_data_year.iloc[i]
        nodes.append(ua['ORIG_FID'])
    print(f'nodes complete for {year}')
    edges = []
    print()
    for i in range(len(urbext_data_year)):
        ua = urbext_data_year.iloc[i]
        ua_f = urbext_year.filter(ee.Filter.eq('ORIG_FID', int(ua['ORIG_FID']))).first()
        intersects_fc = urbext_year.filter(ee.Filter.intersects('.geo', ua_f.geometry()))
        ids = intersects_fc.aggregate_array('ORIG_FID').getInfo()
        for c_id in ids:
            edges.append((ua['ORIG_FID'], c_id))
        if i % 100 == 0:
            print(i, end=' ', flush=True)
    print(f'edges complete for {year}')
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
        old_features = urbext_year.filter(ee.Filter.inList('ORIG_FID', ee.List(idlist)))

        filtered_df = urbext_data_year[urbext_data_year['ORIG_FID'].isin(idlist)]
        sorted_df = filtered_df.sort_values(by='ORIG_FID', ascending=False)
        main_names = []
        all_name_list = []
        studyctrlatlons = []
        for rownum in range(len(sorted_df)):
            if (sorted_df.iloc[rownum]['JRC_NM_LIS'] is not None) and (not sorted_df.iloc[rownum]['JRC_NM_LIS'] in ["", "N/A"]):
                all_name_list += [i.strip() for i in sorted_df.iloc[rownum]['JRC_NM_LIS'].split(";")]
            all_name_list.append(sorted_df.iloc[rownum]['CIES_NM_TL'].split(",")[0].strip())

            studyctrlon = sorted_df.iloc[rownum]['study_center_lon'].round(4).astype(str)
            studyctrlat = sorted_df.iloc[rownum]['study_center_lat'].round(4).astype(str)
            studyctrlatlon = f"({studyctrlat} {studyctrlon})"
            studyctrlatlons.append(studyctrlatlon)

        sorted_df['studyctrlatlons'] = studyctrlatlons

        all_name_list = list(set(all_name_list))
        all_name_list.sort()
        all_name_list = [i for i in all_name_list if not i in ["", "N/A"]]
        if len(all_name_list) == 0:
            all_name_list = ["N/A"]

        max_id = filtered_df.loc[filtered_df[f'P_R23_{ref_year}'].idxmax()]['ORIG_FID'].astype(str)
        max_name = filtered_df.loc[filtered_df[f'P_R23_{ref_year}'].idxmax()]['JRC_NM_MAI']
        if max_name is None or max_name in ("", "N/A"):
            max_name = filtered_df.loc[filtered_df[f'P_R23_{ref_year}'].idxmax()]['CIES_NM_TL'].split(",")[0].strip()
        max_countryiso = filtered_df.loc[filtered_df[f'P_R23_{ref_year}'].idxmax()]['ISO']
        max_countryname = filtered_df.loc[filtered_df[f'P_R23_{ref_year}'].idxmax()]['CNTRY_NM']
        # Here add handling for centroid_large
        
        namestring = '_'.join(all_name_list)
        countryisostring = '_'.join(sorted_df['ISO'].astype(str).unique())
        countrynamestring = '_'.join(sorted_df['CNTRY_NM'].astype(str).unique())
        unregion1string = '_'.join([geoscheme[iso]['ungeo_1'] for iso in countryisostring.split('_')])
        unregion2string = '_'.join([geoscheme[iso]['ungeo_2'] for iso in countryisostring.split('_')])
        unregion3string = '_'.join([geoscheme[iso]['ungeo_3'] for iso in countryisostring.split('_')])
        unregion1string = '_'.join([str(i) for i in np.unique(unregion1string.split('_'))])
        unregion2string = '_'.join([str(i) for i in np.unique(unregion2string.split('_'))])
        unregion3string = '_'.join([str(i) for i in np.unique(unregion3string.split('_'))])
        un_LDCbool = int(np.any([geoscheme[iso]['ungeo_LDC'] for iso in countryisostring.split('_')]))
        un_LLDCbool = int(np.any([geoscheme[iso]['ungeo_LLDC'] for iso in countryisostring.split('_')]))
        un_SIDSbool = int(np.any([geoscheme[iso]['ungeo_SIDS'] for iso in countryisostring.split('_')]))
        studycentroidstring = '_'.join(sorted_df['studyctrlatlons'].astype(str))

        return idstring, ee.Feature(old_features.geometry().dissolve(), ee.Dictionary({'city_name_large': max_name, 'city_id_large': max_id, 'city_id': idstring, 'year': year, 'city_name': namestring, 'country_ISO': countryisostring, 'country_name': countrynamestring, 'country_ISO_large': max_countryiso, 'country_name_large': max_countryname, 'ungeoscheme_reg1': unregion1string, 'ungeoscheme_reg2': unregion2string, 'ungeoscheme_reg3': unregion3string, 'ungeoscheme_LDC': un_LDCbool, 'ungeoscheme_LLDC': un_LLDCbool, 'ungeoscheme_SIDS': un_SIDSbool, 'study_centroid_latlon': studycentroidstring, 'reference_idstring': ref_idstring, 'reference_year': ref_year}))

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
        if idx % 100 == 0:
            print(idx, end=' ', flush=True)

    # Merge features w same idstring into multipolygon features
    new_features_list = []
    for idstring in new_features_dict:
        nf = ee.FeatureCollection(new_features_dict[idstring]).union().first()
        nf = nf.copyProperties(new_features_dict[idstring][0])
        new_features_list.append(nf)

    # Export in chunks if FeatureCollection is large
    chunk_size = 4000
    if len(new_features_list) > chunk_size:
        # Loop to split and export feature collections
        for i in range(math.ceil(len(new_features_list)/chunk_size)):
            # Define the start and end indices for slicing the list
            start_index = i * chunk_size
            end_index = start_index + chunk_size

            # Slice the list to get the current chunk
            features_chunk = new_features_list[start_index:end_index]
            # Convert the chunk to an ee.FeatureCollection
            chunk_collection = ee.FeatureCollection(features_chunk)

            # Create export task
            exportTask = ee.batch.Export.table.toAsset(
                collection=chunk_collection,
                description=f'urbext_unions_{year}_chunk_{i+1}',
                assetId=f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_{year}__chunk_{i+1}'
            )

            # Start the export task
            exportTask.start()
            print(f'Exporting chunk {i+1}...')
    else:
        nf_year = ee.FeatureCollection(new_features_list)

        exportTask = ee.batch.Export.table.toAsset(
            collection=nf_year,
            description=f'urbext_unions_{year}',
            assetId=f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_{year}'
            # projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/urbanextents_unions_{year}
        )
        exportTask.start()




# # If exported in chunks, merge the chunk assets
# # Comment out all of the above code and uncomment below

# for year in YEARS:
#     collections = []
#     for chunk in range(1, [5, 6][int(year > 1980)]):
#         # Load the FeatureCollection assets
#         collections.append(ee.FeatureCollection(f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_{year}__chunk_{chunk}'))

#     # Merge the FeatureCollections
#     merged_collection = ee.FeatureCollection(collections).flatten()


#     # Export the merged FeatureCollection to a new asset
#     task = ee.batch.Export.table.toAsset(
#         collection=merged_collection,
#         description=f'Merged_Collection_Export_{year}',
#         assetId=f'projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_{year}' # Specify the output asset path
#     )
#     task.start()
