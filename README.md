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
