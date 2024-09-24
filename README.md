# Urban Extent

## Requirements
`conda install -n base mamba -c conda-forge`

`conda create -n urban_extent python=3.11 earthengine-api unidecode pandas scikit-learn geemap`

## Getting started
1. `conda activate urban_extent`
2. `jupyter notebook`
3. Set the built-up year for which to produce extents with `mapYear` in [config.py](gee/config.py). Select from 1980/1990/2000/2005/2010/2015/2020.
4. All outputs are stored on GEE under `projects/wri-datalab/cities/urban_land_use/data`, you need to create a folder for your work and update `IC_ID` in [config.py](gee/config.py).
5. Run [super_raster.py](gee/super_raster.py) to generate the urban extent rasters. You need to create a tracking sheet to track the task status for each city. Update the `cities_track` in [super_raster.py](gee/super_raster.py) for your tracking sheets.
6. Run [urban_extents_from_super_raster.py](gee/urban_extents_from_super_raster.py) to generate the urban extent vectors. Update `YEAR`, `ROOT`, `SUFFIX`, `SR_ID`, `DEST_NAME` for your input (urban extent ImageCollection) and output (urban extent FeatureCollection) asset IDs on GEE. 
7. Run [create_city_unions_v2.py](gee/create_city_unions_v2.py) to union the overlapped city polygons.
8. [urban-extent.ipynb](gee/urban-extent.ipynb) is used for interactive visualization.
9. Tracking sheets and city centroid points are stored in the [data](gee/data) folder.

## Method used to delineate urban extents
To map the urban extent of any city, we followed the steps articulated here:
1.	Obtain centroids for cities of interest and a built-up layer for their regions. For built-up layers, we used [GHS-BUILT-S R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php) at 100-meter resolution, including only pixels classified as having 10% or greater built-up coverage, for years 1980 to 2020 with ten-year intervals prior to 2000 and five-year intervals thereafter. For centroids, we initially used latitudes/longitudes of cities available from the [GHS-UCDB R2019A](https://human-settlement.emergency.copernicus.eu/ghs_stat_ucdb2015mt_r2019a.php). To enhance accuracy, we sequentially refined the city centroids not located in a built-up area near the center of the city using four different methods, applied in the following order, until a valid result was generated: 
    1. calculate the average latitudes and longitudes of 5000 random points that fell within the masked built-up coverage of 1980 inside the city polygons from GHS-UCDB R2019A; 
    2. obtain centroids from Overture Maps, matched by city and country names; 
    3. obtain centroids from Google Map API, matched by city and country names; 
    4. manually inspect and adjust the centroid points if none of the prior methods provided satisfactory results.
2.	For each city _i_, define an overly inclusive maximum area of interest (the “study area”) using a radius (_R<sub>i</sub>_) from the city centroid based on estimated city population (_P<sub>i</sub>_) and slope (_S<sub>r</sub>_) and intercept (_I<sub>r</sub>_) from the linear average relationships between population and built-up area for all cities in each geographical region of GHS-UCDB R2019A and scaling it by a scale factor (_F<sub>i</sub>_) initially set at 20. The population and built-up area data used to establish this relationship were from 2015, as provided by GHS-UCDB R2019A. 
$$
R_i = \sqrt{\frac{e^{\left( S_r \cdot \ln(P_i) + I_r \right)} \cdot F_i}{\pi}} \qquad (1)
$$
3.	For each year, classify each built-up pixel within the study area based on the percent of pixels that are built-up within its 1-km2 circular neighborhood, an area with a radius roughly equivalent to a ten-minute walk. If 50% or more of the pixels in the circle are built-up, the pixel is classified as _Urban_. If less than 50% but 25% or more of the pixels in the circle are built-up, the pixel is classified as _Suburban_. If less than 25% of the pixels in the circle are built-up, the pixel is classified as _Rural_.
4.	If any of the _Urban_, _Suburban_, or _Rural_ pixels touches the boundary of the maximum area of interest in step 2, it suggests that the urban extent mapping may be constrained by the predefined study area. In such cases, we double the scale factor and re-run steps 2 and 3. The process begins with an initial scale factor of 20. If the urban extent is still insufficiently covered when the scale factor reaches 2560, a visual inspection of the city on the map was conducted. Based on the inspection, the scale factor was manually adjusted as necessary to ensure complete coverage of the urban extent (this was required for 11 cities for the year 2020 and the same or fewer cities in previous years).
5.	Vectorize all contiguous _Urban_ and _Suburban_ pixels to form urban cluster polygons. 
6.	Calculate the influence distance d of each urban cluster with an area A as the depth of a buffering ring around a circle with an area A and ring area equal to 0.25A. 
$$
d = \sqrt{\frac{1.25A}{\pi}} - \sqrt{\frac{A}{\pi}} = \sqrt{A} \cdot 0.06659 \qquad (2)
$$
7.	Buffer each urban cluster polygon by its influence distance d. Dissolve all buffered polygons to merge the polygons of those with overlapping influence areas. Retain only polygons that are within 200 meters of the city centroid. Merge all remaining polygons into a single feature. 
8.	Mask classified built-up pixels from step 3 to retain only those within the feature polygon. 
9.	Filter _Urban_ and _Suburban_ pixels to retain only those within clusters (from step 5) that contain at least one _Urban_ pixel. Vectorize these _Urban_ and _Suburban_ pixels as a single feature. 
10.	Fill any holes within the feature polygon that are less than 200 hectares in area. Include them in the feature polygon. This feature provides the urban extent.
11.	Repeat for each city and year of interest. 

## Assets on Google Earth Engine
1. Assets for African cities:
    - Cities centroid points asset ID: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/city_data_checked_africa`
    - Urban extent ImageCollection asset IDs: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/builtup_density_JRCs_africa_{year}`
    - Urban polygons FeatureCollection asset IDs: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/GHSL_BUthresh10pct_JRCs_africa_{year}`
    - Unioned urban polygons FeatureCollection asset IDs: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/urbanextents_unions_{year}`
        ###### * `{year}` select from 1980/1990/2000/2005/2010/2015/2020

2. Assets for global cities:
    - Cities centroid points asset ID: `projects/wri-datalab/cities/urban_land_use/data/global_cities_Aug2024/city_data_checked`
    - Urban extent ImageCollection asset IDs: `projects/wri-datalab/cities/urban_land_use/data/global_cities_Aug2024/builtup_density_JRCs_{year}`
    - Urban polygons FeatureCollection asset IDs: `projects/wri-datalab/cities/urban_land_use/data/global_cities_Aug2024/GHSL_BUthresh10pct_JRCs_{year}`
    - Unioned urban polygons FeatureCollection asset IDs: `projects/wri-datalab/cities/urban_land_use/data/global_cities_Aug2024/urbanextents_unions_{year}`
    - Full cities centroid points asset ID: `projects/wri-datalab/cities/urban_land_use/data/global_cities_Aug2024/city_data_checked_all` (includes cities without clear urban areas)
        ###### * `{year}` select from 1980/1990/2000/2005/2010/2015/2020

## Metadata for features and images
- **UC_NM_MN_ORIGINAL**: The original city name from the source.
- **UC_NM_MN**: A cleaned version of the city name. This column includes corrections for non-English characters and fills in missing values, providing a more standardized city name than the original.
- **ID_HDC_G0**: A unique city ID from the source, useful as a key for merging tables.
- **P15**: The population data for 2015 from the source.
- **B15**: The built-up area in 2015 from the source.
- **CENTER_SOURCE**: Source of the selected city centroid point - Source/COM/Overture/Google/Inspected/ToDo.
- **study_center_lat**: Selected city centroid point coordinate - latitude.
- **study_center_lon**: Selected city centroid point coordinate - longitude.
- **bu_city_center_lat**: Non NA start point coordinate - latitude.
- **bu_city_center_lon**:  Non NA start point coordinate - longitude.
- **study_area_scale_factor**: Scale factor - 20/40/80/160/320/640/1280/2560/5120/10240/20480
- **GRGN_L1 [region1]**: The continent from source.
- **GRGN_L2 [region2]**: More detailed regional information from the source, used for B15-P15 regression. 
- **[city_name_large]**: The name of the largest constituent city (based on population in 2015) within a unioned city.
- **[city_id_large]**: The ID of the largest constituent city (based on population in 2015) within a unioned city. Could be used as a key to merge tables.
- **[city_names]**: Names of the unioned cities, joined by '_'.
- **[city_ids]**: IDs of the unioned cities, joined by '_'.

    ###### * Unioned city polygon FeatureCollection used a different column name system labeled in [], it also has less city metadata information than other assets.
