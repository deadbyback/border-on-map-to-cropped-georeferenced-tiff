import math
import urllib.request
import os
import glob
import subprocess
import shutil
import sys
import json
from tile_convert import bbox_to_xyz, tile_edges
from osgeo import gdal
from osgeo import ogr

#---------- CONFIGURATION -----------#

tile_server = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
output_dir = os.path.join(os.path.dirname(__file__), 'output')
zoom = 18
lon_min = 32.0644341554349
lon_max = 32.0744341554349
lat_min = 49.7466314987413
lat_max = 49.7666314987413
#-----------------------------------#

#----------- FUNCTIONS -------------#
def download_tile(x, y, z, tile_server):
    url = tile_server.replace(
        "{x}", str(x)).replace(
        "{y}", str(y)).replace(
        "{z}", str(z))
    print(f"{url}")
    path = f'{temp_dir}/{x}_{y}_{z}.png'
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36')]
    urllib.request.install_opener(opener)

    urllib.request.urlretrieve(url, path)
    return(path)


def merge_tiles(input_pattern, output_path):
    merge_command = ['gdal_merge.py', '-o', output_path]

    for name in glob.glob(input_pattern):
        merge_command.append(name)
    print(f"{merge_command}")
    subprocess.call(merge_command, shell=True)


def georeference_raster_tile(x, y, z, path):
    bounds = tile_edges(x, y, z)
    filename, extension = os.path.splitext(path)
    gdal.Translate(filename + '.tif',
                   path,
                   outputSRS = 'EPSG:4326',
                   rgbExpand = 'RGB',
                   outputBounds=bounds)

def get_extent(raster):
    geoTransform = raster.GetGeoTransform()
    xMin = geoTransform[0]
    yMax = geoTransform[3]
    xMax = xMin + geoTransform[1] * raster.RasterXSize
    yMin = yMax + geoTransform[5] * raster.RasterYSize
    return {'xMax':xMax,'xMin':xMin,'yMax':yMax,'yMin':yMin}

def extent_to_wkt_polygon(extent):
    return 'POLYGON ((%s %s,%s %s,%s %s,%s %s,%s %s))' % (
        extent['xMin'],extent['yMin'],
        extent['xMin'],extent['yMax'],
        extent['xMax'],extent['yMax'],
        extent['xMax'],extent['yMin'],
        extent['xMin'],extent['yMin'])

def crop_raster_by_wkt_polygon(raster,polygon_wkt,output_path):
    geom = ogr.CreateGeometryFromWkt(polygon_wkt)
    extent_json = geom.GetBoundary().ExportToJson()
    extent = json_polygon_to_extent(extent_json)
    print(extent)
    output_raster = gdal.Warp(output_path,
              raster,
              format = 'GTiff',
              outputBounds = [extent['xMin'],extent['yMin'],extent['xMax'],extent['yMax']],
              dstSRS='EPSG:3857',
              outputBoundsSRS='EPSG:4326',
              cutlineLayer = 'extent_json',
              cropToCutline=True,
              dstNodata = 0)
    return output_raster
    

def json_polygon_to_extent(polygon_json):
    x_list = []
    y_list = []
    for pair in json.loads(polygon_json)['coordinates']:
        x_list.append(pair[0])
        y_list.append(pair[1])
    return {'xMax':max(x_list),'xMin':min(x_list),'yMax':max(y_list),'yMin':min(y_list)}

#---------- MAIN LOGIC -------------#
x_min, x_max, y_min, y_max = bbox_to_xyz(
    lon_min, lon_max, lat_min, lat_max, zoom)

print(f"Downloading {(x_max - x_min + 1) * (y_max - y_min + 1)} tiles")

for x in range(x_min, x_max + 1):
    for y in range(y_min, y_max + 1):
        print(f"{x},{y}")
        try:
            png_path = download_tile(x, y, zoom, tile_server)
            georeference_raster_tile(x, y, zoom, png_path)
        except:
            continue

print("Download complete")

print("Merging tiles")
merge_tiles(temp_dir + '/*.tif', output_dir + '/merged.tif')
print("Merge complete")

shutil.rmtree(temp_dir)
os.makedirs(temp_dir)
print("Temporary folder cleaned")

mergedRaster = gdal.Open(output_dir + '/merged.tif')
wktPolygon = 'POLYGON ((%s %s,%s %s,%s %s,%s %s,%s %s))' % (
        lon_min,lat_min,
        lon_min,lat_max,
        lon_max,lat_max,
        lon_max,lat_min,
        lon_min,lat_min)
output_path = output_dir + '/result.tif'

mergedRaster = crop_raster_by_wkt_polygon(mergedRaster,wktPolygon,output_path)
print(mergedRaster)