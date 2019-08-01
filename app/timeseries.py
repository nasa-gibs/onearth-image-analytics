import requests
from owslib.wmts import WebMapTileService
import imageio
import numpy as np
import matplotlib.pyplot as plt
import xmltodict

from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap

import json
import datetime

import pdb
from contextlib import contextmanager
import traceback
import sys
import scipy.stats
# from utils import ACCESS_LOG, ERROR_LOG
import dateutil

capabilities_url = "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml"
# capabilities_url = "http://onearth-tile-services/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml"
# capabilities_url = "https://sealevel-nexus.jpl.nasa.gov/onearth/wmts/geo/wmts.cgi?Service=wmts&Request=GetCapabilities"

wmts = WebMapTileService(capabilities_url)

@contextmanager
def debug(do_debug):
    try:
        yield None
    except Exception as e:
        if do_debug:
            print(''.join(traceback.format_exception(e.__class__, e, e.__traceback__)))
            pdb.post_mortem()
            sys.exit(1)
        else:
            raise e
    finally:
        pass

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

def get_tile_wmts(layer, tilematrix = 1, x = 0, y = 0, date="2017-01-01", verbose = False):
    response = wmts.gettile(layer=layer, time=date, tilematrix=tilematrix, row=x, column=y)    
    image = imageio.imread(response.read())
        # headers are at response.info()

    if verbose:
        print("Response received with shape {}, headers {}, and url {}\n".format(image.shape, str(response.info()), response.geturl()))

    return image, response


def hex_to_rgb(value):
    return tuple([int(value[i:i+2], 16) for i in (0, 2, 4)])

def get_cmap(*args, product="gibs", **kwargs):
    if product == "gibs":
        return get_cmap_gibs(*args, **kwargs)
    elif product == "sea-level":
        return get_cmap_sealevel(*args, **kwargs)
    else:
        raise ValueError("invalid product for get_cmap call")

# AVHRR_OI-NCEI-L4-GLOB-v2.0.json
def get_cmap_sealevel(layer, **kwargs):
    colormap = json.loads(requests.get("https://sealevel.nasa.gov/data-analysis-tool/jpl/assets/colorbars/{}.json".format(layer)).content)
    colors = colormap['scale']['colors']
    labels = colormap['scale']['labels']
    values = colormap['scale']['values']

    cmap = np.nan * np.ones((256, 256, 256), dtype=float)

    for hexcode, values in zip(colors, values):
        cmap[hex_to_rgb(hexcode)] = (values[0] + values[1]) / 2

    cmap[(0, 0, 0)] = np.nan
    cmap[(hex_to_rgb("7d00ffFF"))] = np.nan

    map_cache.cache(layer, cmap)
    return cmap

def get_cmap_gibs(layer, nan=True, verbose=False):
    if map_cache.contains(layer):
        if verbose:
            print("Cache hit for layer {}".format(layer))
        return map_cache.lookup(layer)

    base_url = "http://gibs.earthdata.nasa.gov/colormaps/v1.0/{layer}.xml"
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

    fill_color = cmap_body[1]
    index = tuple([int(x) for x in fill_color['@rgb'].split(",")])
    if nan:
        cmap[index] = np.nan
    else:
        cmap[index] = 0


    for entry in cmap_body[2:]:
        color = tuple([int(x) for x in entry['@rgb'].split(",")])
        print(entry)
        x = entry['@value'][1:-1].split(",")

        if len(x) == 1:
            cmap[color] = float(x[0])
        elif len(x) == 2:
            if "INF" in x[0]:
                if "INF" in x[1]:
                    continue
                else:
                    cmap[color] = float(x[1])
            else:
                if "INF" in x[1]:
                    cmap[color] = float(x[0])
                else:
                    cmap[color] = (float(x[0]) + float(x[1])) / 2

    map_cache.cache(layer, cmap)
    return cmap

def invert_cmap(cmap, image):
    # np.unique(img[cmap[image[:,:,0], image[:,:,1], image[:,:,2]] == 0][:,0:3], axis = 0)
    return cmap[image[:,:,0], image[:,:,1], image[:,:,2]]

class Tile:
    def __init__(self, layer, tilematrix = 0, x = 0, y = 0, date="2017-01-01", product="gibs", verbose=False, nan=True, content=None):
        self.layer = layer
        self.tilematrix = tilematrix
        self.x = x
        self.y = y
        self.date = date
        self.verbose = verbose
        self.nan = nan

        if verbose:
            print("Creating Tile for date {} and layer {} and x {} and y {} and tilematrix {}".format(date, layer, x, y, tilematrix))

        if content is not None:
            self.image = imageio.imread(content)
            self.response = None
        else:
            self.image, self.response = get_tile_wmts(self.layer, tilematrix=self.tilematrix, x=self.x, y=self.y, \
                date=self.date, verbose=self.verbose)
        
        self.cmap = get_cmap(self.layer, nan=self.nan, verbose=verbose, product=product)
        
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

# r = requests.get(capabilities_url)
# capabilities = xmltodict.parse(r.content)
# matrixset = capabilities['Capabilities']['Contents']['TileMatrixSet']

# cdict = {x['ows:Identifier'] : {entry['ows:Identifier'] : entry for entry in x['TileMatrix']} for x in matrixset }

import asyncio
from aiohttp import ClientSession
import aiohttp

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()

import time

async def get_all_tiles(layer, date, tilematrix, product="gibs"):
    tilematrixset = list(wmts[layer].tilematrixsetlinks.keys())[0]
    height = wmts.tilematrixsets[tilematrixset].tilematrix[tilematrix].matrixwidth
    width = wmts.tilematrixsets[tilematrixset].tilematrix[tilematrix].matrixheight

    tasks = []
    if product == "gibs":
        base_url = "http://gibs.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi?"
    elif product == "sea-level":
        base_url = "http://sealevel-nexus.jpl.nasa.gov/onearth/wmts/geo/wmts.cgi?"

    start = time.time()

    async with ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        for x in range(width):
            for y in range(height): 
                url = base_url + wmts.buildTileRequest(layer=layer, time=date, row=x, column=y, tilematrix=tilematrix)
                print(url)
                tasks.append(asyncio.ensure_future(fetch(url, session)))

        responses = await asyncio.gather(*tasks)

    end = time.time()
    print("HTTP REQUESTS:", end - start)

    tiles = []
    for response in responses:
        tiles.append(Tile(layer, date=date, tilematrix=tilematrix, content=response, product=product))

    return tiles


class Overview:
    def __init__(self, layer, tilematrix = '0', date="2017-01-01", product="gibs", verbose=False, nan=True, tiles=None):
        self.layer = layer
        self.tilematrix = tilematrix
        self.date = date
        self.verbose = verbose
        self.nan = nan

        if verbose:
            print("Creating Tile for date {} and layer {} and tilematrix {}".format(date, layer, tilematrix))
        
        if tiles is not None:
            self.tiles = tiles
        else:
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(get_all_tiles(layer, date, tilematrix, product=product))
            loop.run_until_complete(future)
            self.tiles = future.result()

    @staticmethod
    async def get_async(layer, tilematrix = '0', date="2017-01-01", verbose=False, nan=True, product="gibs"):
        tiles = await get_all_tiles(layer, date, tilematrix, product=product)
        return Overview(layer, tilematrix=tilematrix, date=date, verbose=verbose, tiles=tiles)

    def mean(self): 
        return np.mean([tile.mean() for tile in self.tiles])

    def max(self):
        return np.max([tile.max() for tile in self.tiles])

    def min(self,):
        return np.min([tile.min() for tile in self.tiles])

# cmap = get_cmap("MODIS_Terra_Brightness_Temp_Band31_Day")
# tile, response = get_tile_wmts("MODIS_Terra_Brightness_Temp_Band31_Day", date="2017-01-14", verbose=False)
# data = invert_cmap(cmap, tile)


# tile = Tile("MODIS_Terra_Brightness_Temp_Band31_Day", date="2017-01-14", verbose=False)

def format_list(list):
    s = ""

    if len(list) == 1:
        return list[0]

    for i, word in enumerate(list):
        if i == len(list) - 1:
            s += " and "
            s += word
        else:
            s += word
            s += ","
    return s

def time_series(layers, tilematrix : str, date1 : str, date2 : str, verbose = False, increment="daily", product="gibs", typ="single"):    
    d1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(date2, "%Y-%m-%d")

    # d1 = datetime.datetime.strptime("2011-01-01", "%Y-%m-%d")
    # d2 = datetime.datetime.strptime("2017-01-01", "%Y-%m-%d")

    dates = []
    delta = d2 - d1  # timedelta

    if increment=="daily":
        for i in range(delta.days + 1):
            dates.append((d1 + datetime.timedelta(days=i)).strftime('%Y-%m-%d'))
    if increment=="monthly":
        for i in range(delta.days // 30 + 1):
            dates.append((d1 + dateutil.relativedelta.relativedelta(months=i)).strftime('%Y-%m-%d'))
    if increment=="annual":
        for i in range(delta.days // 365 + 1):
            dates.append((d1 + dateutil.relativedelta.relativedelta(years=i)).strftime('%Y-%m-%d'))

    data = np.zeros((len(layers), len(dates), 3))
    
    # info = []

    for j, layer in enumerate(layers):
        results = []
        if typ == "global":
            for i, date in enumerate(dates):
                ov = Overview.get_async(layer, date=date, tilematrix=tilematrix, verbose=verbose, product=product)
                results.append(ov)

            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(asyncio.gather(*results))
            loop.run_until_complete(future)
            results = future.result()

        else:
            for i, date in enumerate(dates):
                print(date)
                results.append(get_tile_wmts(layer, date=date)[0])
        
        for i, ov in enumerate(results):
            data[j, i] = np.array([ov.mean(), ov.min(), ov.max()])

    return data, dates, results

def plot(layers, dates, tilematrix, data):
    plt.figure(figsize=(16,5), dpi=100)

    for i, layer in enumerate(layers):
        plt.plot(dates, data[i,:,0], ".-", label=layer)

    plt.gca().set(title="Mean Value for {} and for TileMatrix {}".format(format_list(layers), tilematrix), xlabel="Date", ylabel="Data Value")

    if len(layers) == 2:
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        plt.gca().text(0.02, 0.98, "Correlation: {}".format(scipy.stats.pearsonr(data[0,:,0], data[1,:,0])[0]), transform=plt.gca().transAxes, fontsize=8, verticalalignment='top', bbox=props)

    plt.legend()
    plt.show()

if __name__ == "__main__":
    print("running debug!")
    with debug(True):
        data, dates, ovs = time_series(["AIRS_Methane_Volume_Mixing_Ratio_Daily_Day"], "1", "2012-01-01", "2014-01-01", increment="monthly", typ="single") # , "AIRS_Methane_Volume_Mixing_Ratio_Daily_Day"
        plot(["AIRS_Methane_Volume_Mixing_Ratio_Daily_Day"], dates, "1", data) # , "AIRS_Methane_Volume_Mixing_Ratio_Daily_Day"
        
    # with debug(True):
    #     data, dates, ovs = time_series(["AVHRR_OI-NCEI-L4-GLOB-v2.0"], "1", "2017-01-01", "2017-01-14", increment="daily", product="gibs")
    #     plot(["AVHRR_OI-NCEI-L4-GLOB-v2.0"], dates, "1", data)
