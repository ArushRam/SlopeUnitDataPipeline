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

# def import_derived_features(feature_dir):
    # grass_utils.import_raster(os.path.join(feature_dir, 'aspect.tif'), 'aspect_map')
    # grass_utils.import_raster(os.path.join(feature_dir, 'slope.tif'), 'slope')
    # grass_utils.import_raster(os.path.join(feature_dir, 'relief.tif'), 'relief')
    # grass_utils.import_raster(os.path.join(feature_dir, 'discharge.tif'), 'discharge')
    # grass_utils.import_raster(os.path.join(feature_dir, 'distance_to_channel.tif'), 'distance_to_channel')
    # grass_utils.import_raster(os.path.join(feature_dir, 'curv_mean.tif'), 'curv_mean')
    # grass_utils.import_raster(os.path.join(feature_dir, 'curv_planform.tif'), 'curv_planform')
    # grass_utils.import_raster(os.path.join(feature_dir, 'curv_profile.tif'), 'curv_profile')
    # grass_utils.import_raster(os.path.join(feature_dir, 'curv_total.tif'), 'curv_total')
    # grass_utils.import_raster(os.path.join(feature_dir, 'distance_to_active_fault.tif'), 'distance_to_active_fault')

def import_all_features(feature_paths):
    for feature_name, feature_path in feature_paths.items():
        grass_utils.import_raster(feature_path, feature_name)

def subregion_processor(region_id, region_file, output_directory, **kwargs):
    # create output directory
    region_out_dir = os.path.join(output_directory, region_id)
    setup_dir(region_out_dir)

    # 1. import region boundary into GRASS
    grass_utils.import_vector(region_file, region_id)

    # 2. update bounds to sub-region
    grass_utils.set_subregion_bounds(region_id, 'elevation')

    # 7. crop and export MAP, PGA, soil data
    crop_and_export('PGA', region_id, os.path.join(region_out_dir, 'PGA.tif'))
    crop_and_export('MAP', region_id, os.path.join(region_out_dir, 'MAP.tif'))
    crop_and_export('aspect_map', region_id, os.path.join(region_out_dir, 'aspect.tif'))
    crop_and_export('elevation', region_id, os.path.join(region_out_dir, 'elevation.tif'))
    crop_and_export('relief', region_id, os.path.join(region_out_dir, 'relief.tif'))
    crop_and_export('slope', region_id, os.path.join(region_out_dir, 'slope.tif'))
    crop_and_export('discharge', region_id, os.path.join(region_out_dir, 'discharge.tif'))
    crop_and_export('distance_to_channel', region_id, os.path.join(region_out_dir, 'distance_to_channel.tif'))
    crop_and_export('curv_mean', region_id, os.path.join(region_out_dir, 'curv_mean.tif'))
    crop_and_export('curv_planform', region_id, os.path.join(region_out_dir, 'curv_planform.tif'))
    crop_and_export('curv_profile', region_id, os.path.join(region_out_dir, 'curv_profile.tif'))
    crop_and_export('curv_total', region_id, os.path.join(region_out_dir, 'curv_total.tif'))
    crop_and_export('distance_to_active_fault', region_id, os.path.join(region_out_dir, 'distance_to_active_fault.tif'))
    crop_and_export('NEE', region_id, os.path.join(region_out_dir, 'nee.tif'))
    crop_and_export('sm_day_before', region_id, os.path.join(region_out_dir, 'soil_moisture_day_before.tif'))
    crop_and_export('sand', region_id, os.path.join(region_out_dir, 'sand.tif'))
    crop_and_export('silt', region_id, os.path.join(region_out_dir, 'silt.tif'))
    crop_and_export('clay', region_id, os.path.join(region_out_dir, 'clay.tif'))

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

    # configure output directory
    setup_dir(output_dir)

    region_list = get_region_files(regions_dir)
    for region_id in region_list:
        print('Processing region: ', region_id)
        subregion_processor(region_id, os.path.join(regions_dir, f'{region_id}.shp'), output_dir)

if __name__ == "__main__":
    # handle arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--regions_dir', type=str, required=True)
    parser.add_argument('--data_json_path', type=str, required=True)
    args = parser.parse_args()

    process_subregions(args.data_json_path, args.regions_dir, args.output_dir)