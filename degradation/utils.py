

import os
import collections

import pandas as pd
import numpy as np
import pickle


def make_filler():
    """Make a filler dataframe for plotting empty time series.

    Returns
    -------
    filler: pd.DataFrame
        Empty frame with time-series index and dc_power column.
    """
    filler = pd.DataFrame(index=pd.date_range(start='07-25-1989', end='03-25-2018'))
    filler['dc_power'] = np.nan
    filler['dc_power_norm'] = np.nan
    return filler


def make_hovers(df):
    """Make text field for when hovering over points on map.

    Parameters
    ----------
    df: pd.DataFrame
        Metadata must include 'ID', 'Latitude', and 'Longitude' columns.

    Returns
    -------
    df: pd.DataFrame
        Input dataframe plus the 'text' column.
    """
    texts = []
    for idx, x in df.iterrows():
        texts.append(
            '{0} -- {1}<br>{2}, {3}<br>{4}W system<br>Active for {5} days'.format(x['ID'], x['system_name'],
                                                                                  x['county'], x['state (abbr)'],
                                                                                  x['system_size (W)'],
                                                                                  x['active_days'])
        )
    df['text'] = texts
    return df


class DBHandler(object):
    """
    Handle calls to MongoDB for degradation analysis.
    """

    def __init__(self, collection):
        """Create instance.

        Parameters:
        ----------
        collection: pymongo collection
            Time-series performance data.
        """

        self.collection = collection
        self.cache = collections.OrderedDict()
        self.metadata = None

    def get_system_data(self, points, allow_add=False):
        """Query for system-specific performance data.

        Parameters:
        ----------
        points: list-like
            List of unique system_id values (*not* mongo _id values).
        allow_add: bool
            Add new entries to a cache to avoid repetitive queries.

        Returns
        -------
        systems: dict
            Dictionary with {system_id: time-series dataframe} format.
        """

        points = [int(i) for i in points]
        to_retrieve = [i for i in points if i not in self.cache]

        tmp_systems = {}
        if to_retrieve:
            res = pd.DataFrame(list(self.collection.find({'ID': {'$in': to_retrieve}}, {'ID': 1, 'performance': 1, '_id': 0})))
            for idx, df in zip(res['ID'], res['performance']):
                tmp_systems[idx] = pickle.loads(df)

        if allow_add:
            for idx in tmp_systems:
                self.cache[idx] = tmp_systems[idx]
            ret_dict = {i: self.cache[i] for i in points}
        else:
            tmp_dict = {**self.cache, **tmp_systems}
            ret_dict = {i: tmp_dict[i] for i in points}

        return ret_dict

    def get_system_metadata(self):
        """Get metadata of all systems.

        Returns
        -------
        metadata: pd.DataFrame
            Dataframe includes latitude, longitude, system_id, and public_name.
        """
        if self.metadata is None:
            fields = {'ID': 1, 'system_size (W)': 1, 'latitude (deg)': 1, 'longitude (deg)': 1, 'system_name': 1, '_id': 0,
                      'state (abbr)': 1, 'county': 1, 'active_days': 1, 'climate': 1, 'csd_rd': 1, 'yoy_rd': 1, 'ols_rd': 1}
            metadata = pd.DataFrame(list(self.collection.find({}, fields)))
            self.metadata = make_hovers(metadata)
            self.metadata = self.metadata.rename(columns={'system_size (W)': 'Size (W)', 'state (abbr)': 'State',
                                                          'county': 'County', 'climate': 'Climate', 'active_days': 'Active Days'})
        return self.metadata
#
# class DBHandler(object):
#     """
#     Handle calls to MongoDB for degradation analysis.
#     """
#
#     def __init__(self, collection):
#         """Create instance.
#
#         Parameters:
#         ----------
#         collection: pymongo collection
#             Time-series performance data.
#         """
#
#         self.collection = collection
#         self.cache = collections.OrderedDict()
#         self.metadata = None
#
#     def get_system_data(self, points, allow_add=False):
#         """Query for system-specific performance data.
#
#         Parameters:
#         ----------
#         points: list-like
#             List of unique system_id values (*not* mongo _id values).
#         allow_add: bool
#             Add new entries to a cache to avoid repetitive queries.
#
#         Returns
#         -------
#         systems: dict
#             Dictionary with {system_id: time-series dataframe} format.
#         """
#
#         points = [int(i) for i in points]
#         to_retrieve = [i for i in points if i not in self.cache]
#
#         tmp_systems = {}
#         if to_retrieve:
#             res = pd.DataFrame(list(self.collection.find({'ID': {'$in': to_retrieve}}, {'ID': 1, 'df': 1, '_id': 0})))
#             for idx, df in zip(res['ID'], res['df']):
#                 tmp_systems[idx] = pickle.loads(df)
#
#         if allow_add:
#             for idx in tmp_systems:
#                 self.cache[idx] = tmp_systems[idx]
#             ret_dict = {i: self.cache[i] for i in points}
#         else:
#             tmp_dict = {**self.cache, **tmp_systems}
#             ret_dict = {i: tmp_dict[i] for i in points}
#
#         return ret_dict
#
#     def get_system_metadata(self):
#         """Get metadata of all systems.
#
#         Returns
#         -------
#         metadata: pd.DataFrame
#             Dataframe includes latitude, longitude, system_id, and public_name.
#         """
#         if self.metadata is None:
#             fields = {'ID': 1, 'System Size(W)': 1, 'Latitude': 1, 'Longitude': 1, 'System Name': 1, '_id': 0,
#                       'State': 1, 'County': 1, 'Active Days': 1}
#             metadata = pd.DataFrame(list(self.collection.find({}, fields)))
#             self.metadata = make_hovers(metadata)
#         return self.metadata
