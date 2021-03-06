

import os
import base64
import io

import pandas as pd
import numpy as np

from clearsky.clearsky_detection import cs_detection


# def read_df(file, start_date, end_date, freq):
#     ground_df = pd.read_pickle(os.path.join('./clearsky_data', 'ornl_irrad_ground.pkl.gzip'))
#     nsrdb_df = pd.read_pickle(os.path.join('./clearsky_data', 'ornl_irrad_nsrdb.pkl.gzip'))
#
#     ground_master = cs_detection.ClearskyDetection(ground_df, 'GHI', 'Clearsky GHI pvlib')
#     nsrdb_master = cs_detection.ClearskyDetection(nsrdb_df, 'GHI', 'Clearsky GHI pvlib', 'sky_status')
#
#     ground_master.df = ground_master.df[~ground_master.df.index.duplicated(keep='first')]
#     nsrdb_master.df = nsrdb_master.df[~nsrdb_master.df.index.duplicated(keep='first')]
#
#     ground_master.df = ground_master.df.reindex(
#         pd.date_range(ground_master.df.index[0], ground_master.df.index[-1], freq='T').fillna(0)
#     )
#     # ground_master.trim_dates('06-01-2008', '07-01-2008')
#     # nsrdb_master.trim_dates('06-01-2008', '07-01-2008')
#     ground_master.trim_dates(start_date, end_date)
#     nsrdb_master.trim_dates(start_date, end_date)

#     ground_master.downsample(freq)

#     mask, _ = ground_master.get_mask_tsplit(nsrdb_master, ignore_nsrdb_mismatch=False)
#     return ground_master, mask

# def read_df(file, start_date, end_date, freq):
def read_df(contents, filename):
    """Read dataframe from a file.  Review dash tutorial on file uploading - mainly copied from there.

    Returns:
        dataframe of time-series values
    """
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    else:
        df = pd.read_csv('./clearsky_data/example_clearsky.csv')

    # df = pd.read_csv('./clearsky_data/example_clearsky.csv')
    df.index = pd.to_datetime(df['datetime'])
    # df = df[~df.index.duplicated(keep='first')]
    # df = df.reset_index(pd.date_range(start=pd.to_datetime(df.index[0]),
    #                                   end=pd.to_datetime(df.index[-1]), freq='{}min'.format(freq)))

    return df


def dict_to_text(d):
    text = ''
    for key in ['F-score', 'window length', 'mean diff', 'max diff',
                'upper line length', 'lower line length', 'std slope', 'max slope diff']:
        text += key.title() + ': ' + str(np.round(d[key], 6)) + '<br>'
    return text


def df_to_text(df):
    text_list = []
    key_list = ['Window length', 'Mean difference', 'Max difference',
                'Upper line length', 'Lower line length', 'Max difference of slopes', 'Variance of slopes']
    for idx, row in df.iterrows():
        text = ''
        for key in key_list:
            text += key.title() + ': ' + str(np.round(row[key], 6)) + '<br>'
        text_list.append(text)
    return text_list

