# gibs-image-analytics

This is a Flask web-server integrated into the OnEarth Docker network for serving
on-demand analytics from GIBS imagery. This includes image filters, correlations,
time-series data, and more. 

## Installation

Read the docker README for installation advice. The easiest way is to change the backend URL
to the public GIBS server at (https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi). Simply edit the
backend in `wmts/index.js` to the above endpoint, and change links in the `app/main.py` and `app/tileseries.py` utilities.

To run locally, you have to run the entire OnEarth Docker network and load data local into the various services. After acquiring
some MRF data and configuration XML files for OnEarth, you need to format everything to work locally. The instructions in `setup.md`
give a pretty good overview of what's necessary, but there's a painful trial and error process involved too. 

## Overview

### frontend

This directory hosts a frontend OpenLayers website which allows you to make requests to the WMTS tile service and analytic service
hosted in `app`. This can be setup with `npm install` and `npm start`. Basically just follow the basic OpenLayers installation.

### app

This directory contains a WMTS tile service capable of transforming data with a variety of filters and performing on-demand analytics
on raw image data, including time-series analysis. `timeseries.py` is the body of the code for doing on-demand analysis.

### docker

This contains the Dockerfile and setup scripts for this application, called `onearth-analytics`, which hooks into an existing Docker
network (oe2) run by the OnEarth service.

### docs

This contains documentation for this code, OnEarth in general, and the MRF file format. It also contains benchmarks for MRF generation
improvements and the VarnishCache implementation, which could be a good reverse cache for OnEarth/GIBS.