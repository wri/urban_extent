# Urban Extent


## Requirements
`conda install -n base mamba -c conda-forge`
`conda create -n urban_extent python=3.11 earthengine-api unidecode pandas scikit-learn geemap`

## Getting started
1. `conda activate urban_extent`
2. `jupyter notebook`
3. `gee/urban-extent.ipynb` # All the other scripts are referenced from here.
4. All outputs are stored on GEE under `projects/wri-datalab/cities/urban_land_use/data` but you need to create a folder for your work and update `IC_ID` in `gee/config.py`.
