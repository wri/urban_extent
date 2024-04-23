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
# filtered_collection = filtered_collection.randomColumn().sort('random').limit(1300)
# # Sample the point FeatureCollection based on the images
# sampled_points = geelayers.CITY_DATA.filterBounds(filtered_collection.geometry())
# # Limit the number of sampled points to 300
# sampled_points = sampled_points.limit(1300)
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


# id_hdc_g0_700 = [item for item in id_hdc_g0 if item not in id_hdc_g0_50]
# id_hdc_g0_700 = [item for item in id_hdc_g0_700 if item not in id_hdc_g0_250]
# id_hdc_g0_700 = id_hdc_g0_700[:700]

id_hdc_g0_700 = [3050, 991, 1010, 1036, 1089, 4980, 3310, 3460, 3506, 3512, 888, 998, 1099, 1324, 
                 1333, 1336, 187, 204, 403, 462, 625, 866, 885, 899, 917, 989, 1041, 876, 914, 
                 12084, 12208, 12378, 12396, 12420, 12436, 12600, 10429, 11254, 11381, 11390, 
                 11411, 11493, 11988, 1585, 512, 540, 2886, 2422, 2439, 2523, 2524, 2531, 2584, 
                 2748, 2849, 2887, 1986, 1602, 1632, 1673, 1991, 1821, 1969, 1989, 2017, 2246, 
                 1877, 4975, 353, 12601, 11489, 7248, 7299, 8253, 8326, 2773, 2827, 12904, 12914, 
                 12915, 12918, 12947, 12958, 12962, 12989, 5984, 11478, 12673, 12678, 3631, 3269, 
                 3537, 63, 132, 255, 231, 237, 1521, 12598, 418, 532, 3092, 3096, 3159, 8031, 3502, 
                 3734, 3735, 4019, 4545, 4563, 5633, 6019, 6025, 6033, 6037, 6155, 6157, 6195, 6266, 
                 1059, 2682, 2902, 10450, 10822, 3469, 3532, 3626, 3655, 3769, 26, 55, 79, 193, 203, 
                 206, 580, 686, 694, 898, 910, 911, 933, 945, 981, 983, 992, 997, 1004, 1025, 11123, 
                 11125, 11126, 11127, 11134, 11136, 11180, 11236, 11864, 3227, 1008, 1035, 13036, 2093, 
                 3401, 849, 897, 1148, 1190, 1208, 1334, 1345, 1359, 1386, 1395, 1398, 1437, 873, 12089, 
                 12126, 12142, 12149, 12171, 12320, 12340, 12363, 12385, 12459, 10302, 10415, 11299, 11393, 
                 11401, 11421, 11879, 11924, 1637, 2901, 531, 544, 547, 552, 575, 621, 631, 673, 678, 687, 
                 2395, 2431, 2713, 2757, 2852, 2024, 447, 455, 464, 479, 1708, 2010, 2264, 2080, 1816, 1860, 
                 1891, 1893, 12394, 12435, 12445, 7084, 7109, 7680, 7011, 5243, 2504, 2519, 2521, 2529, 2559, 
                 2560, 2605, 2725, 2750, 4393, 12921, 12936, 12974, 5892, 6174, 11165, 12551, 12661, 3303, 88, 
                 89, 91, 104, 119, 178, 184, 186, 189, 197, 78, 2122, 2124, 2593, 370, 796, 2998, 3130, 3223,
                 4351, 5489, 5507, 5560, 5645, 321, 4407, 10857, 3795, 3809, 4216, 4498, 4679, 5199, 3394, 
                 3616, 4068, 4083, 4175, 69, 166, 250, 264, 559, 567, 577, 594, 601, 675, 707, 718, 733, 749, 
                 903, 920, 1011, 1018, 697, 836, 840, 879, 3605, 3611, 3667, 3689, 3697, 3698, 3719, 10374, 
                 10880, 10996, 11779, 10454, 10747, 10757, 10779, 10780, 10824, 10855, 10892, 10958, 11034, 
                 11076, 11170, 11273, 11358, 11387, 11463, 11566, 11667, 11722, 6075, 5928, 6045, 5951, 5897,
                 5980, 6080, 6053, 5956, 5995, 6078, 6084, 9425, 10089, 8448, 8612, 7951, 7957, 8278, 3366,
                 3363, 3371, 3491, 4007, 3746, 3803, 2885, 2936, 3000, 3448, 3301, 3453, 3069, 3413, 3414, 
                 3121, 3314, 3423, 9590, 9650, 9682, 9802, 7055, 7854, 8123, 8290, 8404, 8463, 8491, 8554, 
                 8557, 8683, 8831, 9217, 9227, 9323, 6847, 7061, 7063, 7122, 7163, 7177, 7227, 7337, 7387, 
                 7406, 7459, 7518, 7523, 7551, 7644, 7812, 7879, 7914, 7924, 8067, 8711, 8739, 8760, 8911, 
                 9448, 9799, 6822, 6980, 6992, 8365, 8202, 7384, 7807, 8185, 8284, 12053, 12101, 11111, 11199, 
                 11294, 11437, 11532, 11687, 11705, 11735, 11738, 11749, 11768, 11790, 11941, 12009, 10987, 
                 11084, 11311, 11329, 11362, 11449, 11508, 11551, 11556, 11731, 10122, 10124, 10136, 10149, 
                 10154, 10232, 10296, 10299, 10463, 10479, 10494, 10505, 10512, 10570, 10619, 10893, 10897, 
                 10908, 10924, 10986, 10990, 11090, 11270, 11312, 10091, 10138, 10291, 10305, 10352, 10428, 
                 10442, 10446, 10480, 10490, 10507, 10517, 10526, 10527, 10691, 10833, 10960, 10992, 11269, 
                 11317, 11346, 11431, 6442, 6456, 6538, 6558, 6659, 6189, 6221, 6232, 6234, 6289, 6291, 6300, 
                 6335, 6357, 6373, 6395, 6407, 6430, 6548, 6555, 6614, 6623, 6639, 6680, 6705, 6711, 6823, 
                 6824, 6832, 6948, 6353, 6404, 6439, 6475, 6485, 10084, 10092, 10170, 7272, 8609, 8657, 
                 8817, 7510, 7561, 7676, 7772, 7886, 7995, 8005, 8110, 8553, 8584, 3044, 3186, 9055, 8419, 272, 
                 347, 379, 397, 417, 432, 474, 483, 484, 487, 502, 513, 525, 551, 553, 554, 624, 640, 401, 409, 
                 491, 1105, 13007, 1165, 1259, 1272, 199, 12076, 12114, 12158, 12190, 12218, 12231, 12244, 12245, 
                 12249, 12267, 12272, 12289, 12300, 12336, 12391, 12400, 12406, 12495, 12539, 12569, 12597, 
                 12618, 11137, 11553, 11684, 11703, 11716, 11761, 11925, 11933, 12029, 11858, 1675, 437, 3850, 
                 3920, 3933, 3968, 4004, 1911, 1038, 12050, 12976, 10629, 11653, 11862, 12019, 7887, 8550, 8675, 
                 8677, 6763, 9975, 5738, 5749, 5867, 5918, 2779, 2794, 2801, 2895, 2897, 1526, 68, 75, 227, 228, 
                 243, 2157, 2165, 2511, 2537, 2169, 753, 12772, 13122, 3060, 12087, 1551, 12155, 4911, 5740, 
                 1461, 2924, 4339, 386, 423, 556, 802, 972, 11171, 11212, 11275, 11694, 11821, 6028, 3064, 5917, 
                 996, 1078, 1102, 1109, 1119, 10072, 3503, 5836, 1275, 1353, 1405, 1406, 1420]
len(id_hdc_g0_700)

