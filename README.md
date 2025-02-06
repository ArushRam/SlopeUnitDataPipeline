# Slopeunits Processing Pipeline

## Setup

### Grass Setup

Ensure GRASS GIS is installed in your system, and set up with the `r.slopeunits` package. Create a GRASS session identified by a unique pairing of (Location, Mapset). This information is then entered into the `slopeunits.ini` configuration file as follows.

- `GISBASE`: path to base GIS folder. On MacOS, this path might look like: `/Applications/GRASS-7.8.app/Contents/Resources/`.
- `MAPSET`: GRASS GIS mapset (e.g. `PERMANENT`)
- `LOCATION`: GRASS GIS location
- `GISDB`: GRASS database path

### Data

Mandatory files include a digital elevation model (DEM) and a landslide inventory. These paths are specified in `data_files.json` as shown. In addition, paths to feature raster files (`.tif`) may be listed in the `features` sub-dictionary, with appropriate names.

## Usage

