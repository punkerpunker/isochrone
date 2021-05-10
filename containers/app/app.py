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
    def create_directory(path_to_directory: str):
        if not os.path.exists(path_to_directory):
            os.makedirs(path_to_directory)

    @staticmethod
    def convert_pbf_to_osm(pbf_file_directory: str, osm_file_directory: str):
        for file in os.listdir(pbf_file_directory):
            if file.endswith(".osm.pbf"):
                path = os.path.join(pbf_file_directory, file)
                osm_name = file.rstrip('.pbf')
                new_path = os.path.join(osm_file_directory, osm_name)
                subprocess.check_call([f'osmconvert {path} --drop-author --drop-version --out-osm -o={new_path}'], shell=True)

    @staticmethod
    def load_osm_files_to_db(osm_file_directory: str, mapconfig_path: str, password: str):
        for file in os.listdir(osm_file_directory):
            path = os.path.join(osm_file_directory, file)
            subprocess.check_call([f'osm2pgrouting --host pgrouting --f {path} --conf {mapconfig_path} --dbname postgres '
                                   f'--username postgres --password {password}'], shell=True)


def isochrone(X, Y, sec):
    query = "select ST_AsText(catchment_area(%s, %s, %s)) as polygon" % (X, Y, sec)

    with engine.connect() as connection:
        result = connection.execute(query)
        for row in result:
            return row['polygon']


if __name__ == "__main__":
    Loader.create_directory(OSM_DIR)
    Loader.convert_pbf_to_osm(PBF_DIR, OSM_DIR)
    Loader.load_osm_files_to_db(OSM_DIR, MAPCONFIG_PATH, DB_PASSWORD)

    app = connexion.App(__name__, specification_dir='./')
    app.add_api('swagger.yaml')
    app.run(port=1769)
