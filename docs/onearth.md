# General OnEarth Overview

OnEarth is a high-performance web tile service which supports the WMTS, WMS, and TWMS standards. The GIBS web-service (found at gibs.earthdata.nasa.gov) is an OnEarth server hosting a large portion of NASA's earth satellite imagery. A sample request for OnEarth looks like

`https://gibs-b.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi?TIME=2019-06-12T00:00:00Z&layer=MODIS_Terra_CorrectedReflectance_TrueColor&style=default&tilematrixset=250m&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fjpeg&TileMatrix=1&TileCol=1&TileRow=0`

in the KVP API, or 

`https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2019-06-12/250m/1/0/1.jpeg`

in the REST API. Each request specifies the name of the desired tile (MODIS_Terra_CorrectedReflectance_TrueColor), the style (usual default), the projection (EPSG4326 in this case), the date (2019-06-12), the tilematrixset or resolution of the product (250m in this case, usually between 250m and 2km), the tilematrix or zoom level (1 in this case), and the tile row and column (col: 0, row: 1 in this case. This API is defined in the GetCapabilities XML document which is returned by a standard query to the server (`https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi?SERVICE=WMTS&request=GetCapabilities` in the case of GIBS). This document defines all available layers and their supported tilematrixsets and styles. The GetCapabilities document for GIBS also defines the colormaps used for image generation as well. A list of products for GIBS as of 7/2/2019 can be found in this repository.

# OnEarth Structure

The OnEarth repository, as of 2.0.0, is split into a number of Docker containers, each of which runs a separate microservice. These include: onearth-tile-services, onearth-capabilities, onearth-time-service, onearth-demo, onearth-wms, and onearth-reproject. They are connected by a Docker network called oe2, and pass messages over HTTP.

Generally, Apache related configuration is found at `/etc/httpd` while limited static content is found at `/var/www`. Configuration files are found at `/etc/onearth` (layer YAML files). Data is found at `/onearth`. The startup scripts for each container, including important configuration information, is found in `/home/oe2/onearth/docker/[container name]`. 

## onearth-tile-services

Most imagery served by OnEarth is in an MRF or "Meta Raster File" format. These are large files which contain image pyramids for a given daily satellite reading. This is the container that actually reads these MRF files and sends them out as HTTP requests to the requesting user. By default, as GIBS transitions to the cloud, this pulls data from S3 buckets instead of lock files, but the logic remains the same. To set this up for local development, follow the Local Development guide in this repository. Configuration files are located at `/etc/onearth/config`, and the tiles themselves are located at `/onearth/layers` while the MRF idx files are located at `/onearth/idx`.

## onearth-time-services

This container provides a time-snapping service which converts requests for a specific date into the cannonical request for, say, weekly products. If a tile is requested on a date covered by the weekly period for the product, it snaps the date to the right weekly date and then return that to the requesting use. This using a REDIS database to hold most of the date data. This is configured automatically for products in S3, but it can be manually configured in the startup script, with calls of the form:

```bash
/usr/bin/redis-cli -h $REDIS_HOST -n 0 DEL epsg4326:best:layer:MODIS_Aqua_Aerosol
/usr/bin/redis-cli -h $REDIS_HOST -n 0 SET epsg4326:best:layer:MODIS_Aqua_Aerosol:default "2017-01-01"
/usr/bin/redis-cli -h $REDIS_HOST -n 0 SADD epsg4326:best:layer:MODIS_Aqua_Aerosol:periods "2017-01-01/2017-01-14/P1D"
```

which defines an EPSG4326 layer for the "best" endpoint and the MODIS_Aqua_Aerosol layer for a January 1st 2017 start date, covering the 1/1-1/14 period in daily increments. 

## onearth-capabilities

This is the repository which generates the GetCapabilities document. Specifically, this calls a lua script

`lua /home/oe2/onearth/src/modules/gc_service/make_gc_endpoint.lua /etc/onearth/config/endpoint/epsg4326_best.yaml`

(for example) which sets up an endpoint from a .yaml configuration file. All of the configuration files reside at /etc/onearth/config, including yaml configurations for the individual products and for the endpoints. While covered in more detail in the local development guide, to make local products, you need to add their YAML files to `/etc/onearth/config/layers/epsg4326/best`, for example, and modify those yaml files to set `data_file_path` to a local path instead of a remote uri.

## onearth-reproject and onearth-wms

Onearth-WMS is a container which supports WMS requests, an alternative API for tile requests. Instead of requesting tiles, you request geographic boundaries and a resolution, and the image is rescaled. Onearth-reproject performs reprojection for projections besides EPSG4326, if requested.

# MRF Generation

The MRF generation process takes a raw image or a set of image tiles or granules and creates a large MRF file with the image split into small tiles and rescaled to a variety of resolutions for use in an image pyramid. The progress largely uses the mrfgen.py script which itself uses GDAL. 