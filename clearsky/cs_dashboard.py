
import os

import pandas as pd
import numpy as np

import dash_core_components as dcc
import dash_html_components as html

from misc.misc_pages import serve_header


# files = [f for f in os.listdir('./clearsky/data') if f.endswith('pkl.gzip')]
# files = [f for f in os.listdir('./clearsky/data') if f.endswith('pkl.gzip')]
files = [None]
print(files)


description = 'Recent research has shown that filtering periods of cloudy skies out of PV degradation rate ' \
              'calculations can significantly impact the results.  In this dashboard, you are encouraged to explore ' \
              'detecting clear sky periods using the PVLib method (https://bit.ly/2E5sArY).  Modify the PVLib ' \
              'parameters to see the effects they have on the data set provided.  You may also upload your own data ' \
              'set to optimize parameters for your own anaylsis.  All previous runs are plotted below.'

description2 = 'Please be patient if you are working with large data sets (especially if it is high frequency).  ' \
               'You may have a better experience using smaller data sets.'


def serve_layout():
    app_layout = \
    html.Div([
        serve_header(),
        html.H1('Clear Sky Detection'),
        html.P(description),
        html.P(description2),
        html.Div([
            html.Div([
                html.H4('Select data set: '),
                dcc.Dropdown(
                    id='cs-site',
                    options=[{'label': i, 'value': i} for i in files],
                    value=files[0]
                )
            ], className='three columns'),
            html.Div([
                html.H4(children='Select start and end dates: '),
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
        ], className='row', style={'fontSize': '14'}),
        html.Div([
            html.Div([
                html.H4(children='Select data frequency: '),
                dcc.Dropdown(
                    id='cs-freq',
                    options=[{'label': '{} minutes'.format(i), 'value': i} for i in [1, 5, 10, 15, 30]],
                    value=30,
                )
            ], className='three columns'),
            html.Div([
                html.H4(children='Set window length (minutes): '),
                dcc.Input(
                    id='cs-window_length_slider',
                    min=0,
                    max=180,
                    step=1,
                    value=90,
                    type='Number',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H4(children='Set average difference: '),
                dcc.Input(
                    id='cs-mean_diff_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=75,
                    type='number',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ] , className='three columns'),
            html.Div([
                html.H4(children='Set maximum difference: '),
                dcc.Input(
                    id='cs-max_diff_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=75,
                    type='number',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
        ], className='row'),
        html.Div([
            html.Div([
                html.H4('Set upper line length: '),
                dcc.Input(
                    id='cs-upper_ll_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=10,
                    type='number',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H4('Set lower line length: '),
                dcc.Input(
                    id='cs-lower_ll_slider',
                    min=-500,
                    max=0,
                    step=1,
                    value=-5,
                    type='number',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H4('Set standard deviation of slopes: '),
                dcc.Input(
                    id='cs-vardiff_slider',
                    min=0,
                    max=1,
                    step=.005,
                    value=.005,
                    type='number',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
            html.Div([
                html.H4('Set maximum difference of slopes: '),
                dcc.Input(
                    id='cs-slopedev_slider',
                    min=0,
                    max=500,
                    step=1,
                    value=8,
                    type='number',
                    style={'height': '35px', 'fontFamily': 'HelveticaNeue', 'width': '100%'},
                )
            ], className='three columns'),
        ], className='row'),
            # html.Div([
            #     html.H4(['Mean difference:  ',
            #         dcc.Input(
            #             id='cs-mean_diff_slider',
            #             min=0,
            #             max=500,
            #             step=1,
            #             value=75,
            #             type='number',
            #             # marks={str(i): i for i in np.arange(0, 501, 25)}
            #         )] , className='six columns'),
            #     html.H4(['Max difference',
            #         dcc.Input(
            #             id='cs-max_diff_slider',
            #             min=0,
            #             max=500,
            #             step=1,
        #                 value=75,
        #                 type='number',
        #                 # marks={str(i): i for i in np.arange(0, 501, 25)}
        #         )] , className='six columns')
        #     ], style={'width': '90%'}),
        #     html.H4([
        #     html.H4(['Upper line length',
        #         dcc.Slider(
        #             id='cs-upper_ll_slider',
        #             min=0,
        #             max=500,
        #             step=1,
        #             value=10,
        #             marks={str(i): i for i in np.arange(0, 501, 25)}
        #         )] , className='six columns'),
        #     html.H4(['Lower line length',
        #         dcc.Slider(
        #             id='cs-lower_ll_slider',
        #             min=-500,
        #             max=0,
        #             step=1,
        #             value=-5,
        #             marks={str(i): i for i in np.arange(-500, 0, 25)}
        #         )] , className='six columns')
        #     ], style={'width': '90%'}),
        #     html.H4([
        #     html.H4(['Standard deviation of slope',
        #         dcc.Slider(
        #             id='cs-vardiff_slider',
        #             min=0,
        #             max=1,
        #             step=.005,
        #             value=0.005,
        #             marks={str(np.round(i, 4)): str(np.round(i, 4)) for i in np.arange(0, 1, .05)}
        #         )] , className='six columns'),
        #     html.H4(['Max slope difference',
        #         dcc.Slider(
        #             id='cs-slopedev_slider',
        #             min=0,
        #             max=500,
        #             step=1,
        #             value=8,
        #             marks={str(i): i for i in np.arange(0, 501, 25)}
        #         )] , className='six columns'),
        #     ], style={'width': '90%'})
        # ], className='row'),
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
