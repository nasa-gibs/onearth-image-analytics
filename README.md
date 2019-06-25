# gibs-image-analytics

This is a Flask web-server integrated into the OnEarth Docker network for serving
on-demand analytics from GIBS imagery. This includes image filters, correlations,
time-series data, and more.

## Installation

Read the docker README for installation advice. The easiest way is to change the backend URL
to the public GIBS server at (https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/wmts.cgi). To run locally,

1. In onearth-tile-services, copy data to /onearth/layers/epsg4326/ and /onearth/idx/epsg4326/ using a Python script to unzip the files.

```ls */*/*.idx.tgz >> files.txt```

then

```python
import subprocess
import os

with open("files", "r") as f:
	layers = f.read().splitlines()

print("current directory is {}".format(os.getcwd()))

for file in data:
	try:
		command = "cd {} && tar -xvzf {}".format(os.getcwd(), file)
		print(command)
		cmd = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
		name = cmd.stdout.readlines()
		name = name[0].decode('utf-8').strip()
		os.rename(name, file.rstrip(".tgz"))
	except:
		print("file {} failed".format(file))
```


2. In onearth-tile-services, copy configs to /etc/onearth/config/layers/epsg4326/best/ and use sed script to update data_path.

```sed "s/data_file_uri: '\/{S3_URL}\/epsg4326/data_file_path: '\/onearth\/layers\/epsg4326/g" /etc/onearth/config/layers/epsg4326/best/MODIS_*.yaml```

3. Rerun the setup script for configuring the epsg4326 endpoint. Then restart the server, ideally also setting the debug flag to true in the startup script.
4. In time-services, modify the startup script to include the correct snapping range. Use the following script:

Script:

ls * > layers.txt

for open("layers.txt", "r") as f:
	layers = f.read().splitlines()

template = '/usr/bin/redis-cli -h $REDIS_HOST -n 0 DEL epsg4326:best:layer:{0}\n/usr/bin/redis-cli -h $REDIS_HOST -n 0 SET epsg4326:best:layer:{0}:default "2017-01-01"\n/usr/bin/redis-cli -h $REDIS_HOST -n 0 SADD epsg4326:best:layer:{0}:periods "2017-01-01/2017-01-14/P1D"'

for layer in layers:
	print(template.format(layer))	

Copy the output into the startup script near a bunch of similar commands.

5. Set debug flag to true and restart, rerunning the startup script.
6. In capabilities, copy all the config files to the right places and rerun the startup script. Same process as for tile-services.

The following aliases might be useful:

```bash
alias www='cd /var/www/html/wmts/epsg4326/best/'
alias config='cd /etc/onearth/config/layers/epsg4326/best/'
alias idx='cd /onearth/idx/epsg4326/'
alias data='cd /onearth/layers/epsg4326/'
alias aqua='cd MODIS_Aqua_Brightness_Temp_Band31_Day'
alias terra='cd MODIS_Terra_Brightness_Temp_Band31_Day'
```

Rerun the configuration script and restart everything.
