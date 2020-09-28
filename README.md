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

You can find tutorial in this repo named OSMGraph.md (https://github.com/punkerpunker/geofeat/blob/master/OSMGraph.md)

### Installing

Installation could be as simple as:

```
python3 setup.py install

psql -d your_db_with_postgis -f sql/catchment_area.sql
psql -d your_db_with_postgis -f sql/find_path_to_closest.sql
psql -d your_db_with_postgis -f sql/find_cost_to_closest.sql

```

To verify installation try: 

```
import geofeat
```

### Isocrone calculation example
```sql
Select catchment_area(37.46, 55.67, 300, 'car')
```
![alt text](https://github.com/punkerpunker/geofeat/blob/master/image.png "Isocrone example")


### Usage example

```python
from geofeat import GeoFeatures

city_id = 1 # (Ekat)

df = pd.read_sql(' select gc_lat, gc_lng from points ', db.engine)

gdf = GeoFeatures(db, df, 'gc_lng', 'gc_lat']
yandex_categories = ['Ломбард', 'Рынок', 
                      'Салон оптики', 'Оценочная компания', 
                      'Жилье посуточно']

for zone in ['ped', 'car']:
    for sec in [300, 600, 1200]:
        print(sec)
        gdf.aggregate_in_isochrone('select longitude, latitude from stops where longitude is not null', sec=sec, mode=zone, column_name='stops_'+str(zone)+'_'+str(sec))
        gdf.aggregate_in_isochrone('select lng, lat, flat_count from flats where lat is not null', sec=sec, mode=zone, column_name='flats_'+str(zone)+'_'+str(sec))
        for category in ['Лотереи']:
            print(category)
            gdf.aggregate_in_isochrone('select gc_lng, gc_lat from organizations where name = \'%s\' and gc_lat is not null' % category, sec=sec, mode=zone, column_name=category + '_' + str(zone) + '_' + str(sec))

for category in yandex_categories:
    print(category)
    gdf.distance_to_closest('select gc_lng, gc_lat from organizations where name = \'%s\' and gc_lat is not null' % category, column_name='"closest_'+category+'"', limit_meters=100000)
```

## Authors

* **Gleb Vazhenin** - *Initial work* - [punker](https://github.com/punkerpunker/)

## License

This project doesn't have any license yet.
