from setup import *
import grass_utils
from utils import setup_dir
import grass.script as gs
import argparse
import os
import json

def crop_and_export(raster_name, mask_name, file_path, **kwargs):
    interpolated_name = grass_utils.interpolate_raster(raster_name)
    cropped_name = grass_utils.crop_raster(interpolated_name, mask_name, **kwargs)
    grass_utils.export_raster(cropped_name, output_file=file_path, **kwargs)

def import_all_features(feature_paths):
    for feature_name, feature_path in feature_paths.items():
        grass_utils.import_raster(feature_path, feature_name)

def subregion_processor(region_id, region_file, output_directory, feature_names, **kwargs):
    # create output directory
    region_out_dir = os.path.join(output_directory, region_id)
    setup_dir(region_out_dir)

    # 1. import region boundary into GRASS
    grass_utils.import_vector(region_file, region_id)

    # 2. update bounds to sub-region
    grass_utils.set_subregion_bounds(region_id, 'elevation')

    # 7. crop and export MAP, PGA, soil data
    for feature in feature_names:
        crop_and_export(feature, region_id, os.path.join(region_out_dir, f'{feature}.tif'))

    # 3. rasterize landslide inventory
    grass_utils.rasterize_vmap('inventory', verbose=True, binarize=True)
    grass_utils.export_raster(f'inventory_raster', 
        output_file=os.path.join(region_out_dir, 'inventory.tif'), type='UInt16'
    )

    # 4. rasterize region bounds
    grass_utils.rasterize_vmap(region_id, verbose=True)
    grass_utils.export_raster(f'{region_id}_raster', output_file=os.path.join(region_out_dir, 'region.tif'), type='UInt16')
    
    # 5. generate slope units
    slu_map = f'{region_id}_slu'
    grass_utils.run_slopeunits(
        demmap = 'elevation',
        slumap = slu_map,
        thresh = 1e6,
        cvmin = 0.9,
        areamin = 5e4,
        areamax = 5e5,
        rf = 10,
        maxiteration = 50,
        overwrite = True
    )

    # 6. rasterize and store slopeunits
    grass_utils.set_subregion_bounds(region_id, 'elevation')
    grass_utils.export_raster(slu_map, 
        output_file=os.path.join(region_out_dir, 'slopeunits.tif'), type='UInt32'
    )

def process_subregions(data_json_path, regions_dir, output_dir):
    with open(data_json_path, 'r') as f:
        data_files = json.load(f)

    inventory_path = data_files['inventory']
    dem_path = data_files['elevation']
    feature_paths = data_files['features']

    grass_utils.import_raster(dem_path, 'elevation')
    grass_utils.import_vector(inventory_path, 'inventory')
    import_all_features(feature_paths)
    feature_names = ['elevation'] + list(feature_paths.keys())

    # configure output directory
    setup_dir(output_dir)

    region_list = get_region_files(regions_dir)
    for region_id in region_list:
        print('Processing region: ', region_id)
        subregion_processor(region_id, os.path.join(regions_dir, f'{region_id}.shp'), output_dir, feature_names)

if __name__ == "__main__":
    # handle arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--regions_dir', type=str, required=True)
    parser.add_argument('--data_json_path', type=str, required=True)
    args = parser.parse_args()

    process_subregions(args.data_json_path, args.regions_dir, args.output_dir)