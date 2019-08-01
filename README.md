# gibs-image-analytics

This is a Flask web-server integrated into the OnEarth Docker network for serving
on-demand analytics from GIBS imagery. This includes image filters, correlations,
time-series data, and more. 

## Installation

Read the docker README for installation advice. The application can be run as a Docker container by simply running `./run.sh`,
but it is set up to accept requests passed through the OnEarth frontend. To run fully, the simplest system is:

1. Clone the OnEarth repository from https://github.com/nasa-gibs/onearth
2. Launch the various docker contains with the start script.
3. Connect to the `onearth-demo` container and edit the `/etc/httpd/conf.d/oe2_demo.conf` by adding the lines

```
ProxyPass /analytics http://onearth-analytics
ProxyPassReverse /analytics http://onearth-analytics
```

4. Launch the `onearth-analytics` container with `./run.sh`. 
5. Launch the frontend from the `frontend` directory with `frontend/run.sh`. 

This will work properly, but it will be slow, because it has to pull all of the data remotely from the OnEarth servers, instead of 
over a local network as part of OnEarth. This also works with OnEarth running locally, and instructions for configuring
that can be found in the `docs` folder. With that running, just change the directories in `app/main.py` and `frontend/index.js`
to point to the localhost address of OnEarth.

## Overview

### frontend

This directory hosts a frontend OpenLayers website which allows you to make requests to the WMTS tile service and analytic service
hosted in `app`. This can be setup with `npm install` and `npm start`. Basically just follow the basic OpenLayers installation.

### app

This directory contains a WMTS tile service capable of transforming data with a variety of filters and performing on-demand analytics
on raw image data, including time-series analysis. `timeseries.py` is the body of the code for doing on-demand analysis.
This is not the best code in the world. I was experimenting with async coding in Python, and the quality and speed of the
code didn't benefit. This could be vastly improved with a single asynchronous system for making tile requests. The Colormap
parsing utility also fails from some colormaps in different formats, so this could be made more robust to work for all products.

### docker

This contains the Dockerfile and setup scripts for this application, called `onearth-analytics`, which hooks into an existing Docker
network (oe2) run by the OnEarth service.

### docs

This contains documentation for this code, OnEarth in general, and the MRF file format. It also contains benchmarks for MRF generation
improvements and the VarnishCache implementation, which could be a good reverse cache for OnEarth/GIBS.
