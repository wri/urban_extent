# Urban Extent

## Requirements
`conda install -n base mamba -c conda-forge`

`conda create -n urban_extent python=3.11 earthengine-api unidecode pandas scikit-learn geemap`

## Getting started
1. `conda activate urban_extent`
2. `jupyter notebook`
3. Set the built-up year for which to produce extents with `mapYear` in `gee/config.py`. Select from 1980/1990/2000/2005/2010/2015/2020.
4. All outputs are stored on GEE under `projects/wri-datalab/cities/urban_land_use/data`, you need to create a folder for your work and update `IC_ID` in `gee/config.py`.
5. Run `gee/super_raster.py` to generate the urban extent rasters. You need to create a tracking sheets to track the task status for each city. Update the `cities_track` in `gee/super_raster.py`for your tracking sheets.
6. Run `gee/urban_extents_from_super_raster.py` to generate the urban extent vectors. Update `YEAR`, `ROOT`, `SUFFIX`, `SR_ID`, `DEST_NAME` for your input (urban extent ImageCollection) and output (urban extent FeatureCollection) asset IDs on GEE. 
7. Run `gee/create_city_unions_v2.py` to merge the overlapped city polygons.
8. `gee/urban-extent.ipynb` is used for interactive visualization.
9. Tracking sheets and city centroid points are stored in the `data` folder.

## Assets on Google Earth Engine
1. Assets for African cities:
    - Cities centroid points asset ID: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/city_data_checked_africa`
    - Raster asset IDs: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/builtup_density_JRCs_africa_yyyy`
    - Vector asset IDs: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/GHSL_BUthresh10pct_JRCs_africa_yyyy`
    - Merged vector asset IDs: `projects/wri-datalab/cities/urban_land_use/data/african_cities_July2024/urbanextents_unions_yyyy`
        ###### * `yyyy` select from 1980/1990/2000/2005/2010/2015/2020

2. Global assets [Work in Progress]

## Metadata for features and images
- **UC_NM_MN_ORIGINAL**: Original city name from source.
- **UC_NM_MN [city_name]**: I tried to fill in the N/As and correct the non-English characters when go through the cities. The city name in this column is a bit more clean than the original.
- **ID_HDC_G0 [city_ids]**: Unique City ID from source. Could be used as a key to merge tables.
- **P15**: Population 2015 from source.
- **B15**: Built-up area 2015 from source.
- **study_center_lat**: Selected city centroid point coordinate - latitude.
- **study_center_lon**: Selected city centroid point coordinate - longitude.
- **bu_city_center_lat**: Non NA start point coordinate - latitude.
- **bu_city_center_lon**:  Non NA start point coordinate - longitude.
- **study_area_scale_factor**: Scale factor - 20/40/80/160/320/640/1280/2560/5120/10240
- **GRGN_L1 [region1]**: Continent from source.
- **GRGN_L2 [region2]**: More detailed region info from source. Used for B15-P15 regression. 
    ###### * Merged city polygon feature collection used a different column name system labeled in [], it also has less city metadata information than other assets.
