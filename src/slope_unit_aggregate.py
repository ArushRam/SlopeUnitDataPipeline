import numpy as np
import pandas as pd
import os
import rasterio
import argparse
import pickle

feature_filenames = [
    'aspect', 'curv_mean', 'curv_planform', 'curv_total', 'curv_profile', 'distance_to_active_fault', 'distance_to_channel', 'elevation', 'MAP', 'nee', 'PGA', 'relief', 'slope', 'soil_moisture_day_before', 'silt', 'clay', 'sand'
]

def load_tif_numpy(filepath, crop_edgecols=False):
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

def compute_slopeunit_centroids(raster_path):
    """
    Reads a slope-units raster from 'raster_path', where each slope unit
    is identified by a unique integer ID. Computes the centroid
    (x, y) in map coordinates for each ID.
    
    Returns
    -------
    centroids : dict
        Dictionary keyed by slope-unit ID, with values = (x, y) centroid.
    """
    with rasterio.open(raster_path) as src:
        slope_units = src.read(1)  # read the first (and only) band
        transform = src.transform
        # If needed, check src.crs for the coordinate system

    unique_ids = np.unique(slope_units)
    centroids = np.zeros((len(unique_ids), 2), dtype=np.float64)
    for uid in unique_ids:
        if np.any(slope_units == uid) == 0:
            continue
        # Get all pixels belonging to this slope unit
        rows, cols = np.where(slope_units == uid)
        if len(rows) == 0:
            continue  # skip if empty for some reason
        # Compute the mean row and column
        mean_row = rows.mean()
        mean_col = cols.mean()
        # Convert (row,col) → (x,y) using the geotransform
        # You can do this manually or use rasterio's transform machinery:
        # x, y = transform * (col, row)
        x, y = rasterio.transform.xy(transform, mean_row, mean_col, offset='center')
        centroids[uid-1] = (x, y)
    return slope_units, centroids

def aggregate_slope_units(base_dir, output_dir):
    for region in os.listdir(base_dir):
        region_path = os.path.join(base_dir, region)
        if region[0] == '.' or not os.path.isdir(region_path):  # Check if it's a directory
            continue
        region_data = {}
        region_data['slopeunits'], region_data['centroids'] = compute_slopeunit_centroids(os.path.join(region_path, 'slopeunits.tif'))
        region_data['features'], region_data['names'] = stack_tif_files(region_path, feature_filenames)
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

        with open(os.path.join(output_dir, region) + '.pkl', 'wb') as f:
            pickle.dump(region_data, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--base_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    args = parser.parse_args()
    aggregate_slope_units(args.base_dir, args.output_dir)