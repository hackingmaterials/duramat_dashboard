

import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

from . import degradation_functions as deg


def add_callbacks(app, db_handler):
    metadata = db_handler.get_system_metadata()
    @app.callback(
        Output('degradation-deg_modes_master', 'style'),
        [Input('degradation-metadata_table', 'selected_row_indices'),
         Input('degradation-selected', 'children')]
    )
    def make_deg_mode_dropdown(points, dummy_fig):
        """Create dropdown menu of degradation rate calculation methods.

        Parameters
        ----------
        sites
            List of system_id values (if not empty, menu will show).
        dummy_fig
            Figure that has no effect on functionality.  Included here to force a dependency that makes loading 'prettier'.

        Returns
        -------
        style
            Makes dropdown menu visible.
        """
        site_ids = [metadata.iloc[i]['ID'] for i in points]

        if site_ids:
            style = {'visibility': 'visible'}
        else:
            style = {'visibility': 'hidden'}

        return style

    # @app.callback(
    #     Output('degradation-metadata_table', 'rows'),
    #     [Input('degradation-table_sort_col', 'value'),
    #      Input('degradation-table_sort_dir', 'value')],
    # )
    # def update_table(col_name, col_dir):
    #     # rows = pd.DataFrame(rows)
    #     rows = metadata.sort_values(col_name, ascending=col_dir).copy()
    #     return rows.to_dict('records')


    @app.callback(
        Output('degradation-metadata_table', 'selected_row_indices'),
        [Input('degradation-map', 'clickData'),
         Input('degradation-map', 'selectedData'),
         Input('degradation-metadata_table', 'rows')],
        [State('degradation-metadata_table', 'selected_row_indices')]
    )
    def get_clicked_points(clicked, selected, rows, table_prev):
        """Adds points that have been clicked to a list (or removes them if they have already been clicked).

        Parameters
        ----------
        clicked
            Data from a mouse click.
        previous
            Previously clicked points.

        Returns
        -------
        clicked_points
            JSON encoded list
        """

        if selected is None:
            selected = []
        else:
            selected = [i['pointNumber'] for i in selected['points']]
            # selected = [i['customdata'] for i in selected['points']]

        if clicked is None:
            clicked = []
        else:
            clicked = [i['pointNumber'] for i in clicked['points']]
            # clicked = [i['customdata'] for i in clicked['points']]

        # site_locs = set(selected + clicked)
        # site_locs = np.argwhere(rows['ID'].isin(site_locs))
        # site_locs = [i for i in set(selected + clicked) if i in [x['ID'] for x in rows]]
        # site_locs = sorted(np.argwhere(np.in1d(site_locs, set(selected + clicked))).flatten())
        # site_locs = sorted(np.argwhere(metadata['ID'].isin(set(selected + clicked))).flatten())

        for point in set(selected + clicked):
            if point in table_prev:
                table_prev.remove(point)
            else:
                table_prev.append(point)

        return table_prev

    # @app.callback(
    #     Output('degradation-hidden', 'children'),
    #     [Input('degradation-metadata_table', 'selected_row_indices')]
    # )
    # def do_absolutely_nothing(selected):
    #     print(selected)

    # @app.callback(
    #     Output('degradation-map', 'figure'),
    #     [Input('degradation-metadata_table', 'selected_row_indices')]
    # )
    # def update_map_selected(points):
    #     print('recoloring point numbers: {}'.format(points))
    #     colors = np.zeros(len(metadata),)
    #     colors[points] = 1
    #     cdict = {0: '#1f77b4', 1: '#d62728'}
    #     colors = [cdict[i] for i in colors]
    #     symbols = ['circle-open' for _ in metadata]
    #     # layout = go.Layout(mapbox={'accesstoken': mapbox_access_token, 'style': 'light'}, hovermode='closest',
    #     #                    autosize=True, height=500, showlegend=False,
    #     #                    margin={'r': 20, 't': 40, 'b': 20, 'l': 20, 'pad': 0})
    #
    #     figure={'data': [go.Scattermapbox(lon=metadata['Longitude'].values,
    #                                       lat=metadata['Latitude'].values,
    #                                       customdata=metadata['ID'], text=metadata['text'],
    #                                       marker={'color': colors, 'size': 6})],
    #             'layout': map_layout}

    #     return figure


    @app.callback(Output('degradation-selected', 'children'),
                  [Input('degradation-metadata_table', 'selected_row_indices')])
    def make_individual_figure(points):
        """Plot all clicked points.

        Parameters
        ----------
        points
            List of clicked points

        Returns
        -------
        div
            html.Div object that is empty (if no points clicked) or displays a plot of all sites.
        """
        site_ids = [metadata.iloc[i]['ID'] for i in points]

        if not site_ids:
            return html.Div(style={'display': 'none'})

        plots = []
        systems_loc = db_handler.get_system_data(site_ids, allow_add=True)
        for idx in site_ids:
            df = systems_loc[idx]
            plots.append(go.Scatter(x=df.index, y=df['Power(W) norm'], name=idx))

        if plots:
            figure = {'data': plots,
                      'layout': go.Layout(showlegend=True, autosize=True, height=500,
                                          # margin={'r': 20, 't': 40, 'b': 20, 'l': 60, 'pad': 0},
                                          yaxis={'title': 'Wh/W'})}
            div = html.Div([
                html.H3('Selected Sites', style={'textAlign': 'center'}),
                dcc.Graph(id='degradation-selected_graph', figure=figure),
            ])
        else:
            div = html.Div(style={'display': 'none'})

        return div

    # @app.callback(Output('degradation-hoverplot', 'figure'),
    #               [Input('degradation-map', 'hoverData')])
    # def make_individual_figure_preview(map_graph_hover):
    #     """Create preview of sites based on Wh/Were mouse is hovering over map.
    #
    #     Parameters
    #     ----------
    #     map_graph_hover
    #         Data from nearest point mouse is hovering over
    #
    #     Returns
    #     -------
    #     figure
    #         Plotly figure (empty if not hovering over a point).
    #     """
    #     print(map_graph_hover)
    #     if map_graph_hover is None:
    #         map_graph_hover = {'points': [{'curveNumber': 4,
    #                                         'pointNumber': 569,
    #                                         'customdata': None}]}
    #
    #     chosen_lat = [point['lat'] for point in map_graph_hover['points']]
    #     chosen_lon = [point['lon'] for point in map_graph_hover['points']]
    #     filtered = metadata[(metadata['Latitude'] == chosen_lat) &
    #                         (metadata['Longitude'] == chosen_lon)]
    #     datapoints = filtered['ID'].values
    #     site_ids = sorted(datapoints)
    #     plots = []
    #     systems_loc = db_handler.get_system_data(site_ids, allow_add=False)
    #     for idx in site_ids:
    #         df = systems_loc[idx]
    #         plots.append(go.Scatter(x=df.index, y=df['Power(W) norm'], name=idx))
    #
    #     layout = go.Layout(showlegend=True, autosize=True, height=500,
    #                        margin={'r': 20, 't': 40, 'b': 20, 'l': 60, 'pad': 0},
    #                        yaxis={'title': 'Wh/W'})
    #     if plots:
    #         figure = {'data': plots, 'layout': layout}
    #     else:
    #         layout['showlegend'] = False
    #         figure = {'data': [go.Scatter(x=filler.index, y=filler['dc_power_norm'])], 'layout': layout}
    #
    #     return figure


    @app.callback(
        Output('degradation-deg_plots', 'children'),
        [Input('degradation-metadata_table', 'selected_row_indices'),
         Input('degradation-insol_low', 'value'),
         Input('degradation-insol_hi', 'value'),
         Input('degradation-prod_low', 'value'),
         Input('degradation-prod_hi', 'value'),
         Input('degradation-run_button', 'n_clicks')],
        [State('degradation-deg_modes', 'value')]
    )
    def update_graph(points, insol_low, insol_hi, prod_low, prod_hi, n_clicks, deg_mode):
        """Display smoothed trends and degradation rate statistics for 'clicked' sites.

        Parameters:
        ----------
        sites
            List of sites to chart.
        deg_mode
            List of smoothing/degradation modes.
        Returns
        -------
        div
            html Div that includes 2 rows of charts  - smoothed/trended systems over time and
            summary statistics of the degrdation rates by site and method.
        """
        site_ids = [metadata.iloc[i]['ID'] for i in points]

        if not site_ids:
            return
        if n_clicks == 0:
            return

        dfdict = db_handler.get_system_data(site_ids, allow_add=True)

        for df in dfdict.values():
            df['mask'] = (df['poa_global'] >= insol_low) & (df['poa_global'] <= insol_hi) & \
                         (df['Power(W) norm'] >= prod_low) & (df['Power(W) norm'] <= prod_hi)

        if len(dfdict) == 0 or not deg_mode:
            return html.Div(style={'display': 'none'})

        layout = go.Layout(yaxis={'title': 'Wh/W'})
        yoy_layout = go.Layout(xaxis={'title': 'Degradation (Wh/W/year)'}, yaxis={'title': 'Normalized frequency'})
        plots = []
        yoy_plots = []
        eqns = {'OLS': {}, 'CSD': {}, 'Rolling': {}, 'LOWESS': {}, 'YOY': {}, 'ARIMA': {}}

        for site in sorted(dfdict):
            df = dfdict[site]
            if 'Rolling' in deg_mode:
                df = deg.rolling_mean(df)
                _, eqn = deg.trendline(df, column='Power(W) norm trend rolling mean')
                eqns['Rolling'][site] = eqn
                plots += [
                    go.Scatter(x=df.index, y=df['Power(W) norm trend rolling mean'], name='{} Rolling'.format(site))]
            if 'OLS' in deg_mode:
                df, eqn = deg.trendline(df)
                eqns['OLS'][site] = eqn
                plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend ols'], name='{} OLS'.format(site))]
            if 'CSD' in deg_mode:
                df = deg.csd(df)
                _, eqn = deg.trendline(df, column='Power(W) norm trend csd')
                eqns['CSD'][site] = eqn
                plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend csd'], name='{} CSD'.format(site))]
            if 'LOWESS' in deg_mode:
                df = deg.lowess(df)
                _, eqn = deg.trendline(df, column='Power(W) norm trend lowess')
                eqns['LOWESS'][site] = eqn
                plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend lowess'], name='{} LOWESS'.format(site))]
            if 'YOY' in deg_mode:
                ratios, rate = deg.yoy(df)
                eqns['YOY'][site] = rate
                yoy_plots += [go.Histogram(x=ratios, name=site, histnorm='percent')]

        big_plot = dcc.Graph(id='degradation-big_graph', figure={'data': plots, 'layout': layout})
        yoys = dcc.Graph(id='degradation-yoys', figure={'data': yoy_plots, 'layout': yoy_layout})
        if any(len(eqns[i]) > 0 for i in eqns):
            # boxplots by degradation type
            boxes = []
            boxes_layout = go.Layout(yaxis={'title': 'Degradation (Wh/W/year)'}, xaxis={'title': 'Calculation method'})
            for method in eqns:
                boxes += [go.Box(y=list(eqns[method].values()), name=method)]
            box = dcc.Graph(id='degradation-hist', figure={'data': boxes, 'layout': boxes_layout})

            # scatterplots by sites
            scatters = []
            scatters_layout = go.Layout(yaxis={'title': 'Degradation (Wh/W/year)'}, xaxis={'title': 'Site'})
            for method in eqns:
                tmp = []
                for site in sorted(eqns[method]):
                    tmp.append(eqns[method][site])
                scatters.append(
                    go.Scatter(x=['[{}]'.format(i) for i in sorted(site_ids)], y=tmp, name=method, mode='markers'))
            scatters = dcc.Graph(id='degradation-scatters', figure={'data': scatters, 'layout': scatters_layout})

            # YOY gets special histogram
            if 'YOY' in deg_mode:
                final = html.Div([
                    html.Div([html.H3('Trend over time', style={'textAlign': 'center'}), big_plot]),
                    html.Div([
                        html.Div([html.H3('YOY degradation', style={'textAlign': 'center'}), yoys],
                                 className='four columns'),
                        html.Div([html.H3('Degradation by calculation method', style={'textAlign': 'center'}), box],
                                 className='four columns'),
                        html.Div([html.H3('Degradation by site', style={'textAlign': 'center'}), scatters],
                                 className='four columns'),
                    ], className='row'),
                ])
            else:
                final = html.Div([
                    html.Div([html.H3('Trend over time', style={'textAlign': 'center'}), big_plot]),
                    html.Div([
                        html.Div([html.H3('Degradation by calculation method', style={'textAlign': 'center'}), box],
                                 className='six columns'),
                        html.Div([html.H3('Degradation by site', style={'textAlign': 'center'}), scatters],
                                 className='six columns')
                    ], className='row'),
                ])
            return final
        else:
            return html.Div([big_plot])

    @app.callback(
        Output('degradation-run_button', 'n_clicks'),
        [Input('degradation-metadata_table', 'selected_row_indices'),
         Input('degradation-insol_low', 'value'),
         Input('degradation-insol_hi', 'value'),
         Input('degradation-prod_low', 'value'),
         Input('degradation-prod_hi', 'value'),
         Input('degradation-deg_modes', 'value')],
        [State('degradation-run_button', 'n_clicks')]
    )
    def reset_run_button(points, insol_low, insol_hi, prod_low, prod_hi, deg_modes, prev_clicks):
        return 0
