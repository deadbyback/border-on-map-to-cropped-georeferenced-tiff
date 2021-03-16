# border-on-map-to-cropped-georeferenced-tiff

[![CodeQL](https://github.com/deadbyback/border-on-map-to-cropped-georeferenced-tiff/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/deadbyback/border-on-map-to-cropped-georeferenced-tiff/actions/workflows/codeql-analysis.yml)

Python script for converting XYZ raster tiles for slippy maps to a georeferenced TIFF image.

## Special thanks

The repository was based on <https://github.com/jimutt/tiles-to-tiff>.

## Prerequisites

- GDAL
- Empty "output" and "temp" folders in project directory.

## Usage

- Modify configuration in `tiles_to_tiff.py` according to personal preferences.
- Run script with `$ python tiles_to_tiff.py -lat_min={number} -lat_max={number} -lng_min={number} -lng_max={number} -z={number}`

Be careful with zoom value
