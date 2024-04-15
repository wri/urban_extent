import ee
ee.Initialize()

import geelayers



##### select random cities for testing
# image_collection = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/builtup_density_GHSL_BUthresh10pct')
# # Filter the image collection by ID to include only images from 2020
# filtered_collection = image_collection.filter(ee.Filter.stringContains('system:index', '2020'))
# filtered_collection.size().getInfo()
# image_ids = filtered_collection.aggregate_array('system:index').getInfo()
# # Split each string by '-' and save the first item in a new list
# first_items = [item.split('-')[0] for item in image_ids]
# matching_items = [item for item in first_items if item in df['UC_NM_MN'].values]
# import random
# l=0
# while l!=50:
#     random_items = random.sample(matching_items, 50)

#     # Filter the DataFrame based on whether UC_NM_MN values are in random_items
#     filtered_df = df[df['UC_NM_MN'].isin(random_items)]

#     # Extract the ID_HDC_G0 column values for these filtered rows
#     id_hdc_g0 = filtered_df['ID_HDC_G0'].values
#     l=len(id_hdc_g0)

#### Test 50 cities
id_hdc_g0_50=[2125,10248,7756,1242,1595,9359,833,8405,5959,9905,3141,5250,2377,1787,
           4141,3743,3804,5475,3450,616,702,3289,6648,1436,188,5881,115,1707,2739,
           541,82,1633,12920,2398,478,663,6591,4386,12672,10104,2429,1307,656,2280,
           2104,4093,2966,2195,2925,3557]
UC_NM_MN = ['Akhisar','Latina','Avignon','Koszalin','Murom','Valenciennes','Annecy','Savannah',
            'Barreiras','Trondheim','Sittwe','Muncar','Chipata','Pathankot','Ayacucho','Cajamarca',
            'Ughelli','Yamagata','Yamoussoukro','Eugene','Davenport','Lafia','Plymouth',
            'Zacatecas','Nukus','Monclova','Caruaru','Sirsa','Lublin','Dayton','Huancayo',
            'Vitebsk','Kut','Damanhur','Tula','Suez','Oujda','Constantine','Makhachkala',
            'Maroua','Kishoreganj','Herat','Mirzapur','Maracay','Jamshedpur','Rabat','Curitiba',
            'Kanpur','Yangon','Lagos']

#### 13 cities with scale factor issue
id_hdc_g0=[3557,2195,4386,2739,3141,5881,6591,6648,4141,2398,2104,12920,1633]

#### Test 250 cities
# # Filter the ImageCollection by the region of the point FeatureCollection
# filtered_collection = filtered_collection.randomColumn().sort('random').limit(300)
# # Sample the point FeatureCollection based on the images
# sampled_points = geelayers.CITY_DATA.filterBounds(filtered_collection.geometry())
# # Limit the number of sampled points to 300
# sampled_points = sampled_points.limit(251)
# features_with_id = sampled_points.getInfo()['features']
# id_hdc_g0=[]
# for feature in features_with_id:
#     id_hdc_g0 = id_hdc_g0+[feature['properties']['ID_HDC_G0']]

# Randomly selected 250 cities
id_hdc_g0_250=[12080, 9872, 9691, 12389, 1303, 6473, 5222, 5915, 10607, 1910, 12530, 1346, 13023,
 2276, 3420, 2484, 6203, 1780, 5792, 5811, 10186, 4171, 6476, 1177, 10860, 6970, 3193, 2078, 9122,
 12540, 2310, 12279, 9602, 1138, 568, 1751, 5159, 12291, 12778, 1210, 367, 12181, 2927, 2067, 11113,
 7028, 12803, 126, 362, 6238, 1656, 1473, 2514, 2445, 12882, 1449, 5756, 12682, 9278, 10556, 112,
 5344, 7998, 5909, 5924, 1830, 12153, 10809, 2288, 13005, 12097, 2959, 12513, 12095, 12524, 7497, 3615,
 542, 890, 2674, 11856, 2317, 84, 2101, 12306, 10614, 3434, 2312, 11295, 1411, 1477, 1262, 7323,
 2442, 7602, 12175, 12066, 6622, 4189, 12432, 9935, 3877, 7586, 7108, 4454, 456, 926, 12492, 6808,
 11285, 2423, 3610, 7184, 7125, 12559, 7958, 3196, 3260, 2216, 8846, 6217, 12546, 9383, 1856, 4669,
 4584, 12523, 6446, 11276, 3325, 11575, 207, 3791, 4404, 106, 10995, 10533, 4473, 10934, 786, 3684, 6313,
 10217, 8794, 383, 1590, 724, 1520, 2100, 12215, 587, 2653, 1219, 10941, 1539, 3533, 12201, 11004,
 1221, 6324, 6564, 3624, 1463, 12303, 12504, 9760, 4467, 3819, 11808, 12125, 5447, 3797, 2667, 1596,
 12262, 11896, 12113, 12343, 3375, 12596, 2432, 11643, 3586, 1260, 1512, 3567, 5136, 1068, 4457, 3518,
 1705, 12537, 709, 11906, 12512, 436, 12166, 7416, 10427, 2272, 290, 2127, 13020, 984, 3120, 10680,
 2023, 12028, 10171, 12193, 11982, 11286, 4455, 5650, 11700, 6662, 12051, 12586, 1849, 6990, 3298, 1931,
 5202, 6183, 1939, 2522, 12807, 11447, 10604, 1211, 9397, 12450, 5396, 440, 1775, 10980, 1392, 2652,
 12317, 12054, 1628, 7979, 12170, 12105, 10831, 8113, 150, 10369, 5793, 1407]

