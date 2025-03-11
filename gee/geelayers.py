import ee
ee.Initialize()

import geemap
import ipyleaflet
import ipywidgets as widgets
import config

#
# GET DATA
#
# Old output built-up density
# based GHSL data with built-up threshold of 10%
## All
GHSL = ee.ImageCollection('projects/wri-datalab/cities/urban_land_use/data/builtup_density_GHSL_BUthresh10pct')
## 2020
GHSL_2020 = GHSL.filter(ee.Filter.stringContains('system:index', '2020'))

# New City data from GHSL
## Polygons
# CITY_DATA_POLY = ee.FeatureCollection('projects/wri-datalab/AUE/GHS_STAT_UCDB2015MT_GLOBE_R2019A_V1_2')
CITY_DATA_POLY = ee.FeatureCollection('projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Mar2025/guppd_v1_poly')
## Checked city points
# CITY_DATA_POINT = ee.FeatureCollection('projects/wri-datalab/cities/urban_land_use/data/global_cities_Aug2024/city_data_checked')
CITY_DATA_POINT = ee.FeatureCollection('projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Mar2025/guppd_v1')
# 'projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/city_data_checked'
# 'projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/city_data_checked_africa'
# 'projects/wri-datalab/cities/urban_land_use/data/test_tori_Apr2024/city_data_Kigali_Nairobi_Addis'

if config.USE_COMPLETED_FILTER:
    COMPLETED_CITIES = ee.ImageCollection(config.IC_ID).filter(ee.Filter.equals('builtup_year', config.mapYear))
    COMPLETED_CITIES_LIST = COMPLETED_CITIES.aggregate_array('ORIG_FID').getInfo()
    CITY_LIST = CITY_DATA_POINT.aggregate_array('ORIG_FID').getInfo()
    COMPLETED_FILTER =  [item for item in CITY_LIST if item not in COMPLETED_CITIES_LIST]
    CITY_DATA = CITY_DATA_POINT.filter(ee.Filter.inList('ORIG_FID', COMPLETED_FILTER))
else:
    CITY_DATA = CITY_DATA_POINT



# Built up area mask
# based on public GHS data using BuiltAreaThresh
GHSLyear = ee.Image(f"JRC/GHSL/P2023A/GHS_BUILT_S/{config.mapYear}").gte(config.BuiltAreaThresh).selfMask().select('built_surface').rename(['bu'])

# obtain projection, CRS and Transform for input layer
_proj = GHSLyear.projection().getInfo()

# "ESRI:54009" # for use with GHSL2023release image which doesn't have CRS in metadata.
GHSL_CRS = "EPSG:3857"
GHSL_TRANSFORM = _proj['transform']
# print("GHSL PROJ:", GHSL_CRS, GHSL_TRANSFORM)

#
# Select built-up IMAGE
#
BU = GHSLyear

# create band ("builtup") with binary builtup value
IS_BUILTUP = BU.gt(0).rename(['builtup'])

# create band ("density") with the percent of pixels that are built-up within radius of each pixel
_usubu_rededucer = ee.Reducer.mean()
_usubu_kernel = ee.Kernel.circle(
    radius=config.DENSITY_RADIUS,
    units=config.DENSITY_UNIT,
    normalize=True,
    magnitude=1
)
_density = IS_BUILTUP.unmask(0).reduceNeighborhood(
    reducer=_usubu_rededucer,
    kernel=_usubu_kernel,
    skipMasked=True,
)
# create band ("builtup_class") with built-up classification (urban, suburban, rural) for each built-up pixel based on its "density" value
_usubu = ee.Image(0).where(_density.gte(config.SUBURBAN_BOUND).And(_density.lt(config.URBAN_BOUND)), 1).where(_density.gte(config.URBAN_BOUND), 2).rename(['builtup_class'])
_density = _density.multiply(100).rename(['density'])
BU_DENSITY_CAT = _usubu.addBands([_density, IS_BUILTUP]).toUint8()

# create image of all urban or suburban builtup pixels that have at least MINPIXS neighbors that are also urban or suburban builtup pixels
BU_CONNECTED = IS_BUILTUP.multiply(_usubu.gt(0)).selfMask().connectedPixelCount(config.MINPIXS).eq(config.MINPIXS).selfMask()
BU_LATLON = BU_CONNECTED.addBands(ee.Image.pixelLonLat())


# Interactive map
def interactive_map(collection):
    explore_image_collection = ee.ImageCollection(collection)

    ## Select Image
    ### Count the number of images in the collection
    size = explore_image_collection.size().getInfo()
    ### Extract image names as a list
    images = explore_image_collection.toList(size).getInfo()
    image_names = [item['properties']['system:index'] for item in images]

    selected_image = explore_image_collection.filter(ee.Filter.stringContains('system:index', image_names[0])).first()

    #
    # SUB FUNCTIONS
    #
    ## Define a function to zoom to an image
    def zoom_to_image(change):
        if change['type'] == 'change' and change['name'] == 'value':
            # Get the selected image based on the dropdown value
            selected_image = explore_image_collection.filter(ee.Filter.stringContains('system:index', change['new'])).first()
            # Get the image from the collection based on name
            Map.centerObject(selected_image)

    ## Define a function to change the band displayed
    def change_band(change):
        if change['type'] == 'change' and change['name'] == 'value':
            # Remove old image collection
            Map.remove_layer('New Builtup 2020')
            # Remove old point collection
            Map.remove_layer('New City Data Points')
            # Add updated image collection back
            Map.addLayer(explore_image_collection.select(change['new']), {}, 'New Builtup 2020', True)
            # Add city point back
            Map.addLayer(CITY_DATA_POINT, city_point_vis, 'New City Data Points', True)
            explore_layer = Map.find_layer("New Builtup 2020")
            explore_layer.interact(opacity=(0, 1, 0.1))

    ## Define a function to change the scale factor subset
    def change_scale_factor(change):
        if change['type'] == 'change' and change['name'] == 'value':
            # Remove old image collection
            Map.remove_layer('New Builtup 2020')
            # Remove old point collection
            Map.remove_layer('New City Data Points')
            if pass_selector.value == 'All':
                if scale_selector.value == 'All':
                    filtered_collection = explore_image_collection
                else:
                    # Filter image collection by selected scale factor
                    filtered_collection = explore_image_collection.filter(ee.Filter.eq('study_area_scale_factor', change['new']))
            else:
                if scale_selector.value == 'All':
                    filtered_collection = explore_image_collection.filter(ee.Filter.eq('scale_factor_set', pass_selector.value))
                else:
                    # Filter image collection by selected scale factor
                    filtered_collection = explore_image_collection.filter(ee.Filter.eq('study_area_scale_factor', change['new'])).filter(ee.Filter.eq('scale_factor_set', pass_selector.value))
            # Add updated image collection back
            Map.addLayer(filtered_collection, new_bu_vis, 'New Builtup 2020', True)
            # Add city point back
            Map.addLayer(CITY_DATA_POINT, city_point_vis, 'New City Data Points', True)
            # Update image names
            size = filtered_collection.size().getInfo()
            images = filtered_collection.toList(size).getInfo()
            image_names = [item['properties']['system:index'] for item in images]
            # Update options of image_selector widget
            image_selector.options = image_names
            # Update selected image
            selected_image = filtered_collection.first()
            Map.centerObject(selected_image)
            explore_layer = Map.find_layer("New Builtup 2020")
            explore_layer.interact(opacity=(0, 1, 0.1))
                
    
    ## Define a function to change the scale factor subset
    def change_pass(change):
        if change['type'] == 'change' and change['name'] == 'value':
            # Remove old image collection
            Map.remove_layer('New Builtup 2020')
            # Remove old point collection
            Map.remove_layer('New City Data Points')
            if pass_selector.value == 'All':
                filtered_collection = explore_image_collection
                scale_selector.options = ['All', 20, 50, 80, 120, 200, 400, 800, 2000]
            elif pass_selector.value == 'True':
                # Filter image collection by if the city pass the scale factor check
                filtered_collection = explore_image_collection.filter(ee.Filter.eq('scale_factor_set', change['new']))
                scale_selector.options = ['All', 20, 50, 80, 120, 200, 400, 800, 2000]
            elif pass_selector.value == 'False':
                # Filter image collection by if the city pass the scale factor check
                filtered_collection = explore_image_collection.filter(ee.Filter.eq('scale_factor_set', change['new']))
                scale_selector.options = [20]
            # Add updated image collection back
            Map.addLayer(filtered_collection, new_bu_vis, 'New Builtup 2020', True)
            # Add city point back
            Map.addLayer(CITY_DATA_POINT, city_point_vis, 'New City Data Points', True)
            # Update image names
            size = filtered_collection.size().getInfo()
            images = filtered_collection.toList(size).getInfo()
            image_names = [item['properties']['system:index'] for item in images]
            # Update options of image_selector widget
            image_selector.options = image_names
            # Update selected image
            selected_image = filtered_collection.first()
            Map.centerObject(selected_image)
            explore_layer = Map.find_layer("New Builtup 2020")
            explore_layer.interact(opacity=(0, 1, 0.1))


    #
    # WIDGETS
    #
    # Filter by if the scale factor pass the test
    pass_selector = widgets.Dropdown(
        options=['All', 'True', 'False'],
        description="Pass Scale Factor Check:",
        style={'description_width': '150px'} 
    )
    # Add dropdown widgets
    display(pass_selector)

    # Filter by scale factor
    ### Create a dropdown widget
    scale_selector = widgets.Dropdown(
        options=['All', 20, 50, 80, 120, 200, 400, 800, 2000],
        description="Select Scale Factor:",
        style={'description_width': '150px'} 
    )
    display(scale_selector)

    # display(collection)
    ### Create a dropdown widget
    image_selector = widgets.Dropdown(
        options=image_names,
        description="Select Image:",
        style={'description_width': '150px'} 
    )
    display(image_selector)

    ## Select Band
    ### Extract band names as a list
    band_names = selected_image.bandNames().getInfo()
    ### Create a dropdown widget
    band_selector = widgets.Dropdown(
        options=band_names,
        description="Select Band:",
        style={'description_width': '150px'} 
    )
    display(band_selector)

    #
    # MAP
    #
    # Custom vis_params
    city_point_vis = {
        'color': 'yellow',
        'pointSize': 25,
        'pointShape': 'circle',
        'width': 1
    }
    old_bu_vis = {
        'bands': ['builtup_class'],
        'min': 0,
        'max': 2,
        'palette': ['lightcoral', 'indianred', 'darkred']
    }
    new_bu_vis = {
        'bands': ['builtup_class'],
        'min': 0,
        'max': 2,
        'palette': ['lightblue', 'dodgerblue', 'navy']
    }

    ## Create a map
    Map = geemap.Map()

    ## Layer template
    # Map.addLayer(ee_object, vis_params, name, shown, opacity)
    
    ## Add other Urban Extent layers
    # Map.addLayer(GHSL, {}, 'Old Builtup Density', False, 1)
    Map.addLayer(CITY_DATA_POLY, {}, 'New City Polygons', True)
    Map.addLayer(GHSL_2020, old_bu_vis, 'Old Builtup 2020', True)
    # Map.addLayer(BU, {}, 'New Built up Surface input', True)
    # Map.addLayer(IS_BUILTUP, {}, 'New Built up Surface? binary', True)
    # Map.addLayer(BU_DENSITY_CAT, {}, 'Builtup Density Categories', True)
    # Add 2 other bands from BU_DENSITY_CAT
    # Map.addLayer(BU_LATLON, {}, 'Connected Builtup Pixels LatLon', True)
    # Add 1 other bands from BU_LATLON
    

    ## Add Layer for dropdown
    Map.addLayer(explore_image_collection.select(band_names[0]), new_bu_vis, 'New Builtup 2020', True)
    ## Center on image collection
    Map.centerObject(selected_image)

    ## Add point layer
    Map.addLayer(CITY_DATA_POINT, city_point_vis, 'New City Data Points', True)

    ## Controls
    Map.addLayerControl()
    explore_layer = Map.find_layer("New Builtup 2020")
    display(explore_layer.interact(opacity=(0, 1, 0.1)))

    ## Display the map
    display(Map)

    #
    # OBSERVERS
    #
    ## Observe the pass_selector dropdown widget for changes
    pass_selector.observe(change_pass, names='value')
    ## Observe the scale_selector dropdown widget for changes
    scale_selector.observe(change_scale_factor, names='value')
    ## Observe the image_selector dropdown widget for changes
    image_selector.observe(zoom_to_image, names='value')
    ## Observe the band_selector dropdown widget for changes
    band_selector.observe(change_band, names='value')
