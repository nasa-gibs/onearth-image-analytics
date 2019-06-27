import requests
from owslib.wmts import WebMapTileService
import imageio
import numpy as np
import matplotlib.pyplot as plt
import xmltodict

from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import scipy.sparse

import datetime

capabilities_url = "http://localhost/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml"
# capabilities_url = "https://sealevel-nexus.jpl.nasa.gov/onearth/wmts/geo/wmts.cgi?Service=wmts&Request=GetCapabilities"
wmts = WebMapTileService(capabilities_url)

class CMapCache:
    def __init__(self, max_maps = None):
        if max_maps and max_maps <= 0:
            raise ValueError("max_maps parameter should be greater than zero.")

        self.max_maps = max_maps
        self.maps = {}
        self.num = 0

    def clear_cache(self):
        self.maps = {}
        self.num = 0

    def cache(self, name, map):
        if self.max_maps and self.num >= self.max_maps:
            self.clear_cache()
        
        self.maps[name] = map
        self.num += 1
        
    def contains(self, name):
        return name in self.maps

    def lookup(self, name):
        if name in self.maps:
            return self.maps[name]
        else:
            return None

map_cache = CMapCache()

def get_tile_wmts(layer, tilematrix = 0, x = 0, y = 0, date="2017-01-01", verbose = False):
    response = wmts.gettile(layer=layer, time=date, tilematrix=tilematrix, row=x, column=y)    
    # headers are at response.info()

    image = imageio.imread(response.read())

    if verbose:
        print("Response received with shape {}, headers {}, and url {}\n".format(image.shape, str(response.info()), response.geturl()))

    return image, response

def get_cmap(layer, nan=True):
    if map_cache.contains(layer):
        return map_cache.lookup(layer)

    base_url = "https://gibs.earthdata.nasa.gov/colormaps/v1.0/{layer}.xml"
    url = base_url.format(layer=layer)
    r = requests.get(url)
    r.raise_for_status()

    cmap = xmltodict.parse(r.content)
    cmap_body = cmap['ColorMap']['ColorMapEntry']

    cmap = np.zeros((256, 256, 256), dtype=float)

    fill_color = cmap_body[0]
    index = tuple([int(x) for x in fill_color['@rgb'].split(",")])
    if nan:
        cmap[index] = np.nan
    else:
        cmap[index] = 0

    for entry in cmap_body[1:]:
        color = tuple([int(x) for x in entry['@rgb'].split(",")])
        x = entry['@value'][1:-1].split(",")
        cmap[color] = (float(x[0]) + float(x[1])) / 2

    map_cache.cache(layer, cmap)
    return cmap

def invert_cmap(cmap, image):
    return cmap[image[:,:,0], image[:,:,1], image[:,:,2]]

class Tile:
    def __init__(self, layer, tilematrix = 0, x = 0, y = 0, date="2017-01-01", verbose=False, nan=True):
        self.layer = layer
        self.tilematrix = tilematrix
        self.x = x
        self.y = y
        self.date = date
        self.verbose = verbose
        self.nan = nan

        self.image, self.response = get_tile_wmts(self.layer, tilematrix=self.tilematrix, x=self.x, y=self.y, \
            date=self.date, verbose=self.verbose)
        
        self.cmap = get_cmap(self.layer, nan=self.nan)
        self.data = invert_cmap(self.cmap, self.image)
    
    def mean(self):
        return np.nanmean(self.data)

    def max(self):
        return np.nanmax(self.data)

    def min(self,):
        return np.nanmin(self.data)

    def var(self):
        return np.nanvar(self.data)

    def get_image(self):
        return self.image

    def get_url(self):
        return self.response._response.url


# cmap = get_cmap("MODIS_Terra_Brightness_Temp_Band31_Day")
# tile, response = get_tile_wmts("MODIS_Terra_Brightness_Temp_Band31_Day", date="2017-01-14", verbose=False)
# data = invert_cmap(cmap, tile)

tile = Tile("MODIS_Terra_Brightness_Temp_Band31_Day", date="2017-01-14", verbose=False)

d1 = datetime.datetime.strptime("2017-01-01", "%Y-%m-%d")
d2 = datetime.datetime.strptime("2017-01-14", "%Y-%m-%d")

dates = []
delta = d2 - d1  # timedelta

for i in range(delta.days + 1):
    dates.append((d1 + datetime.timedelta(days=i)).strftime('%Y-%m-%d'))

info = np.zeros((len(dates), 4))

for i, date in enumerate(dates):
    tile = Tile("MODIS_Terra_Brightness_Temp_Band31_Day", date=date, verbose=False)
    info[i] = np.array([tile.mean(), tile.min(), tile.max(), tile.var()])

print(f"Mean: {tile.mean()}, Min: {tile.min()}, Max: {tile.max()}")

