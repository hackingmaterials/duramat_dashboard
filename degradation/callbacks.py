

import plotly.graph_objs as go
from plotly import tools
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
from scipy.stats import norm
import numpy as np

from . import degradation_functions as deg

import pandas as pd


def add_callbacks(app, db_handler):
    """Bind callbacks to app.

    Args:
        app (Dash.app): web application object
        db_handler (DBHander): object to perform db queries

    Returns:
        None
    """
    metadata = db_handler.get_system_metadata()

    @app.callback(
        Output('degradation-selected', 'style'),
        [Input('degradation-metadata_table', 'selected_row_indices')]
    )
    def make_deg_mode_dropdown(points):
        """Create dropdown menu of degradation rate calculation methods.

        Args:
            points (list): system_id values (if not empty, menu will show).

        Returns:
            Makes dropdown menu visible.
        """
        site_ids = [metadata.iloc[i]['ID'] for i in points]

        if site_ids:
            style = {'visibility': 'visible'}
        else:
            style = {'visibility': 'hidden'}

        return style

    @app.callback(
        Output('degradation-deg_modes_master', 'style'),
        [Input('degradation-metadata_table', 'selected_row_indices'),
         Input('degradation-selected', 'children')]
    )
    def make_deg_mode_dropdown(points, dummy_fig):
        """Create dropdown menu of degradation rate calculation methods.

        Args:
            points (list): system_id values
            dummy_fig (children): figure that has no effect on functionality - included here to force a dependency
                                  that makes loading 'prettier'

        Returns:
            Makes dropdown menu visible.
        """
        site_ids = [metadata.iloc[i]['ID'] for i in points]

        if site_ids:
            style = {'visibility': 'visible'}
        else:
            style = {'visibility': 'hidden'}

        return style

    @app.callback(
        Output('degradation-metadata_table', 'selected_row_indices'),
        [Input('degradation-map', 'clickData')],
        [State('datatable-gapminder', 'selected_row_indices')])
    def update_selected_row_indices(clickData, selected_row_indices):
        """Add clicked sites to charts.

        Args:
            clickData (list): clicked sites
            selected_row_indices (list): selected sites

        Returns:
            selected row indices
        """
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

    @app.callback(Output('degradation-selected_graph', 'figure'),
                  [Input('degradation-metadata_table', 'rows'),
                   Input('degradation-metadata_table', 'selected_row_indices'),
                   Input('degradation-data_smoother', 'value')])
    def make_individual_figure(rows, selected_row_indices, smoother):
        """Plot all clicked points.

        Args:
            rows (pd.DataFrame): metadata table
            selected_row_indices (list): selected sites
            smoother (str): which smoothing method for plot

        Returns:
            html.Div object that is empty (if no points clicked) or displays a plot of all sites.
        """
        site_ids = [rows[i]['ID'] for i in selected_row_indices]

        if not site_ids:
            return html.Div(style={'display': 'none'})

        dfdict = db_handler.get_system_data(site_ids, allow_add=True)

        vals = {}
        for system_id, df in dfdict.items():
            try:
                if smoother == 'rolling':
                    df = deg.rolling_mean(df)
                    # col = 'Power(W) norm trend rolling mean'
                elif smoother == 'csd':
                    df = deg.csd(df)
                    # col = 'Power(W) norm trend csd'
                else:
                    pass
                tmp = df.resample('W').median()
                tmp.index = tmp.index.map(lambda x: x.date())
                vals[system_id] = tmp
            except:
                print(system_id)

        df2 = pd.DataFrame.from_dict(vals, orient='index')
        df2 = df2.T
        df2 = df2.sort_index()

        hovertext = []
        for yi, yy in enumerate(df2.keys()):
            hovertext.append([])
            for xi, xx in enumerate(df2.index):
                text = 'System ID: {}<br />Date: {}<br />Performance: {:.3f}'.format(yy, xx, df2.values[xi, yi])
                hovertext[-1].append(text)

        plots = [go.Heatmap(x=df2.index, y=['[{}]'.format(i) for i in df2.keys()], z=df2.values.T,
                            colorbar={'title': 'Normalized Performance', 'titleside': 'right'},
                            hoverinfo='text', text=hovertext, colorscale='Reds')]
        layout = go.Layout(xaxis={'title': 'Date', 'showgrid': False}, yaxis={'title': 'System ID', 'showgrid': False},
                           title='Performance of {} selected sites'.format(len(vals)))

        if plots:
            figure = {'data': plots,
                      'layout': layout}
        else:
            figure = {}

        return figure

    @app.callback(Output('degradation-deg_modes_histogram', 'figure'),
                  [Input('degradation-metadata_table', 'rows'),
                   Input('degradation-metadata_table', 'selected_row_indices')])
    def make_deg_modes_hist(rows, selected_row_indices):
        """Make plot showing distribution of degradation rates and methods.

        Args:
            rows (dict): metadata table
            selected_row_indices (list): selected sites

        Returns
            plot that shows distribution of degradation rates
        """
        site_ids = [rows[i]['ID'] for i in selected_row_indices]

        tmp_meta = metadata.where(metadata['ID'].isin(site_ids)).dropna(how='any')

        traces = []
        names = []
        for val, name in zip(['ols_rd', 'csd_rd', 'yoy_rd'], ['OLS', 'CSD', 'YOY']):
            traces.append(go.Histogram(x=tmp_meta[val], name=name))
            # traces.append(tmp_meta[val].values)
            # names.append(name)

        layout = go.Layout(title='Population degradation rates',
                           xaxis={'title': 'Degradation rate (%/year)'}, yaxis={'title': 'System count'})

        # fig = ff.create_distplot(traces, names, bin_size=.2)
        # return fig
        return {'data': traces, 'layout': layout}

    @app.callback(Output('degradation-deg_modes_cumhistogram', 'figure'),
                  [Input('degradation-metadata_table', 'rows'),
                   Input('degradation-metadata_table', 'selected_row_indices')])
    def make_deg_modes_cumhist(rows, selected_row_indices):
        """Make plot of cumulative distribution of degradation rates/modes.

        Args:
            rows (dict): metadata table
            selected_row_indices (list): selected sites

        Returns:
            plot of cumulative distributions
        """
        site_ids = [rows[i]['ID'] for i in selected_row_indices]

        tmp_meta = metadata.where(metadata['ID'].isin(site_ids)).dropna(how='any').copy()

        traces = []
        for val, name in zip(['ols_rd', 'csd_rd', 'yoy_rd'], ['OLS', 'CSD', 'YOY']):
            # xvals = sorted(tmp_meta[val].copy())
            # traces.append(go.Scatter(x=xvals, y=norm.cdf(xvals), name=name))
            # traces.append(go.Histogram(x=tmp_meta[val], name=name, cumulative={'enabled': True}, opacity=0))
            # break
            hist, bin_edges = np.histogram(tmp_meta[val], normed=True, bins=500)
            traces.append(go.Scatter(x=bin_edges, y=np.cumsum(hist) * (bin_edges[1] - bin_edges[0]), name=name))

        layout = go.Layout(title='Population degradation rates',
                           xaxis={'title': 'Degradation rate (%/year)'}, yaxis={'title': 'System count'})

        return {'data': traces, 'layout': layout}

    @app.callback(Output('degradation-deg_modes_by_site', 'figure'),
                  [Input('degradation-metadata_table', 'rows'),
                   Input('degradation-metadata_table', 'selected_row_indices')])
    def make_deg_modes_by_site(rows, selected_row_indices):
        """Make plot of degradation modes by site.

        Args:
            rows (dict): metadata table
            selected_row_indices (list): selected sites

        Returns:
            plot of degradatiom odes by site
        """
        site_ids = [rows[i]['ID'] for i in selected_row_indices]

        tmp_meta = metadata.where(metadata['ID'].isin(site_ids)).dropna(how='any').copy()

        traces = []
        for val, name in zip(['ols_rd', 'csd_rd', 'yoy_rd'], ['OLS', 'CSD', 'YOY']):
            traces.append(go.Scatter(x=tmp_meta['ID'].apply(lambda x: '[{}]'.format(int(x))), y=tmp_meta[val],
                                     name=name, mode='markers'))

        layout = go.Layout(title='System degradation rates', yaxis={'title': 'Degradation rate (%/year)'}, xaxis={'title': 'System ID'})

        return {'data': traces, 'layout': layout}

    @app.callback(Output('degradation-meta_figure', 'children'),
                  [Input('degradation-metadata_table', 'rows'),
                   Input('degradation-metadata_table', 'selected_row_indices')])
    def make_deg_meta_figure(rows, selected_row_indices):
        """Plot all clicked points.

        Args:
            rows (dict): metadata table
            selected_row_indices (list): selected sites

        Returns:
            plots of degradation rates and modes broken down by metadata tags (climate, location, system size, age)
        """
        site_ids = [rows[i]['ID'] for i in selected_row_indices]

        tmp_meta = metadata.where(metadata['ID'].isin(site_ids)).dropna(how='any').copy()

        traces = {}
        for meta in ['State', 'Climate']:
            traces[meta] = []
            traces[meta].append(go.Box(x=tmp_meta[meta], y=tmp_meta['ols_rd'], name='OLS'))
            traces[meta].append(go.Box(x=tmp_meta[meta], y=tmp_meta['csd_rd'], name='CSD'))
            traces[meta].append(go.Box(x=tmp_meta[meta], y=tmp_meta['yoy_rd'], name='YOY'))

        for meta in ['Size (W)', 'Active Days']:
            tmp_meta['interval'] = pd.cut(tmp_meta[meta], 10)
            tmp_meta = tmp_meta.sort_values('interval')
            tmp_meta['interval'] = tmp_meta['interval'].astype(str)
            traces[meta] = []
            traces[meta].append(go.Box(x=tmp_meta['interval'], y=tmp_meta['ols_rd'], name='OLS'))
            traces[meta].append(go.Box(x=tmp_meta['interval'], y=tmp_meta['csd_rd'], name='CSD'))
            traces[meta].append(go.Box(x=tmp_meta['interval'], y=tmp_meta['yoy_rd'], name='YOY'))

        layout = go.Layout(boxmode='group')
        layouts = {}
        layouts['State'] = go.Layout(boxmode='group', xaxis={'title': 'State'}, yaxis={'title': 'Degradation rate (%/year)'})
        layouts['Size (W)'] = go.Layout(boxmode='group', xaxis={'title': 'Size (W)'}, yaxis={'title': 'Degradation rate (%/year)'})
        layouts['Climate'] = go.Layout(boxmode='group', xaxis={'title': 'Climate'}, yaxis={'title': 'Degradation rate (%/year)'})
        layouts['Active Days'] = go.Layout(boxmode='group', xaxis={'title': 'Active Days'}, yaxis={'title': 'Degradation rate (%/year)'})

        children1 = [
            html.Div(dcc.Graph(figure={'data': traces[i], 'layout': layouts[i]}, id='degradation-{}_figure'.format(i)), className='six columns')
            for i in ['State', 'Climate']
        ]

        children2 = [
            html.Div(dcc.Graph(figure={'data': traces[i], 'layout': layouts[i]}, id='degradation-{}_figure'.format(i)), className='six columns')
            for i in ['Size (W)', 'Active Days']
        ]

        final = html.Div([
            html.Div(children1, className='row'),
            html.Div(children2, className='row')
        ])
        return final

    # @app.callback(
    #     Output('degradation-deg_plots', 'children'),
    #     [Input('degradation-run_button', 'n_clicks')],
    #     [State('degradation-deg_modes', 'value'),
    #      State('degradation-metadata_table', 'rows'),
    #      State('degradation-metadata_table', 'selected_row_indices'),
    #      State('degradation-insol_low', 'value'),
    #      State('degradation-insol_hi', 'value'),
    #      State('degradation-prod_low', 'value'),
    #      State('degradation-prod_hi', 'value')]
    # )
    # def update_graph(n_clicks, deg_mode, rows, selected_row_indices, insol_low, insol_hi, prod_low, prod_hi):
    #     """Display smoothed trends and degradation rate statistics for 'clicked' sites.
    #
    #     Parameters:
    #     ----------
    #     sites
    #         List of sites to chart.
    #     deg_mode
    #         List of smoothing/degradation modes.
    #     Returns
    #     -------
    #     div
    #         html Div that includes 2 rows of charts  - smoothed/trended systems over time and
    #         summary statistics of the degrdation rates by site and method.
    #     """
    #     # site_ids = [metadata.iloc[i]['ID'] for i in points]
    #     site_ids = [rows[i]['ID'] for i in selected_row_indices]
    #
    #     if not site_ids:
    #         return
    #     if n_clicks == 0:
    #         return
    #
    #     dfdict = db_handler.get_system_data(site_ids, allow_add=True)
    #
    #     for df in dfdict.values():
    #         df['mask'] = (df['poa_global'] >= insol_low) & (df['poa_global'] <= insol_hi) & \
    #                      (df['Power(W) norm'] >= prod_low) & (df['Power(W) norm'] <= prod_hi)
    #
    #     if len(dfdict) == 0 or not deg_mode:
    #         return html.Div(style={'display': 'none'})
    #
    #     layout = go.Layout(yaxis={'title': 'Wh/W'})
    #     yoy_layout = go.Layout(xaxis={'title': 'Degradation (Wh/W/year)'}, yaxis={'title': 'Normalized frequency'})
    #     plots = []
    #     plots_rolling = {}
    #     plots_ols = {}
    #     plots_csd = {}
    #     plots_lowess = {}
    #     yoy_plots = []
    #     eqns = {'OLS': {}, 'CSD': {}, 'Rolling': {}, 'LOWESS': {}, 'YOY': {}, 'ARIMA': {}}
    #
    #     for site in sorted(dfdict):
    #         df = dfdict[site]
    #         if 'Rolling' in deg_mode:
    #             df = deg.rolling_mean(df)
    #             _, eqn = deg.trendline(df, column='Power(W) norm trend rolling mean')
    #             eqns['Rolling'][site] = eqn
    #             plots += \
    #                 [go.Scatter(x=df.index, y=df['Power(W) norm trend rolling mean'], name='{} Rolling'.format(site))]
    #             plots_rolling[site] = df['Power(W) norm trend rolling mean'].rename('Power(W) norm trend').resample('W').median()
    #         if 'OLS' in deg_mode:
    #             df, eqn = deg.trendline(df)
    #             eqns['OLS'][site] = eqn
    #             plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend ols'], name='{} OLS'.format(site))]
    #             plots_ols[site] = df['Power(W) norm trend ols'].rename('Power(W) norm trend').resample('W').median()
    #         if 'CSD' in deg_mode:
    #             df = deg.csd(df)
    #             _, eqn = deg.trendline(df, column='Power(W) norm trend csd')
    #             eqns['CSD'][site] = eqn
    #             plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend csd'], name='{} CSD'.format(site))]
    #             plots_csd[site] = df['Power(W) norm trend csd'].rename('Power(W) norm trend').resample('W').median()
    #         if 'LOWESS' in deg_mode:
    #             df = deg.lowess(df)
    #             _, eqn = deg.trendline(df, column='Power(W) norm trend lowess')
    #             eqns['LOWESS'][site] = eqn
    #             plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend lowess'], name='{} LOWESS'.format(site))]
    #             plots_lowess[site] = df['Power(W) norm trend lowess'].rename('Power(W) norm trend').resample('W').median()
    #         if 'YOY' in deg_mode:
    #             ratios, rate = deg.yoy(df)
    #             eqns['YOY'][site] = rate
    #             yoy_plots += [go.Histogram(x=ratios, name=site, histnorm='percent')]
    #
    #     trend_plots = []
    #     names = []
    #     for p, n in zip([plots_ols, plots_rolling, plots_csd, plots_lowess],
    #                     ['Ordinary Least Squares', 'Rolling Mean', 'Seasonal Decomposition', 'Locally Weighted Scatterplot Smoothing']):
    #         if not p: continue
    #         tmpdf = pd.DataFrame.from_dict(p, orient='index')
    #         tmpdf = tmpdf.T.sort_index()
    #         trend_plots.append(
    #             go.Heatmap(x=tmpdf.index, y=['[{}]'.format(i) for i in tmpdf.keys()], z=tmpdf.values.T,
    #                             colorbar={'title': 'W/Wp', 'titleside': 'right'})
    #         )
    #         names.append(n)
    #         layout = go.Layout(xaxis={'title': 'Date'}, yaxis={'title': 'System ID'})
    #         # return html.Div([dcc.Graph(id='degradation_thing', figure={'data': [trend_plots[0]], 'layout': layout})])
    #
    #     layout_maker = lambda x: go.Layout(xaxis={'title': 'Date'}, yaxis={'title': 'System ID'}, title=x)
    #     class_name_dict = {1: 'twelve columns', 2: 'six columns', 3: 'four columns', 4: 'three columns'}
    #     class_name = class_name_dict[len(names)]
    #     divs = [html.Div(dcc.Graph(id='degradation-' + n,
    #                                figure={'data': [p], 'layout': layout_maker(n)}), className=class_name, style={'margin': {'l': 0, 'r': 0}})
    #             for n, p in zip(names, trend_plots)]
    #     return html.Div(divs, className='row')
        # fig = tools.make_subplots(rows=1, cols=len(names), shared_xaxes=True, shared_yaxes=True, horizontal_spacing=.01)
        # for i, (p, n) in enumerate(zip(trend_plots, names)):
        #     fig.append_trace(p, 1, i + 1)

        # for trace in fig:
        #     print(trace['layout'].update(''))

        # return html.Div([dcc.Graph(id='degradation_trends', figure=fig)])


        # return html.Div([html.Div(i) for i in final_plots])

        # big_plot = dcc.Graph(id='degradation-big_graph', figure={'data': plots, 'layout': layout})
        # yoys = dcc.Graph(id='degradation-yoys', figure={'data': yoy_plots, 'layout': yoy_layout})
        # if any(len(eqns[i]) > 0 for i in eqns):
        #     # boxplots by degradation type
        #     boxes = []
        #     boxes_layout = go.Layout(yaxis={'title': 'Degradation (Wh/W/year)'}, xaxis={'title': 'Calculation method'})
        #     for method in eqns:
        #         boxes += [go.Box(y=list(eqns[method].values()), name=method)]
        #     box = dcc.Graph(id='degradation-hist', figure={'data': boxes, 'layout': boxes_layout})
        #
        #     # scatterplots by sites
        #     scatters = []
        #     scatters_layout = go.Layout(yaxis={'title': 'Degradation (Wh/W/year)'}, xaxis={'title': 'Site'})
        #     for method in eqns:
        #         tmp = []
        #         for site in sorted(eqns[method]):
        #             tmp.append(eqns[method][site])
        #         scatters.append(
        #             go.Scatter(x=['[{}]'.format(i) for i in sorted(site_ids)], y=tmp, name=method, mode='markers'))
        #     scatters = dcc.Graph(id='degradation-scatters', figure={'data': scatters, 'layout': scatters_layout})
        #
        #     # YOY gets special histogram
        #     if 'YOY' in deg_mode:
        #         final = html.Div([
        #             html.Div([html.H3('Trend over time', style={'textAlign': 'center'}), big_plot]),
        #             html.Div([
        #                 html.Div([html.H3('YOY degradation', style={'textAlign': 'center'}), yoys],
        #                          className='four columns'),
        #                 html.Div([html.H3('Degradation by calculation method', style={'textAlign': 'center'}), box],
        #                          className='four columns'),
        #                 html.Div([html.H3('Degradation by site', style={'textAlign': 'center'}), scatters],
        #                          className='four columns'),
        #             ], className='row'),
        #         ])
        #     else:
        #         final = html.Div([
        #             html.Div([html.H3('Trend over time', style={'textAlign': 'center'}), big_plot]),
        #             html.Div([
        #                 html.Div([html.H3('Degradation by calculation method', style={'textAlign': 'center'}), box],
        #                          className='six columns'),
        #                 html.Div([html.H3('Degradation by site', style={'textAlign': 'center'}), scatters],
        #                          className='six columns')
        #             ], className='row'),
        #         ])
        #     return final
        # else:
        #     return html.Div([big_plot])

    # @app.callback(
    #     Output('degradation-deg_plots', 'children'),
    #     [Input('degradation-run_button', 'n_clicks')],
    #     [State('degradation-deg_modes', 'value'),
    #      State('degradation-metadata_table', 'rows'),
    #      State('degradation-metadata_table', 'selected_row_indices'),
    #      State('degradation-insol_low', 'value'),
    #      State('degradation-insol_hi', 'value'),
    #      State('degradation-prod_low', 'value'),
    #      State('degradation-prod_hi', 'value')]
    # )
    # def update_graph(n_clicks, deg_mode, rows, selected_row_indices, insol_low, insol_hi, prod_low, prod_hi):
    #     """Display smoothed trends and degradation rate statistics for 'clicked' sites.
    #
    #     Parameters:
    #     ----------
    #     sites
    #         List of sites to chart.
    #     deg_mode
    #         List of smoothing/degradation modes.
    #     Returns
    #     -------
    #     div
    #         html Div that includes 2 rows of charts  - smoothed/trended systems over time and
    #         summary statistics of the degrdation rates by site and method.
    #     """
    #     # site_ids = [metadata.iloc[i]['ID'] for i in points]
    #     site_ids = [rows[i]['ID'] for i in selected_row_indices]
    #
    #     if not site_ids:
    #         return
    #     if n_clicks == 0:
    #         return
    #
    #     dfdict = db_handler.get_system_data(site_ids, allow_add=True)
    #
    #     for df in dfdict.values():
    #         df['mask'] = (df['poa_global'] >= insol_low) & (df['poa_global'] <= insol_hi) & \
    #                      (df['Power(W) norm'] >= prod_low) & (df['Power(W) norm'] <= prod_hi)
    #
    #     if len(dfdict) == 0 or not deg_mode:
    #         return html.Div(style={'display': 'none'})
    #
    #     layout = go.Layout(yaxis={'title': 'Wh/W'})
    #     yoy_layout = go.Layout(xaxis={'title': 'Degradation (Wh/W/year)'}, yaxis={'title': 'Normalized frequency'})
    #     plots = []
    #     plots_rolling = {}
    #     plots_ols = {}
    #     plots_csd = {}
    #     plots_lowess = {}
    #     yoy_plots = []
    #     eqns = {'OLS': {}, 'CSD': {}, 'Rolling': {}, 'LOWESS': {}, 'YOY': {}, 'ARIMA': {}}
    #
    #     for site in sorted(dfdict):
    #         df = dfdict[site]
    #         if 'Rolling' in deg_mode:
    #             df = deg.rolling_mean(df)
    #             _, eqn = deg.trendline(df, column='Power(W) norm trend rolling mean')
    #             eqns['Rolling'][site] = eqn
    #             plots += \
    #                 [go.Scatter(x=df.index, y=df['Power(W) norm trend rolling mean'], name='{} Rolling'.format(site))]
    #             plots_rolling[site] = df['Power(W) norm trend rolling mean']
    #         if 'OLS' in deg_mode:
    #             df, eqn = deg.trendline(df)
    #             eqns['OLS'][site] = eqn
    #             plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend ols'], name='{} OLS'.format(site))]
    #             plots_ols[site] = df['Power(W) norm trend ols']
    #         if 'CSD' in deg_mode:
    #             df = deg.csd(df)
    #             _, eqn = deg.trendline(df, column='Power(W) norm trend csd')
    #             eqns['CSD'][site] = eqn
    #             plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend csd'], name='{} CSD'.format(site))]
    #             plots_csd[site] = df['Power(W) norm trend csd']
    #         if 'LOWESS' in deg_mode:
    #             df = deg.lowess(df)
    #             _, eqn = deg.trendline(df, column='Power(W) norm trend lowess')
    #             eqns['LOWESS'][site] = eqn
    #             plots += [go.Scatter(x=df.index, y=df['Power(W) norm trend lowess'], name='{} LOWESS'.format(site))]
    #             plots_lowess[site] = df['Power(W) norm trend lowess']
    #         if 'YOY' in deg_mode:
    #             ratios, rate = deg.yoy(df)
    #             eqns['YOY'][site] = rate
    #             yoy_plots += [go.Histogram(x=ratios, name=site, histnorm='percent')]
    #
    #     big_plot = dcc.Graph(id='degradation-big_graph', figure={'data': plots, 'layout': layout})
    #     yoys = dcc.Graph(id='degradation-yoys', figure={'data': yoy_plots, 'layout': yoy_layout})
    #     if any(len(eqns[i]) > 0 for i in eqns):
    #         # boxplots by degradation type
    #         boxes = []
    #         boxes_layout = go.Layout(yaxis={'title': 'Degradation (Wh/W/year)'}, xaxis={'title': 'Calculation method'})
    #         for method in eqns:
    #             boxes += [go.Box(y=list(eqns[method].values()), name=method)]
    #         box = dcc.Graph(id='degradation-hist', figure={'data': boxes, 'layout': boxes_layout})
    #
    #         # scatterplots by sites
    #         scatters = []
    #         scatters_layout = go.Layout(yaxis={'title': 'Degradation (Wh/W/year)'}, xaxis={'title': 'Site'})
    #         for method in eqns:
    #             tmp = []
    #             for site in sorted(eqns[method]):
    #                 tmp.append(eqns[method][site])
    #             scatters.append(
    #                 go.Scatter(x=['[{}]'.format(i) for i in sorted(site_ids)], y=tmp, name=method, mode='markers'))
    #         scatters = dcc.Graph(id='degradation-scatters', figure={'data': scatters, 'layout': scatters_layout})
    #
    #         # YOY gets special histogram
    #         if 'YOY' in deg_mode:
    #             final = html.Div([
    #                 html.Div([html.H3('Trend over time', style={'textAlign': 'center'}), big_plot]),
    #                 html.Div([
    #                     html.Div([html.H3('YOY degradation', style={'textAlign': 'center'}), yoys],
    #                              className='four columns'),
    #                     html.Div([html.H3('Degradation by calculation method', style={'textAlign': 'center'}), box],
    #                              className='four columns'),
    #                     html.Div([html.H3('Degradation by site', style={'textAlign': 'center'}), scatters],
    #                              className='four columns'),
    #                 ], className='row'),
    #             ])
    #         else:
    #             final = html.Div([
    #                 html.Div([html.H3('Trend over time', style={'textAlign': 'center'}), big_plot]),
    #                 html.Div([
    #                     html.Div([html.H3('Degradation by calculation method', style={'textAlign': 'center'}), box],
    #                              className='six columns'),
    #                     html.Div([html.H3('Degradation by site', style={'textAlign': 'center'}), scatters],
    #                              className='six columns')
    #                 ], className='row'),
    #             ])
    #         return final
    #     else:
    #         return html.Div([big_plot])
