![Issues](https://img.shields.io/github/issues/punkerpunker/isochrone)
![Forks](https://img.shields.io/github/forks/punkerpunker/isochrone)
![Stats](https://img.shields.io/github/stars/punkerpunker/isochrone)
![License](https://img.shields.io/github/license/punkerpunker/isochrone)
![Contributors](https://img.shields.io/github/contributors/punkerpunker/isochrone)

# Isochrone
Isochrone API that provides a functionality of calculating isochrones (walking areas).

# Install:

1. Download **graph** for regions where you need to calculate isochrones. Download `.osm.pbf` files from http://download.geofabrik.de/. 
2. Put your `.osm.pbf`. files under `containers/app/osm/pbf` directory (currently there is `rutland-latest.osm.pbf` for illustration reasons, remove it if you don't need this area).
3. Run `docker-compose up --build` ([Hints](https://phoenixnap.com/kb/install-docker-compose-on-ubuntu-20-04) on how-to install `docker` and `docker-compose`)  

Then, you'll need to wait until **graph** is uploaded to DB. During upload, you might see messages like this `docker-compose logs app`:

```
[|                                   ] (1%) Total processed: 20000        Vertices inserted: 58672       Split ways inserted 53186
[*|                                  ] (3%) Total processed: 40000        Vertices inserted: 48981       Split ways inserted 46608
[**|                                 ] (5%) Total processed: 60000        Vertices inserted: 46003       Split ways inserted 43317
[***|                                ] (6%) Total processed: 80000        Vertices inserted: 33135       Split ways inserted 34595
[****|                               ] (8%) Total processed: 100000       Vertices inserted: 16320       Split ways inserted 18170
```

When API is ready you'll see message like this `docker-compose logs app`:
```
* Serving Flask app "app" (lazy loading)
* Environment: production
WARNING: This is a development server. Do not use it in a production deployment.
  Use a production WSGI server instead.
* Debug mode: off
* Running on http://0.0.0.0:1769/ (Press CTRL+C to quit)
```

# Usage:

In order to calculate isochrone you need to pass 3 query `parameters` to API:

1. `X` (float) - Longitude of a point for which you want to calculate walking area. 
2. `Y` (float) - Latitude of a point for which you want to calculate walking area. 
3. `sec` (integer) - Number of seconds (600 - 10 minute walking area, 300 - 5 minute walking area, etc.) 

## Example:
```python
import requests

url = 'http://localhost:1769/isochrone?'

params = {'X': -0.1946611966680779, 'Y': 51.46534965585685, 'sec': 300}
resp = requests.get(url, params=params)

print(resp.json())
```
```
POLYGON((-0.200436112629018 51.4667218592721,-0.200446733267529 51.4667235969986,-0.200460738988607 51.466725888585,-0.200490282193392 51.4667307223818, ...))
```

![alt text](https://github.com/punkerpunker/isochrone/blob/geofeat-to-isochrone-microservice/image.PNG)
