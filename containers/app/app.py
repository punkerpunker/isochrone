import os
import subprocess
import connexion
import sqlalchemy
from shapely.geometry import Polygon
from shapely import wkt


DB_PASSWORD = os.environ['POSTGRES_PASSWORD']
RAW_DIR = '/osm/pbf'
CONVERTED_DIR = '/osm/pbf/converted'
MAPCONFIG_PATH = '/osm/mapconfig.xml'
engine = sqlalchemy.create_engine(f'postgresql+psycopg2://postgres:{DB_PASSWORD}@pgrouting/postgres')


class Loader:
    @staticmethod
    def create_dirs(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def convert(raw_directory, converted_directory):
        for file in os.listdir(raw_directory):
            if file.endswith(".osm.pbf"):
                path = os.path.join(raw_directory, file)
                osm_name = file.rstrip('.pbf')
                new_path = os.path.join(converted_directory, osm_name)
                subprocess.check_call([f'osmconvert {path} --drop-author --drop-version --out-osm -o={new_path}'], shell=True)

    @staticmethod
    def load(converted_directory, mapconfig_path, password):
        for file in os.listdir(converted_directory):
            path = os.path.join(converted_directory, file)
            subprocess.check_call([f'osm2pgrouting --host pgrouting --f {path} --conf {mapconfig_path} --dbname postgres '
                                   f'--username postgres --password {password}'], shell=True)


def isochrone(X, Y, sec):
    query = "select ST_AsText(catchment_area(%s, %s, %s)) as polygon" % (X, Y, sec)

    with engine.connect() as connection:
        result = connection.execute(query)
        for row in result:
            return row['polygon']


if __name__ == "__main__":
    Loader.create_dirs(CONVERTED_DIR)
    Loader.convert(RAW_DIR, CONVERTED_DIR)
    Loader.load(CONVERTED_DIR, MAPCONFIG_PATH, DB_PASSWORD)

    app = connexion.App(__name__, specification_dir='./')
    app.add_api('swagger.yaml')
    app.run(port=1769)

