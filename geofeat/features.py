import pandas as pd
import geopandas as gpd
from math import isnan
from geopy.distance import geodesic
from geofeat.catchment_area import multi_catchment_area, get_catchment_area
from geofeat.pathfinder import multi_closest_cost


class GeoFeatures(object):
    """GeoFeatures is the mapper for many geographical functions.

    The explanations and documentation can be founded in Confluence
    """
    def __init__(self, db, df, long_column, lat_column, id_column='sys_ind'):
        """
        Note:
            Cache is the system parameter and it shouldn't be used by users.

        Args:
            db (core.database.db.DB): Database connector
            df (pd.DataFrame): DataFrame with points to analyze
            long_column (str): Column name with longitude from df
            lat_column (str): Column name with latitude from df

        Attributes:
            db (core.database.db.DB): Database connector
            df (pd.DataFrame): DataFrame with points to analyze
            long_column (str): Column name with longitude from df
            lat_column (str): Column name with latitude from df
        """
        self.lat_column = lat_column
        self.long_column = long_column
        self.db = db
        self.id_column = id_column
        self.df = self.increment(df)
        # - Cache variables
        self.cache = (0, '')

    def increment(self, df):
        return df.reset_index().rename(columns={'index': self.id_column})

    def __repr__(self):
        return str(self.df)

    def to_frame(self):
        return self.df

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, df):
        if self.lat_column not in df.columns:
            raise KeyError(self.lat_column)
        if self.long_column not in df.columns:
            raise KeyError(self.long_column)
        self._df = df

    def get_points(self, points_query):
        df = pd.read_sql(points_query, self.db.engine)
        if len(df.columns) == 3:
            df.rename(columns={df.columns[2]: 'weight'}, inplace=True)
        else:
            df['weight'] = 1
        df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.iloc[:, 0], df.iloc[:, 1]))
        df.crs = {'init': 'epsg:4326'}
        return df

    def distance_to_closest(self, point_query, column_name='distance', limit_meters=10000):
        self._put_target()
        self._put_points(point_query)
        query = " SELECT targets.%s, targets.%s, targets.%s, poi.dist::integer as %s " \
                " FROM temporary.distance_to_closest___target as targets " \
                " JOIN LATERAL " \
                "   (SELECT points.*, " \
                "           ST_Distance(points.geom, targets.geom) as dist " \
                "   FROM temporary.distance_to_closest___points as points " \
                "   WHERE ST_DWithin(points.geom, targets.geom, %s) " \
                "ORDER BY points.geom <-> targets.geom LIMIT 1) " \
                "AS poi on true;" % (self.id_column, self.long_column, self.lat_column, column_name, limit_meters)
        
        distances = pd.read_sql(query, self.db.engine)
        distances.drop_duplicates([self.long_column, self.lat_column], inplace=True)
        if column_name in self.df:
            self.df.drop(column_name, axis=1, inplace=True)
        self.df = self.df.merge(distances[[self.id_column, column_name]], on=self.id_column, how='left')

    def _put_points(self, point_query):
        points_df = pd.read_sql(point_query, self.db.engine)
        long_lat = points_df.columns[:2]
        points_df.rename(columns={long_lat[0]: 'long', long_lat[1]: 'lat'}, inplace=True)
        points_df.to_sql('distance_to_closest___points', self.db.engine, index=False,
                         if_exists='replace', schema='temporary')
        self.db.cur.execute('alter table temporary.distance_to_closest___points '
                            'add column geom geography')
        self.db.cur.execute('update temporary.distance_to_closest___points '
                            'set geom = ST_MakePoint(long::float, lat::float)::geography')
        self.db.cur.execute('create index distance_to_closest___points_gist_idx '
                            'on temporary.distance_to_closest___points using gist(geom)')
        self.db.commit()

    def _put_target(self):
        self.df[[self.id_column, self.long_column, self.lat_column]].to_sql('distance_to_closest___target', self.db.engine,
                                                            index=False, if_exists='replace', schema='temporary')
        self.db.cur.execute('alter table temporary.distance_to_closest___target '
                            'add column geom geography')
        self.db.cur.execute('update temporary.distance_to_closest___target '
                            'set geom = ST_MakePoint(%s::float, %s::float)::geography' % (self.long_column, self.lat_column))
        self.db.cur.execute('create index distance_to_closest___target_gist_idx '
                            'on temporary.distance_to_closest___target using gist(geom)')
        self.db.commit()

    def distance_to_closest_graph(self, points_query, column_name='distance'):
        """Finds cost in meters for given points to given points

        Function uses core.gis.multi_closest_cost function which in turn uses catchment_area
        PostgreSQL 11.3 function written using PostGIS and PgRouting libraries.

        Args:
            points_query (str): SQL-query that selects two (lng, lat) column
            column_name (str): Column name in which number of objects is going to be returned
        Returns:
            self
        """

        # - Ниже какой то жуткий костыль (5 строк), нужно будет решать потом
        points_df = pd.read_sql(points_query, self.db.engine)
        lat_column = points_df.columns[1]
        long_column = points_df.columns[0]
        points_df.to_sql('points_temp', self.db.engine, if_exists='replace', index=False)
        points_query = 'select %s, %s from points_temp' % (long_column, lat_column)

        self.df = multi_closest_cost(self.df,
                                     long_column=self.long_column, lat_column=self.lat_column,
                                     points_query=points_query,
                                     password=self.db.password)
        self.df.rename(columns={'cost_to_closest': column_name}, inplace=True)

    def recalc_catchment_area_nulls(self, sec, type):
        for index, row in self.df[self.df['catchment_area'].isnull()].iterrows():
            self.df.at[index, 'catchment_area'] = get_catchment_area(row[self.long_column], row[self.lat_column],
                                                                     sec, type, self.db)

    def shrink_catchment_area_nulls(self):
        self.df = self.df[~self.df['catchment_area'].isnull()]

    def aggregate_in_isochrone(self, points_query, sec=600, mode='ped', column_name='count', shrink_bad=False):
        """Aggregate objects in transport or pedestrian accessibility zone around points

        Function uses core.gis.multi_catchment_area function which in turn uses catchment_area
        PostgreSQL 11.3 function written using PostGIS and PgRouting libraries.

        Args:
            points_query (str): SQL-query that selects two (lng, lat) or three (lng, lat, weight) column
            sec (int): Number of seconds of transport accessibility
            mode (str): Transport: 'car' or Pedestrian 'ped' mode of accessibility
            column_name (str): Column name in which number of objects is going to be returned
            shrink_bad: If true - removes rows with bad catchment_area
        Returns:
            self
        """
        points_df = self.get_points(points_query)
        if self.cache[0] == sec and self.cache[1] == mode:
            pass
        else:
            self.df = multi_catchment_area(self.df,
                                           long_column=self.long_column, lat_column=self.lat_column,
                                           sec=sec, type=mode,
                                           password=self.db.password)
            self.cache = (sec, mode)
            # Периодически, почему-то возникают NULL'ы в catchment_area. Эта функция их обрабатывает
            self.recalc_catchment_area_nulls(sec, mode)
            if shrink_bad:
                # Если и так не вышло, то убираем эту строку
                self.shrink_catchment_area_nulls()
        self.df = gpd.GeoDataFrame(self.df, geometry='catchment_area')
        self.df.crs = {'init': 'epsg:4326'}
        joined = gpd.sjoin(points_df, self.df, op='intersects', how='left')
        count = joined[~joined['index_right'].isnull()].groupby(['index_right'])['weight'].sum()
        count.index = count.index.astype(int)
        self.df = self.df.merge(count, left_index=True, right_index=True, how='left')
        self.df[column_name] = self.df['weight'].fillna(0).astype(int)
        self.df.drop('weight', axis=1, inplace=True)
