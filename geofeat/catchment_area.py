import getpass
import numpy as np
import pandas as pd
from functools import partial
from mlbase.db.engine import DB
from shapely.geometry import Polygon
from shapely import wkt
from multiprocessing import Pool


def get_catchment_area(long, lat, sec, type, db):
    query = "select ST_AsText(catchment_area(%s, %s, %s, '%s'))" % (long, lat, sec, type)
    try:
        db.cur.execute(query)
        return Polygon(wkt.loads(db.cur.fetchone()[0]))
    except Exception as e:
        print(e)
        print(query)


def multi_catchment_area(df, long_column, lat_column, sec, type, password=None, n_cores=15):
    df.reset_index(drop=True, inplace=True)
    if not password:
        password = getpass.getpass(prompt='Password for user: %s' % getpass.getuser())
    split_df = np.array_split(df, n_cores)
    pool = Pool(n_cores)
    data = pd.concat(pool.map(partial(apply_parallel,
                                      long_column=long_column, lat_column=lat_column,
                                      sec=sec, type=type, password=password), split_df))
    pool.close()
    pool.join()
    return data


def apply_parallel(df, long_column, lat_column, sec, type, password):
    db = DB(password=password)
    for index, row in df.iterrows():
        df.at[index, 'catchment_area'] = get_catchment_area(row[long_column], row[lat_column], sec, type, db)
        db.commit()
    db.close()
    return df
