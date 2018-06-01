
import os

import pandas as pd
import numpy as np

import dash_core_components as dcc
import dash_html_components as html

from misc.misc_pages import serve_header


description = dcc.Markdown("""
Recent research has shown that filtering periods of cloudy skies out of PV degradation rate 
calculations can significantly impact the results.  In this dashboard, you are encouraged to explore 
detecting clear sky periods using the algorithm from [PVLib](https://bit.ly/2E5sArY).  Modify the PVLib 
parameters to see how they effect clear sky classifications.  You can also upload your own data 
set and optimize parameters for your analysis.

The plots below will show PVLib clear sky determinations along the time-series data provided.
The values of each of the features used in the classifier can also be plotted by selecting them from
the legend.  Below the time-series plot is a 'race track' visualization that shows which
features are within the supplied thresholds.

Please be patient if you are working with large or high frequency data sets. 
You may have a better experience using smaller data sets.

**If you are uploading your own data** it must be .csv formatted, contain columns named 'datetime', 'GHI', and 'GHIcs',
and have evenly spaced times (mixed frequency data isn't supported).
""")


def serve_layout():
    app_layout = \
    html.Div([
        serve_header(),
        html.H1('Clear Sky Detection'),
        html.Div([
            html.P(description),
        ], style={'margin-left': '20px', 'margin-right': '20px'}),
        html.Div([
            html.Div([
                html.H5('Select data set: '),
                dcc.Upload(
                    html.Button('Upload File'),
                    id='cs-file_upload',
                    contents=None,
                    filename=None,
                )
            ], className='three columns'),
            html.Div([
                html.H5(children='Select start and end dates: '),
                html.Div([
                    html.Div([
                        dcc.Input(
                            id='cs-date_picker_start',
                            type='Date',
                            value=pd.to_datetime('06-01-2008'),
                            style={'height': '30px', 'fontFamily': 'HelveticaNeue'}
                        )
                    ], className='six columns'),
                    html.Div([
                        dcc.Input(
                            id='cs-date_picker_end',
                            type='Date',
                            value=pd.to_datetime('07-01-2008'),
                            style={'height': '30px', 'fontFamily': 'HelveticaNeue'}
                        )
                    ], className='six columns'),
                ], className='row'),
            ], className='three columns'),
            html.Div([
                html.Br(),
            ], className='three columns'),
            html.Div([
                html.H5('Run analysis'),
                html.Button('Detect clear skies', id='cs-run')
            ], className='three columns')
        ], className='row', style={'fontSize': '14'}),
        html.Div([
            html.Div([
                html.H5(children='Select data frequency: '),
                dcc.Dropdown(
                    id='cs-freq',
                    options=[{'label': '{} minutes'.format(i), 'value': i} for i in [1, 5, 10, 15, 30]],
                    value=30,
                )
            ], className='three columns'),
            html.Div([
                html.H5(children='Set window length (minutes): '),
                dcc.Input(
                    id='cs-window_length_slider',
                    min=0,
                    max=180,
                    step=1,
                    value=90,
                    type='Number',
                    inputmode='numeric',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H5(children='Set average difference: '),
                dcc.Input(
                    id='cs-mean_diff_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=75,
                    type='number',
                    inputmode='numeric',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ] , className='three columns'),
            html.Div([
                html.H5(children='Set maximum difference: '),
                dcc.Input(
                    id='cs-max_diff_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=75,
                    type='number',
                    inputmode='numeric',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
        ], className='row'),
        html.Div([
            html.Div([
                html.H5('Set upper line length: '),
                dcc.Input(
                    id='cs-upper_ll_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=10,
                    type='number',
                    inputmode='numeric',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H5('Set lower line length: '),
                dcc.Input(
                    id='cs-lower_ll_slider',
                    min=-500,
                    max=0,
                    step=-1,
                    value=-5,
                    type='number',
                    inputmode='numeric',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H5('Set standard deviation of slopes: '),
                dcc.Input(
                    id='cs-vardiff_slider',
                    min=0,
                    max=1,
                    step=.005,
                    value=.005,
                    type='number',
                    inputmode='numeric',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H5('Set maximum difference of slopes: '),
                dcc.Input(
                    id='cs-slopedev_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=8,
                    type='number',
                    inputmode='numeric',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
        ], className='row'),
        html.Div(id='cs-output'),
        html.Div(id='cs-hidden', style={'display': 'none'}),
        html.Div(id='cs-hidden_data')
    ])

    return app_layout




# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})
# app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# if __name__ == '__main__':
#     try:
#         app.run_server(debug=True)
#     except OSError:
#         app.run_server(debug=True, port=8051)
#
