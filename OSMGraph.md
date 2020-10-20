### Инструкция:

В связи с тем, что графы получаются довольно большие, приходится следовать такой долгой инструкции:

#### Подготовка .osm файла

Скачать данные в формате  .osm.pbf отсюда (http://download.geofabrik.de/)

Скачать полигон обрезки формата .poly откуда-нибудь или сделать самому как описано здесь (https://wambachers-osm.website/boundaries/)

С помощью утилиты osmosis вырезать из файла скачанного в п.1 территорию из п.2. Для этого в терминале необходимо сказать (я обрезаю Вологодскую область из файла СЗФО): 
```
osmosis --read-pbf file="/home/punker/data/osm/northwestern-fed-district-latest.osm.pbf" --bounding-polygon file="/home/punker/data/osm/RU-VOL.poly" --write-xml file="/home/punker/data/osm/RU-VOL.osm"
```
#### Загрузка .osm файла

Нужно в терминале сказать: 
```
osm2pgrouting --f /home/punker/data/osm/RU-VOL.osm --conf /home/punker/mlogic/core/gis/osm/mapconfig.xml --dbname db --prefix rt_ --username user --password password
```
(Файл mapconfig.xml лежит в репозитории тут и его лучше не менять)
