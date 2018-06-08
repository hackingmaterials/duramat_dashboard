
import os


import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly.graph_objs as go
from misc.misc_pages import serve_header

import numpy as np

from . import utils

from app import client


def serve_layout(db_handler):
    mapbox_access_token = os.environ['MAPBOX_KEY']
    metadata = db_handler.get_system_metadata()
    map_layout = go.Layout(mapbox={'accesstoken': mapbox_access_token, 'bearing': 0, 'center': {'lat':38, 'lon': -96},
                       'pitch': 0, 'zoom': 2.5, 'style': 'light'}, hovermode='closest', autosize=True, height=480,
                       showlegend=False, margin={'r': 0, 't': 0, 'b': 0, 'l': 0, 'pad': 0})

    # degradation page layout
    app_layout =  \
    html.Div([
        serve_header(),
        html.H1(children='PV Degradation Dashboard'),
            html.P('Explore PV performance and degradation data over time.  Select sites on the map by clicking them '
                   'or by selecting them in the table to the right.  Sites can be de-selected by clicking them on '
                   'the map a second time, or by un-checking them in the table.  Once you have selected the desired '
                   'sites, scroll down for additional options and analysis.  Summary statistics for the sites you '
                   'have chosen will be presented at the end.'),
            html.Div([html.H3('Systems overview', style={'textAlign': 'center'}),
            html.Div([
                html.Div([
                        dcc.Graph(id='degradation-map', animate=True,
                                  figure={'data': [go.Scattermapbox(lon=metadata['longitude (deg)'].values,
                                                                    lat=metadata['latitude (deg)'].values,
                                                                    customdata=metadata['ID'], text=metadata['text'],
                                                                    marker={'color': np.log(metadata['Size (W)'])}),],
                                          'layout': map_layout})
                ], className='six columns'),
                html.Div([
                    dt.DataTable(
                        rows=metadata[['ID', 'Size (W)', 'State', 'County', 'Climate', 'Active Days']].to_dict('records'),
                        columns=['ID', 'Size (W)', 'State', 'County', 'Climate', 'Active Days'],
                        row_selectable=True,
                        sortable=True,
                        filterable=True,
                        selected_row_indices=[],
                        editable=False,
                        id='degradation-metadata_table',
                    ),
                ], className='six columns', style={'margin': {'r': 0, 't': 0, 'b': 0, 'l': 0}}),
                # ], className='six columns', style={'margin': {'r': 20, 't': 40, 'b': 20, 'l': 20, 'pad': 0}, 'height': '500px'}),
            ], className='row'),
        ]),
        html.Div(id='degradation-selected', children=[
            html.H3('Time-series PV performance', style={'textAlign': 'center'}),
            html.Div([
                dcc.RadioItems(
                    id='degradation-data_smoother',
                    options=[{'label': 'Raw data  ', 'value': 'raw'},
                             {'label': 'Rolling mean  ', 'value': 'rolling'},
                             {'label': 'Classical seasonal decomposition  ', 'value': 'csd'}],
                    value='raw',
                    labelStyle={'display': 'inline-block'}
                )
            ], className='container'),
            html.Div([
                dcc.Graph(id='degradation-selected_graph')
            ]),
        ], style={'visibility': 'hidden'}),
        html.Div(id='degradation-deg_modes_master', children=[
            html.Div([
                dcc.Graph(id='degradation-deg_modes_histogram')
            ], className='six columns'),
            html.Div([
                dcc.Graph(id='degradation-deg_modes_by_site')
            ], className='six columns'),
        ], className='row'),
        html.Div(id='degradation-meta_figure'),
        # html.Div(id='degradation-deg_modes_master', children=[
        #     html.Div([
        #         html.H3('Set filters and select rate calculation method', style={'textAlign': 'center'}),
        #     ], style={'textAlign': 'center'}),
        #     html.Div([
        #         html.Div([
        #             html.P('Low insolation cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
        #             html.P('High insolation cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
        #             html.P('Low production cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
        #             html.P('High production cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
        #         ], className='row'),
        #         html.Div([
        #             dcc.Input(value=0, type='number', id='degradation-insol_low', inputmode='numeric',
        #                       placeholder='Low insolation cutoff', className='three columns'),
        #             dcc.Input(value=10000, type='number', id='degradation-insol_hi', inputmode='numeric',
        #                       placeholder='High insolation cutoff', className='three columns'),
        #             dcc.Input(value=0, type='number', id='degradation-prod_low', inputmode='numeric',
        #                       placeholder='Low production cutoff', className='three columns'),
        #             dcc.Input(value=10, type='number', id='degradation-prod_hi', inputmode='numeric',
        #                       placeholder='High production cutoff', className='three columns'),
        #         ], className='row'),
        #     ], className='container', style={'justifyContent': 'center'}),
        #     html.P('Select desired smoothing and rate calculation strategies.  Be patient if you have selected '
        #            'a large number of sites and/or several calculation methods.', style={'textAlign': 'center'}),
        #     html.Div([
        #         html.Div([
        #             html.Div([
        #                 dcc.Dropdown(
        #                 id='degradation-deg_modes',
        #                 options=[{'label': i, 'value': i} for i in ['Rolling', 'OLS', 'CSD', 'LOWESS', 'YOY']],
        #                 value=[], multi=True, placeholder='Select degradation rate calculation method...',
        #                 ),
        #             ], style={'height': '35px'}, className='nine columns'),
        #             html.Div([
        #                 html.Button('Set methods', id='degradation-run_button', style={'height': '35px', 'width': '210px'}),
        #             ], className='three columns'),
        #         ], className='row'),
        #     ], style={'float': 'center'}, className='container')
        # ], style={'visibility': 'hidden', 'textAlign': 'center'}),
        # html.Div(id='degradation-deg_plots'),
        html.Div(id='degradation-hidden', style={'display': 'none'}),
    ])

    return app_layout


