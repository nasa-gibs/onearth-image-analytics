import asyncio
from aiohttp import ClientSession
import time
from owslib.wmts import WebMapTileService

# capabilities_url = "http://localhost/wmts/epsg4326/best/1.0.0/WMTSCapabilities.xml"
# wmts = WebMapTileService(capabilities_url)

async def fetch(url, session):
    async with session.get(url) as response:
        return await response.read()

async def make_requests(n):
    urls = ["http://localhost/wmts/epsg4326/best/MODIS_Aqua_Brightness_Temp_Band31_Day/default/2017-01-01/1km/0/0/0.jpeg"] * n
    tasks = []

    start = time.time()

    async with ClientSession() as session:
        for url in urls:
            tasks.append(asyncio.ensure_future(fetch(url, session)))

        responses = await asyncio.gather(*tasks)

    end = time.time()
    print("{} HTTP REQUESTS: {}s".format(n, end - start))

    return responses

# rs = [make_requests()]

s = time.time()
loop = asyncio.get_event_loop()
future = asyncio.ensure_future(make_requests(100))
loop.run_until_complete(future)

e = time.time()

print("Total time {}: ".format(e - s))