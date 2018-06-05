

import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

from . import degradation_functions as deg

import pandas as pd


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
        [Input('degradation-map', 'clickData')],
        [State('datatable-gapminder', 'selected_row_indices')])
    def update_selected_row_indices(clickData, selected_row_indices):
        if clickData:
            for point in clickData['points']:
                if point['pointNumber'] in selected_row_indices:
                    selected_row_indices.remove(point['pointNumber'])
                else:
                    selected_row_indices.append(point['pointNumber'])
        return selected_row_indices

    # @app.callback(Output('degradation-selected', 'children'),
    #               [Input('degradation-metadata_table', 'rows'),
    #                Input('degradation-metadata_table', 'selected_row_indices')])
    # def make_individual_figure(rows, selected_row_indices):
    #     """Plot all clicked points.

    #     Parameters
    #     ----------
    #     points
    #         List of clicked points

    #     Returns
    #     -------
    #     div
    #         html.Div object that is empty (if no points clicked) or displays a plot of all sites.
    #     """
    #     site_ids = [rows[i]['ID'] for i in selected_row_indices]
    #     # site_ids = [metadata.iloc[i]['ID'] for i in selected_row_indices]

    #     if not site_ids:
    #         return html.Div(style={'display': 'none'})

    #     plots = []
    #     systems_loc = db_handler.get_system_data(site_ids, allow_add=True)
    #     for idx in site_ids:
    #         df = systems_loc[idx]
    #         plots.append(go.Scatter(x=df.index, y=df['Power(W) norm'], name=idx))

    #     if plots:
    #         figure = {'data': plots,
    #                   'layout': go.Layout(showlegend=True, autosize=True, height=500,
    #                                       # margin={'r': 20, 't': 40, 'b': 20, 'l': 60, 'pad': 0},
    #                                       yaxis={'title': 'Wh/W'})}
    #         div = html.Div([
    #             html.H3('Selected Sites', style={'textAlign': 'center', 'margin': {'t': 10}}),
    #             dcc.Graph(id='degradation-selected_graph', figure=figure),
    #         ])
    #     else:
    #         div = html.Div(style={'display': 'none'})
    #
    #     return div

    @app.callback(Output('degradation-selected', 'children'),
                  [Input('degradation-metadata_table', 'rows'),
                   Input('degradation-metadata_table', 'selected_row_indices')])
    def make_individual_figure(rows, selected_row_indices):
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
        site_ids = [rows[i]['ID'] for i in selected_row_indices]
        # site_ids = [metadata.iloc[i]['ID'] for i in selected_row_indices]

        if not site_ids:
            return html.Div(style={'display': 'none'})

        plots = []
        systems_loc = db_handler.get_system_data(site_ids, allow_add=True)
        vals = {}
        for idx in site_ids:
            ts = systems_loc[idx]
            ts = ts[ts['Power(W) norm'] > 0]
            ts = ts.resample('W').median()
            ts.index = [i.date() for i in ts.index]
            vals[idx] = ts['Power(W) norm']

        df2 = pd.DataFrame.from_dict(vals, orient='index')
        df2 = df2.T
        df2 = df2.sort_index()

        plots = [go.Heatmap(x=df2.index, y=['[{}]'.format(i) for i in df2.keys()], z=df2.values.T,
                            colorbar={'title': 'W/Wp', 'titleside': 'right'})]
        layout = go.Layout(xaxis={'title': 'Date'}, yaxis={'title': 'System ID'})

        if plots:
            figure = {'data': plots,
                      'layout': layout}
            div = html.Div([
                html.H3('Selected Sites', style={'textAlign': 'center', 'margin': {'t': 10}}),
                dcc.Graph(id='degradation-selected_graph', figure=figure),
            ])
        else:
            div = html.Div(style={'display': 'none'})

        return div

    @app.callback(
        Output('degradation-deg_plots', 'children'),
        [Input('degradation-run_button', 'n_clicks')],
        [State('degradation-deg_modes', 'value'),
         State('degradation-metadata_table', 'rows'),
         State('degradation-metadata_table', 'selected_row_indices'),
         State('degradation-insol_low', 'value'),
         State('degradation-insol_hi', 'value'),
         State('degradation-prod_low', 'value'),
         State('degradation-prod_hi', 'value')]
    )
    def update_graph(n_clicks, deg_mode, rows, selected_row_indices, insol_low, insol_hi, prod_low, prod_hi):
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
        # site_ids = [metadata.iloc[i]['ID'] for i in points]
        site_ids = [rows[i]['ID'] for i in selected_row_indices]

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

    # @app.callback(
    #     Output('degradation-run_button', 'n_clicks'),
    #     [Input('degradation-metadata_table', 'selected_row_indices'),
    #      Input('degradation-insol_low', 'value'),
    #      Input('degradation-insol_hi', 'value'),
    #      Input('degradation-prod_low', 'value'),
    #      Input('degradation-prod_hi', 'value'),
    #      Input('degradation-deg_modes', 'value')],
    #     [State('degradation-run_button', 'n_clicks')]
    # )
    # def reset_run_button(points, insol_low, insol_hi, prod_low, prod_hi, deg_modes, prev_clicks):
    #     return 0
