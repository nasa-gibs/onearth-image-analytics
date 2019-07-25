import requests
import numpy as np
import matplotlib.pyplot as plt

def get_data(bbox=(-20, -20, 10, 10), date="2014-01-01"):
    url = "https://oceanworks.jpl.nasa.gov/datainbounds?ds={layer}&startTime={time}T00:00:00Z&endTime={time}T00:00:00Z&b={bbox}"

    xwidth = bbox[2] - bbox[0]
    ywidth = bbox[3] - bbox[1]

    temp_url = url.format(layer="AVHRR_OI_L4_GHRSST_NCEI", time=date, bbox=",".join((str(e) for e in bbox)))
    print(temp_url)

    r = requests.get(temp_url)
    r.raise_for_status()

    json = r.json()
    data = [(entry['latitude'], entry['longitude'], entry['data'][0]['variable']) for entry in json['data']]
    data = np.stack(list(zip(*data)), axis=1)

    xvals = np.round((data[:,0] - data[:,0].min()) / 0.25).astype(np.int64)
    yvals = np.round((data[:,1] - data[:,1].min()) / 0.25).astype(np.int64)
    values = data[:,2]

    tile = np.zeros((xwidth * 4, ywidth * 4))

    tile[xvals, yvals] = values

    return tile