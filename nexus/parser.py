import requests
import numpy as np
import matplotlib.pyplot as plt

url = "https://oceanworks.jpl.nasa.gov/datainbounds?ds={layer}&startTime={time}T00:00:00Z&endTime={time}T00:00:00Z&b={bbox}"

bbox = [-20, -20, 10, 10]
temp_url = url.format(layer="AVHRR_OI_L4_GHRSST_NCEI", time="2014-01-01", bbox=",".join((str(e) for e in bbox)))
print(temp_url)

r = requests.get(temp_url)
r.raise_for_status()

json = r.json()
shape = tuple(json['meta']['data']
)
data = np.zeros(shape)

with np.nditer(data, op_flags=['readwrite']) as it:
    for i, x in enumerate(it):
        x[...] = json['data'][i]['data'][0]['variable']

plt.imshow(data.squeeze())
plt.show()