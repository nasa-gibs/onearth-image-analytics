import imageio
import numpy as np
from functools import wraps
import time
from flask import request
import cProfile, pstats, io
from pstats import SortKey

def ACCESS_LOG(message):
    with open("/app/access.txt", "a+") as log: # note logging is expensive
        log.write(message + "\n")

def ERROR_LOG(message):
    with open("/app/error.txt", "a+") as log:
        log.write(message + "\n")

def read_image(r):
    if not 'Content-Type' in r.headers:
        return None

    if r.headers['Content-Type'] == 'image/png':
        return imageio.imread(r.content, format="png")
    elif r.headers['Content-Type'] == 'image/jpeg':
        return imageio.imread(r.content, format="jpeg")
    else:
        return None

def write_image(array, format = "png"):
    return imageio.imwrite(imageio.RETURN_BYTES, np.asarray(array), format=format) # asarray needed for transparency

def log_request(func):
    @wraps(func)
    def function(*args, **kwargs):
        start = time.time()
        ACCESS_LOG("---Received request---")
        ACCESS_LOG("Request URL: {}, domain: {}, endpoint: {}".format(request.path, request.url_root, func.__name__))
        value = func(*args, **kwargs)
        end = time.time()
        ACCESS_LOG("---Request ended (Total time: {})---".format(end - start))
        return value

    return function

def timeit(func):
    @wraps(func)
    def function(*args, **kwargs):
        start = time.time()
        ACCESS_LOG("---Called function {}---".format(func.__name__))
        value = func(*args, **kwargs)
        end = time.time()
        ACCESS_LOG("---Call to function {} ended (Total time: {})---".format(func.__name__, end - start))
        return value

    return function

def profileit(func):
    @wraps(func)
    def function(*args, **kwargs):
        ACCESS_LOG("---Called function {}---".format(func.__name__))
        pr = cProfile.Profile()
        pr.enable()
        value = func(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        ACCESS_LOG(s.getvalue())
        ACCESS_LOG("---Call to function {} ended---".format(func.__name__))
        return value

    return function