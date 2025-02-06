import os
import argparse

from utils import setup_dir, clean_dir
from grass_region_processor import process_subregions
from slope_unit_aggregate import aggregate_slope_units
from slope_unit_processor import process_slopeunits

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, required=True)
    parser.add_argument('--region_vector_dir', type=str, required=True)
    parser.add_argument('--data_json_path', type=str, required=True)
    parser.add_argument('--min_slu_count', type=int, default=5)
    parser.add_argument('--clean_dumps', action='store_true')
    args = parser.parse_args()

    raw_dump_dir = os.path.join(args.output_dir, 'dump_raw')
    setup_dir(raw_dump_dir)
    process_subregions(args.data_json_path, args.region_vector_dir, raw_dump_dir)

    aggregated_dump_dir = os.path.join(args.output_dir, 'dump_aggregated')
    setup_dir(aggregated_dump_dir)
    aggregate_slope_units(raw_dump_dir, aggregated_dump_dir)

    output_dir = os.path.join(args.output_dir, 'output')
    setup_dir(output_dir)
    process_slopeunits(aggregated_dump_dir, output_dir, min_slu_count=args.min_slu_count, data_json_path=args.data_json_path)

    # clean up
    if args.clean_dumps:
        clean_dir(raw_dump_dir)
        clean_dir(aggregated_dump_dir)

if __name__ == "__main__":
    main()