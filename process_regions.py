from setup import *
import grass_utils
import grass.script as gs
import argparse
import os

def crop_and_export(raster_name, mask_name, file_path, **kwargs):
    cropped_name = grass_utils.crop_raster(raster_name, mask_name)
    grass_utils.export_raster(cropped_name, output_file=file_path, **kwargs)

def import_derived_features(derived_dir):
    grass_utils.import_raster(os.path.join(derived_dir, 'aspect.tif'), 'aspect_map')
    grass_utils.import_raster(os.path.join(derived_dir, 'slope.tif'), 'slope')
    grass_utils.import_raster(os.path.join(derived_dir, 'relief.tif'), 'relief')
    grass_utils.import_raster(os.path.join(derived_dir, 'discharge.tif'), 'discharge')
    grass_utils.import_raster(os.path.join(derived_dir, 'distance_to_channel.tif'), 'distance_to_channel')
    grass_utils.import_raster(os.path.join(derived_dir, 'curv_mean.tif'), 'curv_mean')
    grass_utils.import_raster(os.path.join(derived_dir, 'curv_planform.tif'), 'curv_planform')
    grass_utils.import_raster(os.path.join(derived_dir, 'curv_profile.tif'), 'curv_profile')
    grass_utils.import_raster(os.path.join(derived_dir, 'curv_total.tif'), 'curv_total')
    grass_utils.import_raster(os.path.join(derived_dir, 'distance_to_active_fault.tif'), 'distance_to_active_fault')

def process_subregion(region_id, region_file, inventory_name, output_directory, **kwargs):
    # create output directory
    region_out_dir = os.path.join(output_directory, region_id)
    setup_dir(region_out_dir)

    # 1. import region boundary into GRASS
    grass_utils.import_vector(region_file, region_id)

    # 2. update bounds to sub-region
    grass_utils.set_subregion_bounds(region_id, kwargs['dem'])

    # 7. crop and export MAP, PGA, soil data
    crop_and_export('masked_MAP', region_id, os.path.join(region_out_dir, 'MAP.tif'))
    crop_and_export('masked_pga', region_id, os.path.join(region_out_dir, 'PGA.tif'))
    crop_and_export('aspect_map', region_id, os.path.join(region_out_dir, 'aspect.tif'))
    crop_and_export(kwargs['dem'], region_id, os.path.join(region_out_dir, 'elevation.tif'))
    crop_and_export('relief', region_id, os.path.join(region_out_dir, 'relief.tif'))
    crop_and_export('slope', region_id, os.path.join(region_out_dir, 'slope.tif'))
    crop_and_export('discharge', region_id, os.path.join(region_out_dir, 'discharge.tif'))
    crop_and_export('distance_to_channel', region_id, os.path.join(region_out_dir, 'distance_to_channel.tif'))
    crop_and_export('curv_mean', region_id, os.path.join(region_out_dir, 'curv_mean.tif'))
    crop_and_export('curv_planform', region_id, os.path.join(region_out_dir, 'curv_planform.tif'))
    crop_and_export('curv_profile', region_id, os.path.join(region_out_dir, 'curv_profile.tif'))
    crop_and_export('curv_total', region_id, os.path.join(region_out_dir, 'curv_total.tif'))
    crop_and_export('distance_to_active_fault', region_id, os.path.join(region_out_dir, 'distance_to_active_fault.tif'))
    crop_and_export('nee', region_id, os.path.join(region_out_dir, 'nee.tif'))

    # 3. rasterize landslide inventory
    grass_utils.rasterize_vmap(inventory_name, verbose=True, binarize=True)
    grass_utils.export_raster(f'{inventory_name}_raster', 
        output_file=os.path.join(region_out_dir, 'inventory.tif'), type='UInt16'
    )

    # 4. rasterize region bounds
    grass_utils.rasterize_vmap(region_id, verbose=True)
    grass_utils.export_raster(f'{region_id}_raster', output_file=os.path.join(region_out_dir, 'region.tif'), type='UInt16')
    
    # 5. generate slope units
    slu_map = f'{region_id}_slu'
    grass_utils.run_slopeunits(
        demmap = kwargs['dem'],
        slumap = slu_map,
        thresh = 1e6,
        cvmin = 0.5,
        areamin = 1e4,
        areamax = 5e5,
        rf = 10,
        maxiteration = 20,
        overwrite = True
    )

    # 6. rasterize and store slopeunits
    grass_utils.set_subregion_bounds(region_id, kwargs['dem'])
    grass_utils.export_raster(slu_map, 
        output_file=os.path.join(region_out_dir, 'slopeunits_20.tif'), type='UInt32'
    )

def main():
    # handle arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--regions_dir', type=str, required=True)
    args = parser.parse_args()

    # configure output directory
    setup_dir(args.output_dir)
    dem = config_manager.get('DEM')
    inventory = config_manager.get('INVENTORY')
    derived_features_dict = config_manager.get('DERIVED_FEATURES_DICT')

    # import_derived_features(derived_features_dict)
    grass_utils.import_raster('/Users/arushramteke/Desktop/Wenchuan/MAP/nee.tif', 'nee')

    region_list = get_region_files(args.regions_dir)
    for region_id in region_list:
        print('Processing region: ', region_id)
        process_subregion(region_id, os.path.join(args.regions_dir, f'{region_id}.shp'), inventory, args.output_dir, dem=dem)

if __name__ == "__main__":
    main()