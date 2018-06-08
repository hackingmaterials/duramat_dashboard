"""
These are 'toy' smoothing/degradation functions.  These will eventually be replaced by those in
existing analytics software (RdTools) or refactored to be more robust/easier to read.
"""

import pandas as pd
import numpy as np

from sklearn import linear_model
import statsmodels.api as sm


def trendline(df, column='Power(W) norm'):
    """Perform linear least squares on data set.

    Parameters
    ----------
    df: pd.DataFrame
    column: str
        Name of column to perform OLS on.

    Returns
    -------
    df: pd.DataFrame
        Input df with new '<column> + trend_ols' column.
    yearly_coef: float
        Yearly degradation rate.
    """
    try:
        df = df[df['mask']]
    except KeyError:
        pass
    # tmp = df[df['mask']][column]
    # df = pd.DataFrame(df.values, columns=['orig'], index=df.index)
    df.name = 'orig'
    df = pd.DataFrame(df)
    print(df)
    tmp = df
    # tmp = df[column]
    tmp = tmp.dropna()
    # print(tmp.index)
    day_vec = tmp.index - tmp.index[0]
    day_vec = day_vec.days.values
    x = day_vec.reshape(-1, 1)
    y = tmp.values.reshape(-1, 1)
    lr = linear_model.LinearRegression()
    lr.fit(x, y)
    full_day_vec = df.index - df.index[0]
    full_day_vec = full_day_vec.days.values
    df['trend ols'] = lr.predict(full_day_vec.reshape(-1, 1))
    daily_coef = lr.coef_[0][0]
    daily_intercept = lr.intercept_[0]
    yearly_coef = daily_coef * 365
    return df['trend ols'], yearly_coef
    # `return df, yearly_coef


def csd(df, column='Power(W) norm'):
    """Perform classical seasonal decomposition on time series data.

    Parameters
    ----------
    df: pd.DataFrame
    column: str
        Column name on which to perform.

    Returns
    -------
    df: pd.DataFrame
        Input df with addtional columns for trend, seasonality, and residuals.
    """
    # try:
    #     df = df[df['mask']]
    # except KeyError:
    #     pass
    # df[column] = df[column].fillna(method='bfill')
    # df[column] = df[column].fillna(method='ffill')
    # ser = df[df.index.isin(pd.date_range(df[column].first_valid_index(), df[column].last_valid_index()))][column]
    # ser = ser.interpolate()
    # res = sm.tsa.seasonal_decompose(ser, two_sided=True, freq=365)
    # # res = sm.tsa.seasonal_decompose(df[column], two_sided=True, freq=365)
    # df[column + ' trend csd'] = res.trend
    # df[column + ' seasonality csd'] = res.seasonal
    # df[column + ' residuals csd'] = res.resid
    # return df
    df = df.fillna(method='bfill')
    df = df.fillna(method='ffill')
    df = df[df.index.isin(pd.date_range(df.first_valid_index(), df.last_valid_index()))]
    df = df.interpolate()
    res = sm.tsa.seasonal_decompose(df, two_sided=True, freq=365)
    df = res.trend
    tmp = pd.DataFrame(df, columns=['orig'])
    print(tmp)
    # res = sm.tsa.seasonal_decompose(df[column], two_sided=True, freq=365)
    tmp['trend csd'] = res.trend
    tmp['seasonality csd'] = res.seasonal
    tmp['residuals csd'] = res.resid
    return tmp['seasonality csd']


def yoy(df, column='Power(W) norm'):
    """Perform year-on-year degradation analysis.

    Parameters
    ----------
    df: pd.DataFrame
    column: str
        Column name for yoy calculation.

    Returns
    -------
    diffs: array
        Shifted differences
    rate: float
        Yearly degradation.
    """
    try:
        df = df[df['mask']]
    except KeyError:
        pass
    # df = df[df['mask']]
    diffs = (df[column].shift(365, freq='D') - df[column]).dropna()
    rate = np.median(diffs)
    return diffs, rate


def rolling_mean(df, column='Power(W) norm'):
    """Perform rolling mean smoothing.

    Parameters
    ----------
    df: pd.DataFrame
    column: str

    Returns
    -------
    df: pd.DataFrame
    """
    # try:
    #     df = df[df['mask']]
    # except KeyError:
    #     pass
    # df = df[df['mask']]
    # if column + ' trend rolling mean' in df.keys():
    #     return df
    # df[column + ' trend rolling mean'] = df[column].rolling('90D').mean()
    return df.rolling('90D').mean()


def lowess(df, column='Power(W) norm'):
    """Perform LOWESS smoothing.

    Parameters
    ----------
    df: pd.DataFrame
    column: str

    Returns
    -------
    df: pd.DataFrame
    """
    try:
        df = df[df['mask']]
    except KeyError:
        pass
    # df = df[df['mask']]
    if column + ' trend lowess' in df.keys():
        return df
    tmp = pd.DataFrame(df, columns=['orig'])
    print(tmp)
    # tmp = sm.nonparametric.lowess(df[column].values, np.arange(len(df)))[:, 1]
    # df[column + ' trend lowess'] = tmp
    tmp = sm.nonparametric.lowess(tmp['orig'].values, np.arange(len(tmp)))[:, 1]
    df['trend lowess'] = tmp
    return df['trend lowess']
    # return df
