FROM ubuntu:20.04

RUN apt update && apt install -y python3 osm2pgrouting osmctools

COPY load.py .
COPY osm /osm