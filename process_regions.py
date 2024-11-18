from setup import *
import grass_utils
import grass.script as gs
import argparse
import os

def process_subregion(region_id, region_file, inventory_name, output_directory, **kwargs):
    # create output directory
    region_out_dir = os.path.join(output_directory, region_id)
    setup_dir(region_out_dir)

    # 1. import region boundary into GRASS
    grass_utils.import_vector(region_file, region_id)

    # 2. update bounds to sub-region
    grass_utils.set_subregion_bounds(region_id)

    # 3. rasterize landslide inventory
    grass_utils.rasterize_vmap(inventory_name, verbose=True, binarize=True)
    grass_utils.export_raster(f'{inventory_name}_raster', 
        output_file=os.path.join(region_out_dir, 'inventory.tif')
    )

    # 4. rasterize region bounds
    grass_utils.rasterize_vmap(region_id, verbose=True)
    grass_utils.export_raster(f'{region_id}_raster', 
        output_file=os.path.join(region_out_dir, 'region.tif')
    )
    
    # 5. generate slope units
    # TODO: call r.slopeunits to generate subregion units
    slu_map = f'{region_id}_slu'
    grass_utils.run_slopeunits(
        demmap = kwargs['dem'],
        slumap = slu_map,
        thresh = 1e6,
        cvmin = 0.5,
        areamin = 1e4,
        areamax = 5e5,
        rf = 10,
        maxiteration = 10,
        overwrite = True
    )

    # 6. rasterize and store slopeunits
    grass_utils.export_raster(slu_map, 
        output_file=os.path.join(region_out_dir, 'slopeunits.tif')
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

    region_list = get_region_files(args.regions_dir)
    for region_id in region_list:
        print('Processing region: ', region_id)
        process_subregion(region_id, os.path.join(args.regions_dir, f'{region_id}.shp'), inventory, args.output_dir, dem=dem)

if __name__ == "__main__":
    main()