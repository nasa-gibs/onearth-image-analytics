# Mrfgen Overview

## Notes for GIBS:

My summary so far:
1. Existing GPU support for gdal_warp improves performance for certain methods like lanczos, but not for nearest neighbor, and not appreciably, compared to the cost of File IO.
2. From my experiments so far, the vast majority of time in mrfgen.py is spent in file IO. This can't be improved by GPUs. 
3. However, if the memory is never written to disk, and is generated when tiles are requested, this overhead wouldn't exist. However, it doesn't save you a ton of time compared to generating the full pyramids - we think about maybe 1/4 of the time. On the fly generation from granules would be possible, but complex. 
4. The SDAP also supports accelerated time generation from data.
5. Implemented a multiprocessing scheme which improves performance by 3-4 times. Not a huge performance hit so need to figure out why it's slower. 

## Commands:

time python mrfgen.py -c configs/MYR9LSRHLLDY.xml
python mrfgen.py -c configs/ASTGTM2.xml

<mrf_noaddo> - in conjunction with <mrf_nocopy> users mrf_insert to do overview generation
<mrf_nocopy> - does everything in place instead of generating intermediate files with gdal_translate
<extents> - bounding box extents (lower left hand to upper right hand in latitude longitude)
<outsize> - size of final concatenated highest resolution overview

-OF mem - saves in memory somehow.

## Commands:

gdaladdo -r nearest /home/jaaustin/workspace/mrfgen/output/ASTGTM2_20160623___mrfgen_20190610.123030.530876_9720.mrf 2 4 8 16 32 64 128 256 512 1024 2048 4096

time gdalwarp -overwrite -wo ENABLE_OPENCL=TRUE -wo USE_OPENCL=TRUE -t_srs EPSG:3395 -r cubic -wo SOURCE_EXTRA=1000 -co COMPRESS=LZW NE1_50M_SR_W_tenth.tif NE1_50M_SR_W_tenth_mercator.tif --debug on

## Profiling:

mrfgen.py on MYR9LSRHLLDY

Nocopy true, noaddo false:

('mrf_insert', 161.9718210697174)
('gdalinfo', 117.35396075248718)
('gdaladdo', 46.89048409461975)
('gdal_translate', 0.0683598518371582)

real	5m30.917s
user	4m32.937s
sys	1m5.520s

('mrf_insert', 127.4070086479187)
('gdalinfo', 117.81083106994629)
('gdaladdo', 48.53574800491333)
('gdal_translate', 0.12217187881469727)

real	4m57.326s
user	3m49.540s
sys	0m48.748s

Nocopy true, noaddo true:

('mrf_insert', 332.6463987827301)
('gdalinfo', 113.47998237609863)
('gdal_translate', 0.0670621395111084)

real	7m30.360s
user	6m32.493s
sys	1m5.196s

Nocopy false, noaddo false:

('gdalinfo', 0.02478194236755371)
('gdaladdo', 58.554717779159546)
('gdal_translate', 54.82726979255676)

real	1m55.467s
user	1m51.448s
sys	0m5.272s

On ASTGTM2 and 2 4 8 16 32 64 128 256 gdaladdo: 

Nocopy true, noaddo false:

('mrf_insert', 2.056647777557373)
('gdalinfo', 8.49530577659607)
('gdaladdo', 2307.1381599903107)
('gdal_translate', 0.03606700897216797)

real	38m38.258s
user	38m29.981s
sys	0m8.775s

Same dataset, noaddo true, no copy true (2 4 8 16 32 64) (AVG)

('mrf_insert', 2.2643539905548096)
('gdalinfo', 12.011308670043945)
('/home/jaaustin/workspace/mrfgen/RGBApng2Palpng', 2.491624593734741)
('gdal_translate', 21.798181772232056)

real	0m41.171s
user	0m36.721s
sys	0m5.770s

mrf_insert: 738.2699725627899
gdalinfo: 19.2770779132843
gdalwarp: 3.8397624492645264
gdalbuildvrt: 0.11429190635681152
gdal_translate: 0.04046797752380371

real	12m42.131s
user	12m35.336s
sys	0m7.766s

Noaddo false, no copy true 

('mrf_insert', 543.0374882221222)
('gdalinfo', 19.236191749572754)
('gdalwarp', 3.7628979682922363)
('gdaladdo', 153.40291690826416)
('gdal_translate', 0.05488014221191406)

real	12m0.088s
user	11m52.220s
sys	0m8.900s

('mrf_insert', 508.39308738708496)
('gdalinfo', 19.25920033454895)
('gdalwarp', 3.8109190464019775)
('gdaladdo', 161.02954292297363)
('gdal_translate', 0.041680097579956055)

real	11m33.142s
user	11m17.968s
sys	0m9.348s

Noaddo false, no copy false

('gdalinfo', 0.08228302001953125)
('gdaladdo', 170.29925990104675)
('gdal_translate', 1421.1083409786224)

real	26m31.840s
user	26m27.716s
sys	0m4.394s

Noaddo false, no copy false


GDAL Warp:

With GPU:

real	2m34.216s
user	0m50.850s
sys	1m11.227s

Without GPU:

real	0m5.650s
user	0m5.488s
sys	0m0.099s


ASTGTM2:

NO_ADDO FALSE, NO_COPY TRUE

Total:

('gdalinfo', 19.13670587539673)
('mrf_insert', 487.0341787338257)
('gdal_translate', 0.03146195411682129)
('gdaladdo', 158.8517849445343)
('gdalwarp', 3.606529951095581)
('gdalbuildvrt', 0.06231689453125)

Count:

('gdalinfo', 220)
('mrf_insert', 44)
('gdal_translate', 1)
('gdaladdo', 1)
('gdalwarp', 44)
('gdalbuildvrt', 1)

Average:

('gdalinfo', 0.08698502670634876)
('mrf_insert', 11.068958607586948)
('gdal_translate', 0.03146195411682129)
('gdaladdo', 158.8517849445343)
('gdalwarp', 0.08196658979762685)
('gdalbuildvrt', 0.06231689453125)

gdalwarp -of VRT -r near -overwrite -tr 0.000274658203125 -0.000274658203125 /home/jtrobert/workspace/data/src/ASTGTM2/ASTGTM2_N00E102_dem.tif /home/jaaustin/workspace/mrfgen/working_dir/ASTGTM2_N00E102_dem.tif.vrt

mrf_insert -r Avg /home/jaaustin/workspace/mrfgen/working_dir/ASTGTM2_N00E102_dem.tif.vrt /home/jaaustin/workspace/mrfgen/output/ASTGTM2/ASTGTM2_20160623___mrfgen_20190625.145902.263491_7701.mrf

NO_ADDO TRUE, NO_COPY TRUE

Total:

('mrf_insert', 683.9171943664551)
('gdalinfo', 19.33447027206421)
('gdalwarp', 3.72285795211792)
('gdalbuildvrt', 0.06099891662597656)
('gdal_translate', 0.04417920112609863)

Count:

('gdalinfo', 220)
('mrf_insert', 44)
('gdalwarp', 44)
('gdalbuildvrt', 1)
('gdal_translate', 1)

Average:

('mrf_insert', 15.543572599237615)
('gdalinfo', 0.08788395578211004)
('gdalwarp', 0.08461040800268)
('gdalbuildvrt', 0.06099891662597656)
('gdal_translate', 0.04417920112609863)

gdalwarp -of VRT -r near -overwrite -tr 0.000274658203125 -0.000274658203125 /home/jtrobert/workspace/data/src/ASTGTM2/ASTGTM2_N00E102_dem.tif /home/jaaustin/workspace/mrfgen/working_dir/ASTGTM2_N00E102_dem.tif.vrt

mrf_insert -r Avg /home/jaaustin/workspace/mrfgen/working_dir/ASTGTM2_N00E102_dem.tif.vrt /home/jaaustin/workspace/mrfgen/output/ASTGTM2/ASTGTM2_20160623___mrfgen_20190625.151711.730812_9353.mrf

Using MRFs instead of VRTs, with NO_ADDO TRUE, NO_COPY TRUE

('mrf_insert', 670.3613793849945)
('gdalinfo', 19.339109182357788)
('gdalwarp', 513.4317727088928)
('gdalbuildvrt', 0.07308411598205566)
('gdal_translate', 0.05503702163696289)

('mrf_insert', 44)
('gdalinfo', 220)
('gdalwarp', 44)
('gdalbuildvrt', 1)
('gdal_translate', 1)

('mrf_insert', 15.235485895113511)
('gdalinfo', 0.08790504173798995)
('gdalwarp', 11.668903925202109)
('gdalbuildvrt', 0.07308411598205566)
('gdal_translate', 0.05503702163696289)

ASTGTM2 (42 Tiles):

1 Core:

real	8m21.415s
user	8m16.020s
sys	0m6.215s

3 Cores:

real	3m2.931s
user	8m18.349s
sys	0m6.291s

5 Cores:

real	2m8.138s
user	8m32.749s
sys	0m23.535s

7 Cores:

real	2m29.913s
user	8m43.639s
sys	0m45.111s

9 Cores:

real	5m51.651s
user	9m12.984s
sys	3m56.556s

MYR9L:

1 Core:

real	4m51.990s
user	3m31.541s
sys	1m5.660s

2 Core:

real	2m9.122s
user	2m31.015s
sys	1m0.348s

3 Cores:

real	2m24.042s
user	2m32.353s
sys	1m16.709s

5 Cores:

real	3m28.133s
user	2m43.120s
sys	2m30.093s

Blue Marble PNG:

8 Cores:

real	16m58.108s
user	60m49.240s
sys	7m15.158s

## File size:

4.9G	MYR9LSRHLLDY with noaddo and no copy (2:30)
7.8G	MYR9LSRHLLDY with noaddo false and no copy (2:45)

More datasets:

1. https://ecocast.arc.nasa.gov/data/drop/6b6af8af6b0d87f39eb669a77d99cd07/delivery/geo/2000/ (giant)
