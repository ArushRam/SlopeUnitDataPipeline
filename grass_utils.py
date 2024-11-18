import grass.script as gs
import grass
import logging
import os

def generate_flags(flag_list = None, **kwargs):
    flags = ''.join(flag_list) if flag_list else ''
    if 'verbose' in kwargs and kwargs['verbose']:
        flags += 'v'
    if 'overwrite' in kwargs and kwargs['overwrite']:
        flags += 'w'

def apply_region_mask(mask_name, **kwargs):
    logging.info(f"Applying Mask: {mask_name}")
    flags = generate_flags([], **kwargs)
    try:
        gs.run_command('r.mask', vector=mask_name, flags=flags)
    except grass.exceptions.CalledModuleError:
        gs.run_command('r.mask', flags=['r']) # remove existing mask
        gs.run_command('r.mask', vector=mask_name, flags=flags)

def remove_region_mask(mask_name, **kwargs):
    logging.info(f"Removing Mask: {mask_name}")
    flags = generate_flags(['r'], **kwargs)
    gs.run_command('r.mask', flags=flags)

def rasterize_vmap(vector_name, binarize=False, **kwargs):
    logging.info(f"Rasterizing vector {vector_name}")
    flags = generate_flags(['o'], **kwargs)
    gs.run_command('v.to.rast',
        input = vector_name,
        output = 'temp_raster',
        flags = flags,
        overwrite=True,
        use = 'cat'
    )
    if binarize:
        gs.run_command('r.mapcalc', expression = f"{vector_name}_raster = if(isnull(temp_raster), 0, 1)", overwrite=True)
        gs.run_command('g.remove', type='raster', name='temp_raster', flags=['f'])
    else:
        gs.run_command('g.rename', raster=f'temp_raster,{vector_name}_raster', overwrite=True)


def import_vector(input_file, map_name, **kwargs):
    logging.info(f"Importing vector {map_name}")
    flags = generate_flags(['w'], **kwargs)
    gs.run_command('v.import',
        input = input_file,
        output = map_name,
        overwrite = True,
        flags = flags
    )

def export_raster(map_name, output_file, **kwargs):
    logging.info(f"Exporting raster {map_name} to {output_file}.tif")
    flags = generate_flags(['o'], **kwargs)
    gs.run_command('r.out.gdal',
        input = map_name,
        output = output_file,
        format = 'GTiff',
        flags = flags,
        overwrite=True,
    )

def set_subregion_bounds(region_id):
    apply_region_mask(region_id, verbose=True)
    gs.run_command('g.region', vector=region_id, flags='p')
    # maybe extend the region a little bit so that post-processing, slope units have appropriate boundaries
    region = gs.region()
    margin = 2000
    new_region = {
        'e': region['e'] + margin,
        'w': region['w'] - margin,
        'n': region['n'] + margin,
        's': region['s'] - margin,
        'nsres': region['nsres'],
        'ewres': region['ewres']
    }
    gs.run_command('g.region', n=new_region['n'], s=new_region['s'], e=new_region['e'], w=new_region['w'], res=new_region['nsres'], flags='p')

def run_slopeunits(
        demmap,
        slumap,
        thresh = 1000000,
        cvmin = 0.5,
        areamin = 10000,
        areamax = 300000,
        rf = 10,
        maxiteration = 10,
        flags = None,
        **kwargs
    ):
    '''
    Run r.slopeunits on provided arguments.
    '''
    kwargs['overwrite'] = True
    flags = generate_flags([], **kwargs)
    gs.run_command('r.slopeunits',
        demmap = demmap, slumap = slumap, thresh = thresh, cvmin = cvmin, areamin = areamin, areamax = areamax, rf = rf, maxiteration = maxiteration, flags = flags, **kwargs
    )

# `r.slopeunits --overwrite demmap=elev30m@PERMANENT slumap=slope_units_6_10k thresh=500000 cvmin=0.6 areamin=10000 areamax=1000000 rf=10 maxiteration=1000`
