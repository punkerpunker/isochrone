# GeoFeat

GeoFeat - framework to work with isocrones and graphs. The most common usage - creating geodatamarts

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Requirements

Installation requires following packages:
```
PostgreSQL (>11)
PostGIS (>2.5)
PgRouting
```
Usage requires OSM Graph downloaded and stored in PostgreSQL

You can find tutorial in this repo named OSMGraph.md

### Installing

Installation could be as simple as:

```
pip3 install dist/geofeat-0.1.1.tar.gz
```

To verify installation try: 

```
import geofeat
```

## Authors

* **Gleb Vazhenin** - *Initial work* - [punker](https://github.com/punkerpunker/)

## License

This project doesn't have any license yet.


