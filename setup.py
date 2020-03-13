from setuptools import setup, find_packages

setup(
    name='geofeat',
    packages=find_packages(),
    description='GeoFeatures enterprise edition',
    version='0.1.1',
    url='https://bitbucket.org/marketinglogic/gfeat/src/master/',
    author='punker',
    author_email='gvazhenin@marketing-logic.ru',
    install_requires=['geopandas','geopy','shapely','mlbase'],
    )
