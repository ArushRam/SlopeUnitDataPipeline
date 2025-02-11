from setup import *
import grass_utils
from utils import setup_dir
import grass.script as gs
import argparse
import os
import json

def crop_and_export(raster_name, mask_name, file_path, interpolation_method='bicubic', **kwargs):
    print(interpolation_method)
    interpolated_name = grass_utils.interpolate_raster(raster_name, interpolation_method=interpolation_method)
    cropped_name = grass_utils.crop_raster(interpolated_name, mask_name, **kwargs)
    grass_utils.export_raster(cropped_name, output_file=file_path, **kwargs)

def import_all_features(feature_paths, **kwargs):
    for feature_name, feature_path in feature_paths.items():
        grass_utils.import_raster(feature_path, feature_name, **kwargs)

def subregion_processor(region_id, region_file, output_directory, continuous_features, categorical_features, **kwargs):
    # create output directory
    region_out_dir = os.path.join(output_directory, region_id)
    setup_dir(region_out_dir)

    # 1. import region boundary into GRASS
    grass_utils.import_vector(region_file, region_id)

    # 2. update bounds to sub-region
    grass_utils.set_subregion_bounds(region_id, 'elevation')

    # # 7. crop and export MAP, PGA, soil data
    for feature in continuous_features:
        crop_and_export(feature, region_id, os.path.join(region_out_dir, f'{feature}.tif'), interpolation_method='bicubic')
    for feature in categorical_features:
        crop_and_export(feature, region_id, os.path.join(region_out_dir, f'{feature}.tif'), interpolation_method='nearest')

    # 3. rasterize landslide inventory
    grass_utils.rasterize_vmap('inventory', verbose=True, binarize=True)
    crop_and_export('inventory_raster', region_id, os.path.join(region_out_dir, f'inventory.tif'), interpolation_method='nearest')

    # 4. rasterize region bounds
    grass_utils.rasterize_vmap(region_id, verbose=True)
    crop_and_export(f'{region_id}_raster', region_id, os.path.join(region_out_dir, f'region.tif'), interpolation_method='nearest')

    # 5. generate slope units
    slu_map_intermediate = f'{region_id}_slu_intermediate'
    slu_map = f'{region_id}_slu'
    grass_utils.run_slopeunits(
        demmap = f'{region_id}_elevation_interp',
        slumap = slu_map_intermediate,
        slumapclean = slu_map,
        thresh = 800000,
        cvmin = 0.4,
        areamin = 40000,
        rf = 10,
        maxiteration = 100,
        cleansize = 20000,
        overwrite = True
    )

    # 6. rasterize and store slopeunits
    grass_utils.export_raster(slu_map, 
        output_file=os.path.join(region_out_dir, 'slopeunits.tif'), type='UInt32'
    )

def process_subregions(data_json_path, regions_dir, output_dir):
    with open(data_json_path, 'r') as f:
        data_files = json.load(f)

    inventory_path = data_files['inventory']
    dem_path = data_files['elevation']
    feature_paths = data_files['features']
    categorical_feature_paths = data_files['categorical_features']

    # grass_utils.import_raster(dem_path, 'elevation')
    # grass_utils.import_vector(inventory_path, 'inventory')
    # import_all_features(categorical_feature_paths, resample='nearest')
    # import_all_features(feature_paths, resample='bicubic')
    continuous_features = ['elevation'] + list(feature_paths.keys())
    categorical_features = list(categorical_feature_paths.keys())

    # configure output directory
    setup_dir(output_dir)

    region_list = get_region_files(regions_dir)
    for region_id in region_list:
        print('Processing region: ', region_id)
        subregion_processor(region_id, os.path.join(regions_dir, f'{region_id}.shp'), output_dir, continuous_features, categorical_features)

if __name__ == "__main__":
    # handle arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--regions_dir', type=str, required=True)
    parser.add_argument('--data_json_path', type=str, required=True)
    args = parser.parse_args()

    process_subregions(args.data_json_path, args.regions_dir, args.output_dir)