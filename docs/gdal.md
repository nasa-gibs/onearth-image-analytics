# GDAL

GDAL is a software library designed to manipulate geo-tagged images - it performs reprojection and rescaling, image pyramid generation, and more.

## GDAL 3.0

GDAL 3.0 does not quite work with mrfgen.py in its current state. The following is a set of setup instructions for building GDAL 3.0 from scratch, although some kind of resolution issue prevents it from being compatible. In particular, GDAL Warp in GDAL 3.0 leads to negative values in the DstRect XML tags in .MRF and .VRT files.

First build PROJ from the source, in the `projbuild` directory. Then:

```bash
export PATH=/home/jaaustin/projbuild/bin:/home/jaaustin/gdalbuild/bin:$PATH
export PROJ_LIB=/home/jaaustin/projbuild/share/proj/:$PROJ_LIB
export PATH=/usr/local/cuda-9.0/bin/:$PATH
./configure --prefix=/home/jaaustin/gdalbuild --with-opencl=yes --with-opencl-include=/usr/local/cuda-9.0/include --with-opencl-lib=/usr/local/cuda-9.0/lib64 --with-proj=/home/jaaustin/projbuild
```

where INSTALL_DIR is the install directory (prefix) of proj/gdal. The relevant environment variables are listed here: `https://proj.org/usage/environmentvars.html?highlight=environment`.

To monitor GPU usage, you can use nvidia-smi. To set persistent mode (useful for cluster), try: `nvidia-smi -pm 1`.

To run mrfgen: `python mrfgen.py -c configuration_file.xml`

To profile Python commands, run:

`python -m cProfile %1 | sort -k2 -n`

To view tiles from a given mrf file, run:

`for i in {1..100}; do echo $i; python read_mrf.py --input /home/jaaustin/workspace/mrfgen/output/MYR9LSRHLLDY/MYR9LSRHLLDY2016363_.mrf --output ~/workspace/example/test$i.png --tile $i; done`

GDAL Warp:

`time gdalwarp -overwrite -wo ENABLE_OPENCL=TRUE -wo USE_OPENCL=TRUE -t_srs EPSG:3395 -r cubic -wo SOURCE_EXTRA=1000 -co COMPRESS=LZW NE1_50M_SR_W_tenth.tif NE1_50M_SR_W_tenth_mercator.tif --debug on`

The --debug on will display GPU debugging information. Existing GPU support only supports downsampling methods besides nearest neighbor and averge. -overwrite for gdalwarp to overwrite destination. SAMPLE_GRID=YES for polar projections.

## mrf_insert

Internally, calls GDALOpen, then calls RasterIO in a pretty big loop, also ClippedRasterIO. Calls PatchOverview in the mrf_overview file to do downsampling.
