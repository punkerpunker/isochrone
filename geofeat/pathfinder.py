import getpass
import numpy as np
import pandas as pd
from functools import partial
from mlbase.db.engine import MLData
from shapely.geometry import Polygon
from shapely import wkt
from multiprocessing import Pool


def get_closest_cost(long, lat, points_query, db):
    query = "select find_cost_to_closest(%s, %s, '%s')" % (long, lat, points_query)
    try:
        db.cur.execute(query)
        return db.cur.fetchone()[0]
    except Exception as e:
        print(e)
        print(query)


def multi_closest_cost(df, long_column, lat_column, points_query, password=None, n_cores=16):
    if not password:
        password = getpass.getpass(prompt='Password for user: %s' % getpass.getuser())
    split_df = np.array_split(df, n_cores)
    pool = Pool(n_cores)
    data = pd.concat(pool.map(partial(apply_parallel,
                                      long_column=long_column, lat_column=lat_column,
                                      points_query=points_query, password=password), split_df))
    pool.close()
    pool.join()
    return data


def apply_parallel(df, long_column, lat_column, points_query, password):
    db = MLData(password=password)
    for index, row in df.iterrows():
        df.at[index, 'cost_to_closest'] = int(get_closest_cost(row[long_column], row[lat_column], points_query, db))
        db.commit()
    db.close()
    return df
