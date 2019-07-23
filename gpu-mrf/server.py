import scipy.io
import numpy as np
import imageio
import sys
import torch
import time
import pickle

import requests
import xmltodict

from flask import Flask, render_template, flash, redirect, session, url_for, request, g, Markup, jsonify

import requests
import sys
import time
import os
import struct
import math

app = Flask(__name__)

def get_cmap(layer, nan=True, verbose=False):
    with open('cmap.xml', "rb") as f:
        data = f.read()

    cmap = xmltodict.parse(data)
    cmap_body = cmap['ColorMap']['ColorMapEntry']

    cmap = np.zeros((214,3), dtype=np.uint8)

    for i, entry in enumerate(cmap_body[1:-1]):
        color = tuple([int(x) for x in entry['@rgb'].split(",")])
        x = [int(x) for x in entry['@rgb'].split(",")]
        cmap[i] = x

    return cmap

def get_data(name): # temporarily, load pickled data. Can also load from NetCDF (same cost).
    with open("data.pickle", "rb") as f:
        return torch.Tensor(pickle.load(f)[::-1].copy())

# offset = file.variables["analysed_sst"].add_offset
# scale = file.variables["analysed_sst"].scale_factor
# missing = file.variables["analysed_sst"]._get_missing_value()

class TileCache:
    def __init__(self, maxsize=1E9, verbose=False):
        self.verbose = verbose
        self._cache = {}
        self._size = 0
        self._maxsize = maxsize

    def clear(self):
        self._cache = {}
        self._size = 0

    def store(self, col, row, matrix, tile):
        if self._size + self._size > self._maxsize:
            self.clear()

        self._size += self.tilesize(tile)
        self._cache["{}-{}-{}".format(col, row, matrix)] = tile

    def get(self, col, row, matrix):
        return self._cache["{}-{}-{}".format(col, row, matrix)]

    def contains(self, col, row, matrix):
        return "{}-{}-{}".format(col, row, matrix) in self._cache

    def tilesize(self, tile):
        return tile.size * tile.itemsize

    def size(self):
        return self._size

class Product:
    def __init__(self, name):
        self.name = name

        self.offset = 298.15
        self.scale = 0.001
        self.missing = -32768

        self.cmap = torch.Tensor(get_cmap(self.name)).cuda().to(torch.uint8)
        self.data = get_data(self.name).to(torch.int16)
        self.cache = TileCache()
        self.shape = self.data.shape

        print("Loaded Product {} with shape {}".format(self.name, self.shape))

    def getshape(self, tilecolumn, tilerow, tilematrix):
        size = max(self.shape) // (2 ** tilematrix)
        print(size * tilerow, min(size * (tilerow + 1), self.shape[1]), size * tilecolumn, min(size * (tilecolumn + 1), self.shape[1]))
        return self.data[size * tilerow : min(size * (tilerow + 1), self.shape[1]), size * tilecolumn : min(size * (tilecolumn + 1), self.shape[1])]

    def mrfgen(self, num_overviews, config=None):
        if config is None:
            device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
        else:
            if config.get("device", "cpu") == "cuda" and not torch.cuda._is_available():
                raise ValueError("Configuration backend was cuda but cuda is not available")

            device = torch.device("cuda:0") if config.get("device", "cuda") == "cuda" else torch.device("cpu")

        data = self.data.to(device).float()
        data = data.mul_(self.scale).add_(self.offset)
        data = data.sub_(273.15).clamp_(min=0.0, max=100.0)
        data = data.sub_(data.min()).div_(data.max()).mul_(len(self.cmap) - 1).long()
        data = self.cmap[data]
        
        idx_file = open(name + ".idx", "wb")
        data_file = open(name + ".pjg", "wb")

        steps = [(math.ceil(self.shape[0] // 2 ** i / 512), math.ceil(self.shape[1] // 2 ** i / 512)) for i in range(num_overviews)]
        print(steps)

        for i, (numrows, numcols) in enumerate(steps):
            scaled = data[:: 2 ** i, :: 2 ** i].cpu().numpy() # can also downsample by a factor of two each time
            
            ax, ay = np.meshgrid(np.arange(numrows), np.arange(numcols))
            entries = np.stack([ax.flatten(), ay.flatten()], axis=1)
            print(i, numrows, numcols, 2 ** i)

            for j, (row, col) in enumerate(entries):
                # breakpoint()
                tile = scaled[row * 512 : (row + 1) * 512, col * 512 : (col + 1) * 512]
                empty = np.zeros((512, 512, 3), dtype=np.uint8)
                empty[0 : tile.shape[0], 0: tile.shape[1]] = tile
                # breakpoint()  
                
                pos = data_file.tell()
                imageio.imwrite(data_file, empty, format="png")
                # success, buffer = cv2.imencode(".jpg", empty)
                # buffer.tofile(data_file)
                size = data_file.tell() - pos
                idx_file.write(struct.pack("Q", pos))
                idx_file.write(struct.pack("Q", size))
                
        idx_file.close()
        data_file.close()
        
    def gettile(self, tilecolumn, tilerow, tilematrix, config=None):
        """config:
            device (str) -- cuda or cpu
            min_value (float) -- minimum value to set
            max_value (float) -- maximum value to set
            use_cache (bool) -- should use cache regardless of configuration
        """
        
        if config is None:
            device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
            min_value = 0.0
            max_value = 100.0
            use_cache = True
        else:
            if config.get("device", "cpu") == "cuda" and not torch.cuda._is_available():
                raise ValueError("Configuration backend was cuda but cuda is not available")

            device = torch.device("cuda:0") if config.get("device", "cuda") == "cuda" else torch.device("cpu")
            min_value = float(config.get("min_value", 0.0))
            max_value = float(config.get("max_value", 100.0))
            use_cache = True if config.get("use_cache", "True") == "True" else False

        if use_cache and self.cache.contains(tilecolumn, tilerow, tilematrix):
            return self.cache.get(tilecolumn, tilerow, tilematrix)
        
        # s = time.time()
        src = self.getshape(tilecolumn, tilerow, tilematrix).to(device).float()
        # e = time.time()

        # print("copy took {} seconds".format(e - s))
        
        src = src * self.scale + self.offset

        # print("mean is {}, max is {}, min is {}".format(src.mean(), src.max(), src.min()))

        # src = ((src - 273.15) / 0.15).clamp_(min=0, max=len(self.cmap) - 1)
        src = (src - 273.15).clamp_(min=min_value, max=max_value)
        src = src.sub_(src.min()).div_(src.max()).mul_(len(self.cmap) - 1)
        src = src.long()
                
        image = self.cmap[src]
        size = max(self.shape) // (2 ** tilematrix)

        # sizes = [size // (2 ** tilematrix) for size in shape]

        low = image[:: size // 512, :: size // 512]

        # s2 = time.time()
        empty = torch.zeros((512, 512, 3), device=device, dtype=torch.uint8)
        # empty = torch.ByteTensor(512, 512, 3).fill_(0)
        empty[0:low.shape[0], 0:low.shape[1]] = low
        final = empty.cpu().numpy()
        # e2 = time.time()

        # print("copy back took {} seconds".format(e2 - s2))

        if use_cache:
            self.cache.store(tilecolumn, tilerow, tilematrix, final)

        return final
        
name = "GHRSST_L4_MUR_Sea_Surface_Temperature"
product = Product("GHRSST_L4_MUR_Sea_Surface_Temperature")

@app.route("/wmts")
def wmts():
    args = request.args
    tilecol = int(args["TileCol"])
    tilerow = int(args["TileRow"])
    tilematrix = int(args['TileMatrix'])

    with torch.no_grad():
        s = time.time()
        tile = product.gettile(tilecol, tilerow, tilematrix, config = {key : args[key] for key in ["device", "min_value", "max_value", "use_cache"] if key in args})
        e = time.time()

        print("Retrieving tilecol {} tilerow {} tilematrix {} took {} seconds".format(tilecol, tilerow, tilematrix, e - s))

        tile = imageio.imwrite(imageio.RETURN_BYTES, tile, format="png")

    return tile, 200, {'Content-Type' : 'image/png'}
    

if __name__ == "__main__":
    product.mrfgen(7)
    
#     while True:
#         print("enter tilecolumn: ", end="")
#         tilecol = int(input())

#         print("enter tilerow: ", end="")
#         tilerow = int(input())

#         print("enter tilematrix: ", end="")
#         tilematrix = int(input())

#         s = time.time()
#         tile = product.gettile(tilecol, tilerow, tilematrix)
#         e = time.time()

#         print("Retrieving tilecol {} tilerow {} tilematrix {} took {} seconds".format(tilecol, tilerow, tilematrix, e - s))

#         imageio.imwrite("exampledown.png", tile)
