import numpy as np
import pandas as pd
import os
import rasterio
import argparse
import pickle

feature_filenames = [
    'aspect', 'curv_mean', 'curv_planform', 'curv_total', 'curv_profile', 'distance_to_active_fault', 'distance_to_channel', 'elevation', 'MAP', 'nee', 'PGA', 'relief', 'slope', 'soil_moisture_day_before', 'silt', 'clay', 'sand'
]

def load_tif_numpy(filepath, crop_edgecols=True):
    with rasterio.open(filepath) as src:
        arr = src.read(1)
    if crop_edgecols:
        arr = arr[:,1:-1]
    return arr

def stack_tif_files(base_dir, filename):
    """
    Stack multiple .tif raster files into a single 3D numpy array.

    Args:
        file_paths (list of str): List of file paths to the .tif files.

    Returns:
        numpy.ndarray: A 3D numpy array where each slice along the first dimension 
                       corresponds to one .tif file.
    """
    # Initialize a list to hold the arrays
    arrays = []
    for filename in feature_filenames:
        file_path = os.path.join(base_dir, filename) + '.tif'
        arrays.append(load_tif_numpy(file_path).astype(np.float32))
    # Stack all arrays along a new first dimension
    stacked_array = np.stack(arrays, axis=0)
    return stacked_array, feature_filenames

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    args = parser.parse_args()
    base_dir = args.base_dir
    for region in os.listdir(base_dir):
        region_path = os.path.join(base_dir, region)
        if region[0] == '.' or not os.path.isdir(region_path):  # Check if it's a directory
            continue
        region_data = {}
        region_data['features'], region_data['names'] = stack_tif_files(region_path, feature_filenames)
        region_data['slopeunits'] = load_tif_numpy(os.path.join(region_path, 'slopeunits.tif'))
        region_data['inventory'] = load_tif_numpy(os.path.join(region_path, 'inventory.tif'))

        with rasterio.open(os.path.join(region_path, 'region.tif')) as src:
            bounds = src.bounds
            transform = src.transform
            resolution = (transform.a, transform.e)
            crs = src.crs

        region_data['metadata'] = {
            'bounds': bounds,
            'resolution': resolution,
            'crs': crs
        }

        with open(os.path.join(args.output_dir, region) + '.pkl', 'wb') as f:
            pickle.dump(region_data, f)

if __name__ == "__main__":
    main()