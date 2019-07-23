import requests
import numpy as np
import json
import imageio

def hex_to_rgb(value):
    return tuple([int(value[i:i+2], 16) for i in (0, 2, 4)])

def get_colors(layer):
    colormap = json.loads(requests.get("https://sealevel.nasa.gov/data-analysis-tool/jpl/assets/colorbars/{}.json".format(layer)).content)
    colors = colormap['scale']['colors']
    values = colormap['scale']['values']

    c = []
    v = []
    for hexcode, values in zip(colors, values):
        c.append(list(hex_to_rgb(hexcode)))
        v.append((values[0] + values[1]) / 2)

    return np.array(c), np.array(v)


# AVHRR_OI-NCEI-L4-GLOB-v2.0.json
def get_cmap_sealevel(layer, **kwargs):
    colormap = json.loads(requests.get("https://sealevel.nasa.gov/data-analysis-tool/jpl/assets/colorbars/{}.json".format(layer)).content)
    colors = colormap['scale']['colors']
    # labels = colormap['scale']['labels']
    values = colormap['scale']['values']

    cmap = np.nan * np.ones((256, 256, 256), dtype=float)

    for hexcode, values in zip(colors, values):
        cmap[hex_to_rgb(hexcode)] = (values[0] + values[1]) / 2

    cmap[(0, 0, 0)] = np.nan
    cmap[(hex_to_rgb("7d00ffFF"))] = np.nan

    return cmap

def invert_cmap(cmap, image):
    # np.unique(img[cmap[image[:,:,0], image[:,:,1], image[:,:,2]] == 0][:,0:3], axis = 0)
    return cmap[image[:,:,0], image[:,:,1], image[:,:,2]]

layer = "AVHRR_OI-NCEI-L4-GLOB-v2.0"
r = requests.get("https://sealevel-nexus.jpl.nasa.gov/onearth/wmts/geo/wmts.cgi?Service=wmts&Request=GetTile&Version=1.0.0&layer={}&tilematrixset=EPSG4326_1km&Format=image/png&TileMatrix=2&TileCol=1&TileRow=1&TIME=2016-06-01".format(layer))
# cmap = get_cmap_sealevel(layer)
image = imageio.imread(r.content)
colors, values = get_colors(layer)

unique = np.unique(image[:,:,0:3].reshape(-1, 3), axis=0)
diff = (unique.reshape(3, -1, 1) - colors.reshape(3, 1, -1))
mean_r = np.array((unique.reshape(3, -1, 1)[0] + colors.reshape(3, 1, -1)[0]) / 2, dtype=np.uint8)
distance = np.sqrt(np.right_shift(((512+mean_r)*diff[0]*diff[0]), 8) + 4 * diff[1] * diff[1] + np.right_shift(((767-mean_r)*diff[2]*diff[2]), 8))
choice = distance.argmin(axis=1)

cmap = np.nan * np.ones((256, 256, 256), dtype=float)
for i, entry in enumerate(unique):
    cmap[tuple(entry)] = values[choice[i]]

cmap[0, 0, 0] = np.nan

for date in ["2016-06-01", "2016-07-01", "2016-08-01"]:
    r = requests.get("https://sealevel-nexus.jpl.nasa.gov/onearth/wmts/geo/wmts.cgi?Service=wmts&Request=GetTile&Version=1.0.0&layer={}&tilematrixset=EPSG4326_1km&Format=image/png&TileMatrix=2&TileCol=1&TileRow=1&TIME={}".format(layer, date))
    image = imageio.imread(r.content)
    print("mean is {}".format(np.nanmean(invert_cmap(cmap, image))))
# data = invert_cmap(cmap, image)