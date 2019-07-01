from flask import Flask, render_template, flash, redirect, session, url_for, request, g, Markup, jsonify
from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix

from methods import sobel, downsample, blur, gaussian_blur, correlation
from utils import ACCESS_LOG, ERROR_LOG, timeit, log_request, profileit, timeit
from timeseries import time_series 

import requests
import sys
import time
import os

app = Flask(__name__)
app.config['REVERSE_PROXY_PATH'] = '/analytics'
ReverseProxyPrefixFix(app)

def handle_varnish(request, response):
    if 'X-Varnish' in request.headers:
        response.headers['X-Varnish'] = request.headers['X-Varnish']

    if 'Age' in request.headers:
        response.headers['Age'] = request.headers['Age']

    return response

def make_request(url, headers=None):
    startr = time.time()

    # ACCESS_LOG(str(headers))
    response = requests.get(url, headers=headers)

    endr = time.time()

    ACCESS_LOG("--Subrequest start--")
    ACCESS_LOG("Request: " + url)
    ACCESS_LOG("Response Length: " + str(len(response.content)))
    ACCESS_LOG("Response Status Code: " + str(response.status_code))
    ACCESS_LOG("Headers:\n" + str(response.headers))
    ACCESS_LOG("Time for request: " + str(endr - startr))
    ACCESS_LOG("--Subrequest ended--")

    if response.status_code == 404 or response.status_code == 400 or len(response.content) == 0:
        return None, response.status_code, None
    
    return response, 200, response.headers

allowed_methods = {
    "downsample" : {
        "n" : int,
        "method" : downsample
    },

    "sobel" : {
        "method" : sobel
    },
    
    "blur" : {
        "method" : blur
    },

    "correlation" : {
        "layer1" : str,
        "layer2" : str,
        "date1" : str,
        "date2" : str,
        "method" : correlation 
    }
}

def parse_args(args):
    if args.get("method") in allowed_methods.keys():
        method = args.get("method")
        params = allowed_methods[method]

        try:
            arg_dict = { key : val(request.args.get(key)) for key, val in params.items() if key is not "method" }
            return params["method"], arg_dict
        except KeyError as e:
            ERROR_LOG("Invalid arguments for method {} in request: {}".format(method, str(e)))
            raise e
        except (TypeError, ValueError) as e:
            ERROR_LOG("Invalid types for method {} in request: {}".format(method, str(e)))
            raise e

    else:
        return None, {}

import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import numpy as np

@app.route("/getplot")
def getplot():
    # with open("data.json", "rb") as f:
    #     raw = f.read()

    # data = json.loads(raw)
    # metadata = data['meta'][0]
    # data = data['data'] 
    if not 'layer' in request.args:
        return render_template('404.html'), 404

    layer = request.args['layer']

    data, dates = time_series([layer], '1', '2017-01-01', '2017-01-14')

    # N = len(data)
    # x = [entry[0]['iso_time'].split("T")[0] for entry in data] # np.linspace(0, 1, N)
    # y = np.array([entry[0]['mean'] for entry in data])

    # name = metadata['short_name'].replace("_", " ")

    x = dates
    y = data[0,:,0] # mean
    name = layer

    layout = dict(title = 'Image Analytics for {}'.format(name),
              xaxis = dict(title = 'Date'),
              yaxis = dict(title = name),
              height=300,
              ) 

    # Create a trace
    trace = go.Scatter(
        x = x,
        y = y
    )

    data = [trace]
    fig = dict(data=data, layout=layout)

    html = Markup(plotly.offline.plot(fig, include_plotlyjs=False, output_type='div'))
    return html, {'Access-Control-Allow-Origin': '*'}

import json
@app.route("/timeSeriesSpark")
@log_request
def timeSeries():
    ACCESS_LOG(str(request.args))
    ACCESS_LOG(request.full_path)

    with open("data.json", "rb") as f:
        raw = f.read()

    data = json.loads(raw)

    # data['meta']['time']['iso_start']
    # data['meta']['time']['iso_stop']

    # for entry in data['data']:
    #     for key in entry[0].keys():
    #         if key in ['std', 'min', 'max', 'mean']:
    #             entry[0][key] = 5.0

    # ACCESS_LOG(str(data))

    # return jsonify(dict(data)), 200, {"Content-Type" : "application/json"}

    # url = "https://sealevel-nexus.jpl.nasa.gov" + request.full_path
    # ACCESS_LOG(url)
    # r = requests.get(url)

    # if r.status_code != 200:
    #     ACCESS_LOG("Request returned with status code {}".format(r.status_code))
    #     return render_template('404.html'), 404
    
    ACCESS_LOG("---REQUEST SUCCEEDED---")
    # ACCESS_LOG(str(r.json()))
    # ACCESS_LOG(str(r.headers))
    ACCESS_LOG("---REQUEST DONE---")

    # with open("out.json", "wb") as f:
    #     f.write(r.content)

    data['stats'] = {}
    data['meta'][0]['shortName'] = data['meta'][0]['short_name']

    return json.dumps(data, indent=4), 200, {'Content-Type' : 'application/json', 'Access-Control-Allow-Origin' : '*'}

@app.route("/generic/<int:tilematrix>/<int:x>/<int:y>")
@log_request
def generic(tilematrix, x, y):
    ACCESS_LOG(str(request.args))

    try:
        method, arg_dict = parse_args(request.args)    
    except Exception as e:
        error_dict = { "Error" : str(e), "Code" : 404, "Request" : request.path }
        return jsonify(error_dict), 404
    
    if method is None:
        error_dict = { "Error" : "Method not found", "Code" : 404, "Request" : request.path }
        return jsonify(error_dict), 404

    output = method(x, y, tilematrix, **arg_dict)

    # resp = handle_varnish(r, resp)
    return output, 200, {'Content-Type' : 'image/png'}


# @app.route("/wmts/<string:projection>/<string:kind>/<string:product>/default/<string:date>/<string:resolution>/<int:tilematrix>/<int:x>/<int:y>/<int:n>.<string:extension>")
@app.route("/wmts/<string:projection>/<string:kind>/<string:product>/default/<string:date>/<string:resolution>/<int:tilematrix>/<int:x>/<int:y>.<string:extension>")
@log_request
def single_tile(projection, kind, product, date, resolution, tilematrix, x, y, extension):
    url = "http://onearth-tile-services" + request.path

    ACCESS_LOG(f"URL: {url}")
    ACCESS_LOG(f"Projection {projection}, kind: {kind}, product: {product}, date: {date}, resolution: {resolution}")
    ACCESS_LOG(f"Args: {request.query_string}")

    r, status_code, headers = make_request(url, headers=request.headers)
    
    if status_code == 404:
        ACCESS_LOG("Status_code 404")
        return render_template('404.html'), 404, headers
    if status_code == 304:
        ACCESS_LOG("Status_code 304")
        return "", 304, headers
    
    try:
        method, arg_dict = parse_args(request.args)    
    except Exception as e:
        ACCESS_LOG("Error in arg parsing!")
        error_dict = { "Error" : str(e), "Code" : 404, "Request" : request.path }
        return jsonify(error_dict), 404

    if method is None:
        output = r.content
    else:
        output = method(r, **arg_dict)

    # resp = handle_varnish(r, resp)
    # ACCESS_LOG(str(headers))
    return output, status_code, dict(headers)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@log_request
def catch_all_debug(path):
    url = "http://onearth-tile-services/" + path

    r, status_code, headers = make_request(url)
    
    if status_code == 404 or r is None:
        return render_template('404.html'), 404

    return r.content, status_code, {'Content-Type' : 'image/png'}

@app.route('/')
@app.route('/index')
@log_request
def index():
    return render_template('index.html')

@app.route('/about')
@log_request
def about():
    return render_template('about.html')

@app.route('/test')
@log_request
def test():
    ACCESS_LOG("---Executing write test of log file---")
    ERROR_LOG("---Executing write test of log file---")

    return render_template('404.html'), 404
