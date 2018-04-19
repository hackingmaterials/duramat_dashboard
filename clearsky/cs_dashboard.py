
import os

import pandas as pd
import numpy as np

import pvlib

# from sklearn import linear_model
from sklearn import metrics
# import statsmodels.api as sm

import dash
import dash_core_components as dcc
import dash_html_components as html

import plotly.graph_objs as go

import sys
# sys.path.append(os.path.expanduser('~/duramat'))
# from clearsky_detection import cs_detection

from app import app


SCORES = []
SITES_CACHE = {}

# app = dash.Dash()

files = [f for f in os.listdir('./clearsky/data') if f.endswith('pkl.gzip')]
print(files)

def read_df(file=files[0]):
    ground_df = pd.read_pickle(os.path.join('./clearsky/data', 'ornl_irrad_ground.pkl.gzip'))
    nsrdb_df = pd.read_pickle(os.path.join('./clearsky/data', 'ornl_irrad_nsrdb.pkl.gzip'))

    ground_master = cs_detection.ClearskyDetection(ground_df, 'GHI', 'Clearsky GHI pvlib')
    nsrdb_master = cs_detection.ClearskyDetection(nsrdb_df, 'GHI', 'Clearsky GHI pvlib', 'sky_status')

    ground_master.df = ground_master.df[~ground_master.df.index.duplicated(keep='first')]
    nsrdb_master.df = nsrdb_master.df[~nsrdb_master.df.index.duplicated(keep='first')]

    ground_master.df = ground_master.df.reindex(
        pd.date_range(ground_master.df.index[0], ground_master.df.index[-1], freq='T').fillna(0)
    )
    ground_master.trim_dates('06-01-2008', '07-01-2008')
    nsrdb_master.trim_dates('06-01-2008', '07-01-2008')

    ground_master.downsample(10)

    mask, _ = ground_master.get_mask_tsplit(nsrdb_master, ignore_nsrdb_mismatch=False)
    print('rock and roll!')
    return ground_master, mask

description = 'Explore detecting clear sky periods using the PVLib method (https://bit.ly/2E5sArY).'
description += '  Use sliders to set the thresholds and visualize the results.  Previous runs are tracked so you can copy down the optimal parameters.'
description += '  Be patient with long data sets - the method can take some time to converge.'
df = read_df()

app_layout = \
html.Div([
    html.H1(children='Clear Sky Detection Dashboard', style={'textAlign': 'center'}),
    html.H6('Developed by the Hacking Materials Research Group at Lawrence Berkeley National Laboratory', style={'textAlign': 'center'}),
    html.P('Click \'Back\' button in your browser to return to the homepage.', style={'textAlign': 'center'}),
    html.P(description, style={'textAlign': 'center'}),
    # html.H2(children='Select sites'),
    html.Div([
        dcc.Dropdown(
            id='cs-site',
            options=[{'label': i, 'value': i} for i in files],
            value=files[0]
        )], style={'width': '50%', 'display': 'none'}),
    html.H3(children='Select dates'),
    html.Div([
        dcc.DatePickerRange(
            id='cs-date_picker',
            start_date=pd.to_datetime('06-01-2008'),
            end_date=pd.to_datetime('07-01-2008')
        )], style={'width': '50%'}),
    html.Div([
        html.H3(['Window length',
            dcc.Slider(
                id='cs-window_length_slider',
                min=0,
                max=180,
                step=1,
                value=90,
                marks={str(i): i for i in np.arange(0, 181, 10)}
            )], style={'width': '90%'}),
        html.H3([
        html.H3(['Mean difference',
            dcc.Slider(
                id='cs-mean_diff_slider',
                min=0,
                max=500,
                step=1,
                value=75,
                marks={str(i): i for i in np.arange(0, 501, 25)}
            )] , className='six columns'),
        html.H3(['Max difference',
            dcc.Slider(
                id='cs-max_diff_slider',
                min=0,
                max=500,
                step=1,
                value=75,
                marks={str(i): i for i in np.arange(0, 501, 25)}
            )] , className='six columns')# ,
        ], style={'width': '90%'}),
        html.H3([
        html.H3(['Upper line length',
            dcc.Slider(
                id='cs-upper_ll_slider',
                min=0,
                max=500,
                step=1,
                value=10,
                marks={str(i): i for i in np.arange(0, 501, 25)}
            )] , className='six columns'),
        html.H3(['Lower line length',
            dcc.Slider(
                id='cs-lower_ll_slider',
                min=-500,
                max=0,
                step=1,
                value=-5,
                marks={str(i): i for i in np.arange(-500, 0, 25)}
            )] , className='six columns')
        ], style={'width': '90%'}),
        html.H3([
        html.H3(['Standard deviation of slope',
            dcc.Slider(
                id='cs-vardiff_slider',
                min=0,
                max=1,
                step=.005,
                value=0.005,
                marks={str(np.round(i, 4)): str(np.round(i, 4)) for i in np.arange(0, 1, .05)}
                # marks={str(np.round(i, 2)): str(np.round(i, 2)) for i in np.arange(0, 2, .1)}
            )] , className='six columns'),
        html.H3(['Max slope difference',
            dcc.Slider(
                id='cs-slopedev_slider',
                min=0,
                max=500,
                step=1,
                value=8,
                marks={str(i): i for i in np.arange(0, 501, 25)}
            )] , className='six columns'),
        ], style={'width': '90%'})
    ], className='row'),
    html.Div(id='cs-output')
])

@app.callback(
    dash.dependencies.Output('cs-output', 'children'),
    [dash.dependencies.Input('cs-site', 'value'),
     dash.dependencies.Input('cs-date_picker', 'start_date'),
     dash.dependencies.Input('cs-date_picker', 'end_date'),
     dash.dependencies.Input('cs-window_length_slider', 'value'),
     dash.dependencies.Input('cs-mean_diff_slider', 'value'),
     dash.dependencies.Input('cs-max_diff_slider', 'value'),
     dash.dependencies.Input('cs-upper_ll_slider', 'value'),
     dash.dependencies.Input('cs-lower_ll_slider', 'value'),
     dash.dependencies.Input('cs-vardiff_slider', 'value'),
     dash.dependencies.Input('cs-slopedev_slider', 'value'),
     ]
)
def update_plot(site, start_date, end_date, window_length, mean_diff, max_diff,
                upper_ll, lower_ll, vardiff, slopedev):
    print('updating...')
    ground_master, mask = read_df(site)
    df = ground_master.df
    is_clear = \
        pvlib.clearsky.detect_clearsky(df['GHI'], df['Clearsky GHI pvlib'], df.index,
                                       window_length=window_length, mean_diff=mean_diff,
                                       max_diff=max_diff, upper_line_length=upper_ll, lower_line_length=lower_ll,
                                       slope_dev=slopedev, var_diff=vardiff)
    score = metrics.fbeta_score(ground_master.df[mask]['sky_status'], is_clear[mask], beta=.5)
    print('score: ', score)
    plots = []
    plots.append(go.Scatter(x=df.index, y=df['GHI'], name='GHI'))
    plots.append(go.Scatter(x=df.index, y=df['GHI nsrdb'].interpolate(), name='GHI(NSRDB)'))
    plots.append(go.Scatter(x=df.index, y=df['Clearsky GHI pvlib'], name='GHI(CS)'))
    plots.append(go.Scatter(x=df[is_clear].index, y=df[is_clear]['GHI'], name='PVLib clear', mode='markers'))
    plots.append(go.Scatter(x=df[mask & df['sky_status'].astype(bool)].index,
                            y=df[mask & df['sky_status'].astype(bool)]['GHI'],
                            name='NSRDB clear', mode='markers', marker={'symbol': 'circle-open', 'line': {'width': 3}, 'size': 10}))
    layout = go.Layout(xaxis={'title': 'Date'}, yaxis={'title': 'W/m2'},
                       title='Window length: {}, mean diff: {}, max diff: {}, upper line length: {}, lower line length: {}, max slope difference: {}, std slope differece: {}'\
                              .format(window_length, mean_diff, max_diff, upper_ll, lower_ll, slopedev, vardiff))
    SCORES.append({'window length': window_length, 'mean diff': mean_diff, 'max diff': max_diff,
                   'upper line length': upper_ll, 'lower line length': lower_ll,
                   'std slope': vardiff, 'max slope diff': slopedev, 'F-score': score})
    ts_plot = dcc.Graph(id='cs-plot', figure={'data': plots, 'layout': layout})
    scores = [go.Scatter(x=list(range(len(SCORES))),
                         y=[i['F-score'] for i in SCORES], text=[dict_to_text(i) for i in SCORES], hoverinfo='text')]
    scores_layout = go.Layout(xaxis={'title': 'Run', 'tickvals': [i for i in range(1, len(SCORES))], 'ticktext': [str(i + 1) for i in range(1, len(SCORES))],
                                     'range': [0, len(SCORES)]}, yaxis={'title': 'F-score'}, title='Previous runs')
    scores_plot = dcc.Graph(id='cs-scores', figure={'data': scores, 'layout': scores_layout})
    final = html.Div([
                html.Div([html.H3('Time series visual'), ts_plot], className='six columns'),
                html.Div([html.H3('Past runs'), scores_plot], className='six columns')
           ])
    # final = [html.Div([html.H3('Time series visual'), ts_plot]),
    #         html.Div([html.H3('Past runs'), scores_plot])]
    final = [html.Div(ts_plot),
             html.Div(scores_plot)]

    return final

def dict_to_text(d):
    text = ''
    for key in ['F-score', 'window length', 'mean diff', 'max diff',
                'upper line length', 'lower line length', 'std slope', 'max slope diff']:
        text += key.title() + ': ' + str(np.round(d[key], 6)) + '<br>'
    return text

# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})
# app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# if __name__ == '__main__':
#     try:
#         app.run_server(debug=True)
#     except OSError:
#         app.run_server(debug=True, port=8051)
#
