import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import rasterio
import os
import argparse

def map_raster_to_slu(raster, slope_units, reduce_fn=np.mean, get_im=False):
    raster = raster.astype(np.float32)
    n_units = len(np.unique(slope_units))
    feature_table = np.zeros(n_units, dtype=raster.dtype)
    for i in range(n_units):
        if np.any(slope_units == i+1) == 0:
            continue
        feature_table[i] = reduce_fn(raster[slope_units == i+1])
    if get_im:
        feature_im = np.zeros_like(raster)
        for i in range(n_units):
            if np.any(slope_units == i+1) == 0:
                continue
            feature_im[slope_units == i+1] = feature_table[i]
        return feature_table, feature_im
    return feature_table

def process_region_slopeunits(region_file, min_count, out_file):

    with open(region_file, 'rb') as f:
        region = pickle.load(f)

    slopeunits = region['slopeunits']
    y = region['inventory']
    X = region['features']
    feature_names = region['names']
    metadata = region['metadata']

    y_slu = map_raster_to_slu(y, slopeunits, reduce_fn=np.mean)
    counts_slu = map_raster_to_slu(np.ones_like(y), slopeunits, reduce_fn=np.sum)

    extreme_features = ['slope', 'curv_mean', 'curv_total', 'curv_profile', 'drainage_area']
    feats, new_feat_names = [], []
    for i, feat in enumerate(feature_names):
        feat_mean = map_raster_to_slu(X[i], slopeunits, reduce_fn=np.mean)
        feat_var = map_raster_to_slu(X[i], slopeunits, reduce_fn=np.var)
        feats += [feat_mean, feat_var]
        new_feat_names += [f'{feat}_mean', f'{feat}_var']
        if feat in extreme_features:
            feat_min = map_raster_to_slu(X[i], slopeunits, reduce_fn=np.min)
            feat_max = map_raster_to_slu(X[i], slopeunits, reduce_fn=np.max)
            feats += [feat_min, feat_max]
            new_feat_names += [f'{feat}_min', f'{feat}_max']
    feats = np.stack(feats)

    mask = counts_slu >= min_count
    feats = feats[:,mask]
    y_slu = y_slu[mask]
    counts_slu = counts_slu[mask]
    X_slu = pd.DataFrame(feats, index=new_feat_names).T

    data_dict = {
        'X': X_slu,
        'y': y_slu,
        'counts': counts_slu,
        'slope_units': slopeunits,
        'metadata': metadata,
    }

    with open(out_file, 'wb') as f:
        pickle.dump(data_dict, f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, required=True)
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--min_slu_count', type=int, default=5)
    args = parser.parse_args()

    for region in os.listdir(args.input_dir):
        print('Processing region: ', region.split('.')[0])
        if region[0] == '.':
            continue
        region_file = os.path.join(args.input_dir, region)
        output_file = os.path.join(args.output_dir, region)
        process_region_slopeunits(region_file, args.min_slu_count, output_file)

if __name__ == "__main__":
    main()