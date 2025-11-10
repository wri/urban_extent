import ee
ee.Initialize()

import config

# If exported in chunks, merge the chunk assets
for year in config.YEARS:
    # Load the FeatureCollection assets
    collection1 = ee.FeatureCollection(f'{config.ROOT}/{config.VERSION}/urbanextents_unions_{year}_chunk_1')
    collection2 = ee.FeatureCollection(f'{config.ROOT}/{config.VERSION}/urbanextents_unions_{year}_chunk_2')

    # Merge the FeatureCollections
    merged_collection = collection1.merge(collection2)

    # Export the merged FeatureCollection to a new asset
    task = ee.batch.Export.table.toAsset(
        collection=merged_collection,
        description=f'Merged_Collection_Export_{year}',
        # Specify the output asset path
        assetId=config.URBAN_EXTENTS_UNIONS.format(year=year)
    )
    task.start()
