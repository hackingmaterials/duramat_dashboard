
import os


import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
import plotly.graph_objs as go

from . import utils

from app import client


def serve_layout(db_handler):
    mapbox_access_token = os.environ['MAPBOX_KEY']
    metadata = db_handler.get_system_metadata()
    map_layout = go.Layout(mapbox={'accesstoken': mapbox_access_token, 'bearing': 0, 'center': {'lat':38, 'lon': -96},
                       'pitch': 0, 'zoom': 2.5, 'style': 'light'}, hovermode='closest', autosize=True, height=450,
                       showlegend=False,  margin={'r': 20, 't': 40, 'b': 20, 'l': 20, 'pad': 0})

    # degradation page layout
    app_layout =  \
    html.Div([
        html.H1(children='PV Degradation Dashboard', style={'textAlign': 'center'}),
            html.H6('Explore PV performance and degradation data over time.  ',
                    style={'textAlign': 'center'}),
            html.P('Click \'Back\' button in your browser to return to the homepage.', style={'textAlign': 'center'}),
            html.Div([html.H3('Systems overview', style={'textAlign': 'center'}),
            # html.Div([html.H3('Site Map', style={'textAlign': 'center'}),
            # html.Div([html.P('Hover over site to see preview.  If nothing shows, then the site is missing production data. '
            #                  'Click on a point to enable further analysis.  Clicking point again will remove it from '
            #                  'further analysis.', style={'textAlign': 'center'})]),
            html.Div([html.P('Select sites for further analysis by clicking them on the map or selecting them '
                             'in the adjacent table.  Scroll down once the desired sites have been slected.',
                             style={'textAlign': 'center'})]),
            html.Div([
                html.Div([
                        dcc.Graph(id='degradation-map', animate=True,
                                  figure={'data': [go.Scattermapbox(lon=metadata['Longitude'].values,
                                                                    lat=metadata['Latitude'].values,
                                                                    customdata=metadata['ID'], text=metadata['text'])],
                                          'layout': map_layout})
                ], className='six columns'),
                html.Div([
                    html.Div([
                    #     dcc.RadioItems(
                    #         id='degradation-table_sort_col',
                    #         options=[{'label': i, 'value': i} for i in ['ID', 'System Size(W)', 'State', 'Active Days']],
                    #         value='ID',
                    #         labelStyle={'display': 'inline-block'}, className='six columns'
                    #     ),
                    #     # html.P(' | ', className='one column'),
                    #     dcc.RadioItems(
                    #         id='degradation-table_sort_dir',
                    #         options=[{'label': 'Ascending', 'value': True}, {'label': 'Descending', 'value': False}],
                    #         value=True,
                    #         labelStyle={'display': 'inline-block'}, className='six columns'
                    #     )
                    ], style={'height': '38px'}),
                    dt.DataTable(
                        rows=metadata[['ID', 'System Name', 'System Size(W)', 'State',
                                       'County', 'Latitude', 'Longitude', 'Active Days']].to_dict('records'),
                        columns=['ID', 'System Name', 'System Size(W)', 'State',
                                 'County', 'Latitude', 'Longitude', 'Active Days'],
                        row_selectable=True,
                        selected_row_indices=[],
                        sortable=False,
                        filterable=False,
                        editable=False,
                        id='degradation-metadata_table',
                    ),
                ], className='six columns', style={'margin': {'r': 20, 't': 40, 'b': 20, 'l': 20, 'pad': 0}, 'height': '500px'}),
            ], className='row'),
        ]),
        html.Div(id='degradation-selected'),
        html.Div(id='degradation-deg_modes_master', children=[
            html.Div([
                html.H3('Set filters and select rate calculation method', style={'textAlign': 'center'}),
            ], style={'textAlign': 'center'}),
            html.Div([
                html.Div([
                    html.P('Low insolation cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
                    html.P('High insolation cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
                    html.P('Low production cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
                    html.P('High production cutoff (daily)', className='three columns', style={'textAlign': 'center'}),
                ], className='row'),
                html.Div([
                    dcc.Input(value=0, type='number', id='degradation-insol_low', inputmode='numeric',
                              placeholder='Low insolation cutoff', className='three columns'),
                    dcc.Input(value=10000, type='number', id='degradation-insol_hi', inputmode='numeric',
                              placeholder='High insolation cutoff', className='three columns'),
                    dcc.Input(value=0, type='number', id='degradation-prod_low', inputmode='numeric',
                              placeholder='Low production cutoff', className='three columns'),
                    dcc.Input(value=10, type='number', id='degradation-prod_hi', inputmode='numeric',
                              placeholder='High production cutoff', className='three columns'),
                ], className='row'),
            ], className='container', style={'justifyContent': 'center'}),
            html.P('You can select multiple smoothing and rate calculation strategies.  Be patient if large number of '
                   'sites or large data sets have been selected.', style={'textAlign': 'center'}),
            html.Div([
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                        id='degradation-deg_modes',
                        options=[{'label': i, 'value': i} for i in ['Rolling', 'OLS', 'CSD', 'LOWESS', 'YOY']],
                        value=[], multi=True, placeholder='Select degradation rate calculation method...',
                        ),
                    ], style={'height': '35px'}, className='nine columns'),
                    html.Div([
                        html.Button('Set methods', id='degradation-run_button', style={'height': '35px', 'width': '210px'}),
                    ], className='three columns'),
                ], className='row'),
            ], style={'float': 'center'}, className='container')
        ], style={'visibility': 'hidden', 'textAlign': 'center'}),
        html.Div(id='degradation-deg_plots'),
        html.Div(id='degradation-hidden', style={'display': 'none'}),
    ])

    return app_layout


