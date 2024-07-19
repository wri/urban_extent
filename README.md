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
