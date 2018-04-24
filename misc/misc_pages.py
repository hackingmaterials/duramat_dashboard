

import base64

import dash_html_components as html
import dash_core_components as dcc


def serve_header():
    link_style = {'float': 'left', 'textAlign': 'center', 'padding': '14px 16px', 'display': 'inline',
                  'text-decoration': 'none'}
    link_style_r = {'float': 'left', 'textAlign': 'right', 'padding': '14px 16px', 'display': 'inline',
                    'text-decoration': 'none'}
    encoded_duramat = base64.b64encode(open('./images/duramat_logo.png', 'rb').read())
    encoded_doe = base64.b64encode(open('./images/doe-logo.png', 'rb').read())
    # img_style = {'float': 'right', 'textAlign': 'center',
    #              'padding': '14px 16px', 'display': 'inline', 'width': '200px'}

    header = html.Div([
        html.Div([
            html.Div([
                dcc.Link('Home', href='/', style=link_style),
                dcc.Link('Degradation', href='/degradation', style=link_style),
                dcc.Link('Clear sky detection', href='/clearsky', style=link_style),
                html.A('Submit an issue', href='https://github.com/hackingmaterials/duramat_dashboard/issues/new',
                       style=link_style),
                html.A('DuraMAT', href='https://www.duramat.org/', style=link_style),
                html.A('DataHub', href='https://datahub.duramat.org/', style=link_style),
            ], style={'float': 'left', 'textAlign': 'center'}),
            html.Div([
                html.Img(src='data:image/png;base64,{}'.format(encoded_duramat.decode()),
                         style={'width': '100px', 'float': 'right'}),
                html.Img(src='data:image/png;base64,{}'.format(encoded_doe.decode()),
                         style={'width': '100px', 'float': 'right', 'padding': '5px'}),
            ], style={'float': 'right'})
        ])
    ], style={'display': 'inline-block', 'width': '100%', 'textAlign': 'center'})

    return header

def serve_error():
    page = html.Div([
        serve_header(),
        html.H1('Page currently under construction...  Check back soon!')
    ])

    return page
