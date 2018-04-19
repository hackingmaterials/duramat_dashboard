

import base64

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

from app import app, client

# from clearsky import cs_dashboard

from degradation import deg_dashboard
from degradation import callbacks as deg_callbacks
from degradation.utils import DBHandler


encoded_logo = base64.b64encode(open('./images/duramat_logo.png', 'rb').read())
encoded_degradation = base64.b64encode(open('./images/icon-data-management.png', 'rb').read())
encoded_clearsky = base64.b64encode(open('./images/icon-module-testing.png', 'rb').read())

header = html.Div([
    dcc.Location(id='header-url', refresh=False),
    html.Nav(
        style={
            'jutifyContent': 'spaceAround',
            'textAlign': 'center'
        },
        children=[
            html.Span(
                html.Img(src='data:image/png;base64,{}'.format(encoded_logo.decode()),
                              style={'width': '200px'}, className='container')
            ),
            html.Span(
                dcc.Link('Home', href='/', style={'fontSize': '20pt'}),
            style={'margin': 'auto'}),
            # style={'margin': 'auto', 'width': '100px'}),
            html.Span(
                dcc.Link('Degradation Dashboard', href='/degradation',
                         style={'margin': 'atuo', 'fontSize': '20pt'}),
            style={'margin': 'auto'}),
            # style={'margin': 'auto', 'width': '100px'}),
            html.Span(
                dcc.Link('Clear Sky Detection', href='/clearsky',
                         style={'margin': 'atuo', 'fontSize': '20pt'}),
            style={'margin': 'auto'}),
        ],
        id='nav_bar'),
], className='row',)

layout = \
html.Div([
    # header,
    html.Div([
        html.Img(src='data:image/png;base64,{}'.format(encoded_logo.decode()),
                 style={'width': '275px', 'float': 'right', 'position': 'relative'}, className='container'),
        html.Div([
            html.H1(children='DuraMAT Data Analytics Dashboard', style={'position': 'relative', 'textAlign': 'center'}),
            # html.H6('Developed by the Hacking Materials Research Group at Lawrence Berkeley National Laboratory', style={'textAlign': 'center'}),
            html.P('Select a link below in order to navigate to a specific dashboard.  '
                   'Please contact us with requests for dashboard-specific features, '
                   'new dashboards, or if if you\'re interested in sharing data.', style={'textAlign': 'center'}),
        ], className='container')
    ], className='row'),
    html.Br(),
    html.Div([
        html.Div([
            dcc.Link('PV Degradation', href='/degradation', className='six columns', style={'textAlign': 'center'}),
            # dcc.Link('Clear sky detection', href='/clearsky', className='six columns', style={'textAlign': 'center'})
        ]),
    ], className='row'),
    html.Div([
        html.Div([
            html.Div([
                html.Img(src='data:image/png;base64,{}'.format(encoded_degradation.decode()), style={'width': '300px', 'display': 'block'}, className='container'),
            ], className='six columns'),
            # html.Div([
            #     html.Img(src='data:image/png;base64,{}'.format(encoded_clearsky.decode()), style={'width': '300px', 'display': 'block'}, className='container'),
            # ], className='six columns'),
        ])
    ], className='row'),
])


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    html.Div(id='useless', children=[
        dt.DataTable(id='tbale-useless', rows=[{}])
    ], style={'display': 'none'}),
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/degradation':
        return deg_dashboard.serve_layout(deg_db_handler)
        # return deg_dashboard.app_layout
    elif pathname == '/clearsky':
        # return deg_dashboard.serve_layout(deg_db_handler)
        # return deg_dashboard.app_layout
        # cs_dashboard.SCORES = []
        # return cs_dashboard.app_layout
        pass
    else:
        return layout


deg_db_handler = DBHandler(client.pvproduction.time_series)
deg_callbacks.add_callbacks(app, deg_db_handler)


if __name__ == '__main__':
    app.run_server(threaded=True)
    # app.run_server(debug=True, threaded=True)
