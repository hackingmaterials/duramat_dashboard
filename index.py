

import base64

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

from app import app, client
from misc.misc_pages import serve_header, serve_error

# from clearsky import cs_dashboard

from degradation import deg_dashboard
from degradation import callbacks as deg_callbacks
from degradation.utils import DBHandler


encoded_logo = base64.b64encode(open('./images/duramat_logo.png', 'rb').read())
encoded_degradation = base64.b64encode(open('./images/icon-data-management.png', 'rb').read())
encoded_clearsky = base64.b64encode(open('./images/icon-module-testing.png', 'rb').read())





layout = html.Div([
    serve_header(),
    html.Br(),
    html.H1('DuraMAT Data Analytics'),
    html.Div([
        html.P('The Durable Module Materials Consortium (DuraMAT) combines government, academic, and industry '
                'expertise in order to discover, de-risk, and enable commercialization of new material designs '
                'for photovoltaic (PV) modules.  This project works in concert with other Department of Energy (DOE) '
                'projects to help realize a levelized cost of electricity less than 3 cents per kilowatt-hour.'),
        html.P('A large part of the DuraMAT effort is developing data analytics, visualization, and machine learning '
               'tools to accelerate research.  This website will showcase current and completed data-driven projects '
               'through interactive visualaztion and analytics pipelines.'),
        html.P('For more information on DuraMAT, follow the link in the navigation bar at the top of the page.  '
               'If you are interested in sharing your data with DuraMAT, with the potenial of developing interactive '
               'dashboards, please start by visiting the DuraMAT DataHub link above.'),
    ], style={'margin-left': '20px'}),
    html.H2('Dashboards'),
    html.Div([
        html.Div([
            html.Div([
                dcc.Link('PV Degradation', href='/degradation',
                         style={'display': 'inline-block', 'text-decoration': 'none'}),
            ]),
            html.Div([
                html.Div([
                    html.P('Explore degradation of PV systems across the United States.  '
                           'Select different systems based on' 'nameplate size, technology type, '
                           'geographic location, and so on.  Apply data filters and apply '
                           'degradation rate calculations such as ordinary least squares or year-on-year.',
                           style={'textAlign': 'justfiy', 'text-justify': 'inter-word'})],
                           style={'float': 'left', 'width': '700px'}),
                # html.Div([
                #     html.Img(src='data:image/png;base64,{}'.format(encoded_degradation.decode()), style={'width': '125px'}),
                # ], style={'margin-left': '720px', 'vertical-align': 'top', 'float': 'left'})
            ], style={'display': 'inline-block'}),
        ], style={'float': 'left'}),
        html.Div([
            html.Div([
                dcc.Link('Clear sky detection', href='/clearsky',
                         style={'display': 'inline-block', 'text-decoration': 'none'}),
            ]),
            html.Div([
                html.Div([
                    html.P('Interactively explore PVLib\'s clear sky detection algorithm.  '
                           'Set the parameters and score classifications against known sky conditions.  Use your '
                           'optimal parameters downstream in your degradation rate calculations or visit the '
                           'PV Degradation dashboard to see its effect.')],
                    style={'textAlign': 'justfiy', 'textJustify': 'inter-word'})],
                style={'float': 'left', 'width': '700px'}),
                # html.Div([
                #     html.Img(src='data:image/png;base64,{}'.format(encoded_clearsky.decode()), style={'width': '125px'}),
                # ], style={'margin-left': '720px', 'vertical-align': 'top', 'float': 'left'})
            ], style={'float': 'left'}),
    ], style={'margin-left': '20px'})
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
    elif pathname == '/clearsky':
        # return deg_dashboard.serve_layout(deg_db_handler)
        # return deg_dashboard.app_layout
        # cs_dashboard.SCORES = []
        # return cs_dashboard.app_layout
        return serve_error()
        # pass
    # elif pathname == ''
    else:
        return layout


deg_db_handler = DBHandler(client.pvproduction.time_series)
deg_callbacks.add_callbacks(app, deg_db_handler)


if __name__ == '__main__':
    app.run_server(threaded=True)
    # app.run_server(debug=True, threaded=True)
