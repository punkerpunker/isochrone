FROM ubuntu:20.04

RUN apt update && apt install -y python3 osm2pgrouting osmctools python3-pip

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

COPY load.py .
COPY osm /osm