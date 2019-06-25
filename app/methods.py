import io
import skimage
from skimage.color.adapt_rgb import adapt_rgb, each_channel
from utils import read_image, write_image, ACCESS_LOG, ERROR_LOG, timeit, log_request, profileit
import cv2 as cv
import grequests
import numpy as np
import imageio
import datetime
import skimage.measure
import time

# @adapt_rgb(each_channel)
# def sobel_each(image):
#     return skimage.filters.sobel(image)

def sobel(r):
    image = read_image(r)
    ACCESS_LOG("Response shape: {}".format(image.shape))
    image = cv.Canny(image, 300, 200)
    # image = sobel_each(image)
    output = write_image(image, format="png")
    
    return output

def blur(r):
    image = read_image(r)
    image = cv.blur(image, (5,5))
    return write_image(image, format="png")

def gaussian_blur(r):
    image = read_image(r)
    image = cv.GaussianBlur(image, (5,5), 0)
    return write_image(image, format="png")

# @timeit
# @profileit
def get_range(x, y, tilematrix, resolution, layer, date1, date2):
    base_url = "http://onearth-tile-services/wmts/epsg4326/best/{layer}/default/{date}/{resolution}/{tilematrix}/{x}/{y}.png"
    dates = []

    d1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(date2, "%Y-%m-%d")

    delta = d2 - d1  # timedelta

    for i in range(delta.days + 1):
        dates.append((d1 + datetime.timedelta(days=i)).strftime('%Y-%m-%d'))

    urls = []
    for date in dates:
        url = base_url.format(layer=layer, date=date, resolution=resolution, tilematrix=tilematrix, x=x, y=y)
        urls.append(url)
        # ACCESS_LOG(url)

    s = time.time()
    rs = (grequests.get(u) for u in urls)
    responses = grequests.map(rs)
    e = time.time()

    ACCESS_LOG("Requests took: {}s".format(e - s))

    s = time.time()
    data = np.stack((imageio.imread(r.content) for r in responses))
    e = time.time()

    ACCESS_LOG("Stacking took {}s".format(e - s))

    return data

# @profileit
def correlation(x, y, tilematrix, layer1, layer2, date1, date2):
    s = time.time()
    image1 = get_range(x, y, tilematrix, "500m", layer1, date1, date2)
    image2 = get_range(x, y, tilematrix, "250m", layer2, date1, date2)
    e = time.time()

    ACCESS_LOG("Both requests took: {}s".format(e - s))
    ACCESS_LOG("image1 shape {}, image2 shape {}".format(image1.shape, image2.shape))

    n = 8
    increment = image1[0].shape[1] // n

    data1 = skimage.measure.block_reduce(image1, (1, n, n, 1), np.average)
    data2 = skimage.measure.block_reduce(image2, (1, n, n, 1), np.average)

    # data1 = np.zeros((n, n, image1[0].shape[-1], image1.shape[0]))
    # for i in range(n):
    #     for j in range(n):
    #         data1[i, j] = image1[:, increment * i : increment * (i + 1), increment * j : increment * (j + 1), 0:3].mean(axis=(1, 2)).T

    # data2 = np.zeros((n, n, image2[0].shape[-1], image2.shape[0]))
    # for i in range(n):
    #     for j in range(n):
    #         data2[i, j] = image2[:, increment * i : increment * (i + 1), increment * j : increment * (j + 1), 0:3].mean(axis=(1, 2)).T

    output = np.zeros((image1[0].shape[0], image1[0].shape[1], image1[0].shape[-1]))

    s = time.time()
    for i in range(n):
        for j in range(n):
            for k in range(output.shape[2]):
                output[increment * i : increment * (i + 1), increment * j : increment * (j + 1), k] = np.corrcoef(data1[i, j, k], data2[i, j, k])[1,0]

    e = time.time()
    ACCESS_LOG("output shape: {}. Correlation took {}s".format(output.shape, e - s))

    return write_image(output, format="jpeg")

def downsample(r, n):
    image = read_image(r)

    ACCESS_LOG("Response shape: {}".format(image.shape))

    if n == 0:
        return r.content

    increment = image.shape[0] // n
    for i in range(n):
        for j in range(n):
            image[increment * i : increment * (i + 1), increment * j : increment * (j + 1), 0:3] = image[increment * i : increment * (i + 1), increment * j : increment * (j + 1), 0:3].mean(axis=(0, 1))

    if image.shape[2] == 4:
        image[:,:,3] = 255

    output = write_image(image, format="png")
    
    return output
