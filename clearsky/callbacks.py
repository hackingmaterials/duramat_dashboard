

import pvlib
import base64
import io
import datetime

import plotly.graph_objs as go
import plotly.tools as tls
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

from clearsky import utils
from clearsky.clearsky_detection import utils as cs_utils

from sklearn import metrics
import pandas as pd


def add_callbacks(app):
    # @app.callback(
    #     Output('cs-hidden', 'children'),
    #     [Input('cs-file_upload', 'contents'),
    #      Input('cs-file_upload', 'filename'),
    #      Input('cs-date_picker_start', 'value'),
    #      Input('cs-date_picker_end', 'value'),
    #      Input('cs-freq', 'value'),
    #      Input('cs-window_length_slider', 'value'),
    #      Input('cs-mean_diff_slider', 'value'),
    #      Input('cs-max_diff_slider', 'value'),
    #      Input('cs-upper_ll_slider', 'value'),
    #      Input('cs-lower_ll_slider', 'value'),
    #      Input('cs-vardiff_slider', 'value'),
    #      Input('cs-slopedev_slider', 'value')],
    #     [State('cs-hidden', 'children')]
    # )
    # def update_table(contents, filename, start_date, end_date, freq, window_length, mean_diff, max_diff,
    #                  upper_ll, lower_ll, vardiff, slopedev, prev_params):
    #     window_length = int(window_length)
    #     mean_diff = float(mean_diff)
    #     max_diff = float(max_diff)
    #     upper_ll = float(upper_ll)
    #     lower_ll = float(lower_ll)
    #     vardiff = float(vardiff)
    #     slopedev = float(slopedev)
    #
    #     new_params = {'Window length': window_length,
    #                   'Mean difference': mean_diff,
    #                   'Max difference': max_diff,
    #                   'Upper line length': upper_ll,
    #                   'Lower line length': lower_ll,
    #                   'Variance of slopes': vardiff,
    #                   'Max difference of slopes': slopedev,}
    #
    #     try:
    #         prev_runs = pd.read_json(prev_params)
    #     except:
    #         prev_runs = pd.DataFrame()
    #
    #     new_params['Run'] = len(prev_runs) + 1
    #     prev_runs = pd.concat([prev_runs, pd.DataFrame([new_params])], ignore_index=True)
    #
    #     return prev_runs.to_json()

    @app.callback(
        Output('cs-output', 'children'),
        [Input('cs-run', 'n_clicks')],
        [State('cs-file_upload', 'contents'),
         State('cs-file_upload', 'filename'),
         State('cs-date_picker_start', 'value'),
         State('cs-date_picker_end', 'value'),
         State('cs-freq', 'value'),
         State('cs-window_length_slider', 'value'),
         State('cs-mean_diff_slider', 'value'),
         State('cs-max_diff_slider', 'value'),
         State('cs-upper_ll_slider', 'value'),
         State('cs-lower_ll_slider', 'value'),
         State('cs-vardiff_slider', 'value'),
         State('cs-slopedev_slider', 'value')]
    )
    def update_plot(click, contents, filename, start_date, end_date, freq, window_length, mean_diff,
                    max_diff, upper_ll, lower_ll, vardiff, slopedev):
        """Redraw plot with updated parameters.

        Args:
            click: button clicked
            contents: file contents (see dash tutorial on file uploading)
            filename: file name (see dash dutorial on file uploading)
            start_date: Beginning date
            end_date:  Ending date
            freq: data frequency (in minute)
            window_length: window size (in minute) for PVLIB algorithm
            mean_diff: cutoff for mean diff (see PVLIB)
            max_diff: cutoff for max diff (see PVLIB)
            upper_ll: cutoff for upper line length (see PVLIB)
            lower_ll: cutoff for lower line length (see PVLIB)
            vardiff: cutoff for vardiff (see PVLIB)
            slopedev: cutoff for slopedev (see PVLIB)

        Returns:
            plot of clear periods and feature values (needs to be beautified)
        """
        if click < 1:
            return

        # params = pd.read_json(params)
        # params = params.apply(pd.to_numeric)
        # params = params.sort_values('Run')

        window_length = int(window_length)
        mean_diff = float(mean_diff)
        max_diff = float(max_diff)
        upper_ll = float(upper_ll)
        lower_ll = float(lower_ll)
        slopedev = float(slopedev)
        vardiff = float(vardiff)


        df = utils.read_df(contents, filename)
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        df = df[df.index.minute % freq == 0]
        is_clear, components, alpha = \
            cs_utils.detect_clearsky(df['GHI'], df['GHIcs'], df.index,
                                     window_length=window_length, mean_diff=mean_diff,
                                     max_diff=max_diff, upper_line_length=upper_ll, lower_line_length=lower_ll,
                                     slope_dev=slopedev, var_diff=vardiff, return_components=True)

        df['GHIcs'] = df['GHIcs'] * alpha
        fig = tls.make_subplots(rows=2, cols=1, shared_xaxes=True)

        plots = []
        plots.append(go.Scatter(x=df.index, y=df['GHI'], name='GHI'))
        plots.append(go.Scatter(x=df.index, y=df['GHIcs'], name='GHIcs'))
        plots.append(go.Scatter(x=df[is_clear].index, y=df[is_clear]['GHI'], name='PVLib clear', mode='markers'))
        plots.append(go.Scatter(x=df.index, y=components['mean_diff'],
                                name='Mean diff.', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['max_diff'],
                                name='Max diff.', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['line_length'],
                                name='Line length', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['slope_nstd'],
                                name='Slope std. dev.', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['slope_max'],
                                name='Max slope diff.', visible='legendonly'))

        for p in plots:
            fig.append_trace(p, 1, 1)

        plots2 = []
        passes = pd.DataFrame(components)
        for i, test in enumerate(['mean_diff_pass', 'max_diff_pass', 'line_length_pass',
                                  'slope_nstd_pass', 'slope_max_pass']):
            slice = passes[test].astype(int)
            ii = i / 4
            yval = [ii] * len(slice.astype(bool) & passes['non_zero'].astype(bool))
            plots2.append(
                go.Scatter(x=df.index[:len(slice)][slice.astype(bool) & passes['non_zero'].astype(bool)],
                           y=yval, name='', mode='markers', showlegend=False)
            )

        for p in plots2:
            fig.append_trace(p, 2, 1)

        fig['layout']['yaxis2'].update(tickmode='text', tickvals=[0, .25, .5, .75, 1],
                                       ticktext=['Mean diff.', 'Max diff.', 'Line length',
                                                 'Slope std. dev.', 'Max slope diff.'])
        fig['layout']['xaxis2'].update(title='Date')
        fig['layout']['yaxis2'].update(domain=[0, 0.2])
        fig['layout']['yaxis1'].update(title='GHI / W/m2')
        fig['layout']['yaxis1'].update(domain=[.25, 1])
        fig['layout'].update(height=500, margin={'l': 100})
        fig['layout'].update(title='Window length: {}, mean diff: {}, max diff: {}, upper line length: {}, '
                                   'lower line length: {}, max slope difference: {}, std slope differece: {}'
                                   .format(window_length, mean_diff, max_diff, upper_ll, lower_ll, slopedev, vardiff))

        plots = fig

        layout = go.Layout(xaxis={'title': 'Date'}, # yaxis={'title': 'W/m2'},
                           title='Window length: {}, mean diff: {}, max diff: {}, upper line length: {}, '
                                 'lower line length: {}, max slope difference: {}, std slope differece: {}'
                                  .format(window_length, mean_diff, max_diff, upper_ll, lower_ll, slopedev, vardiff),
                           )
        ts_plot = dcc.Graph(id='cs-plot', figure={'data': plots, 'layout': layout})

        # scores = [go.Scatter(x=list(range(len(params))),
        #                      y=params['F-score'],
        #                      text=utils.df_to_text(params), hoverinfo='text')]
        # scores_layout = go.Layout(xaxis={'title': 'Run', 'tickvals': [i for i in range(1, len(params))],
        #                                  'ticktext': [str(i + 1) for i in range(1, len(params))],
        #                                  'range': [0, len(params)]}, yaxis={'title': 'F-score'})
        # scores_plot = dcc.Graph(id='cs-scores', figure={'data': scores, 'layout': scores_layout})
        #
        # table = dt.DataTable(
        #     rows=params[['Run', 'Window length', 'Mean difference', 'Max difference',
        #                  'Upper line length', 'Lower line length', 'Variance of slopes',
        #                  'Max difference of slopes', 'F-score']].round(3).to_dict('records'),
        #     columns=['Run', 'Window length', 'Mean difference', 'Max difference',
        #              'Upper line length', 'Lower line length', 'Variance of slopes',
        #              'Max difference of slopes', 'F-score'],
        #     selected_row_indices=[],
        #     sortable=True,
        #     filterable=True,
        #     editable=False,
        #     id='cs-param_table'
        # )

        final = html.Div([
            html.Div(ts_plot)
        ], style={'width': '98%', 'float': 'center', 'pad': {'l': 40}})

        return final

    # @app.callback(
    #     Output('cs-output', 'children'),
    #     [Input('cs-site', 'value'),
    #      Input('cs-date_picker', 'start_date'),
    #      Input('cs-date_picker', 'end_date'),
    #      Input('cs-window_length_slider', 'value'),
    #      Input('cs-mean_diff_slider', 'value'),
    #      Input('cs-max_diff_slider', 'value'),
    #      Input('cs-upper_ll_slider', 'value'),
    #      Input('cs-lower_ll_slider', 'value'),
    #      Input('cs-vardiff_slider', 'value'),
    #      Input('cs-slopedev_slider', 'value')]
    # )
    # def update_plot(site, start_date, end_date, window_length, mean_diff, max_diff,
    #                 upper_ll, lower_ll, vardiff, slopedev):
    #     SCORES = []
    #     ground_master, mask = utils.read_df(site)
    #     df = ground_master.df
    #     is_clear = \
    #         pvlib.clearsky.detect_clearsky(df['GHI'], df['Clearsky GHI pvlib'], df.index,
    #                                        window_length=window_length, mean_diff=mean_diff,
    #                                        max_diff=max_diff, upper_line_length=upper_ll, lower_line_length=lower_ll,
    #                                        slope_dev=slopedev, var_diff=vardiff)
    #     score = metrics.fbeta_score(ground_master.df[mask]['sky_status'], is_clear[mask], beta=.5)
    #     print('score: ', score)
    #     plots = []
    #     plots.append(go.Scatter(x=df.index, y=df['GHI'], name='GHI'))
    #     plots.append(go.Scatter(x=df.index, y=df['GHI nsrdb'].interpolate(), name='GHI(NSRDB)'))
    #     plots.append(go.Scatter(x=df.index, y=df['Clearsky GHI pvlib'], name='GHI(CS)'))
    #     plots.append(go.Scatter(x=df[is_clear].index, y=df[is_clear]['GHI'], name='PVLib clear', mode='markers'))
    #     plots.append(go.Scatter(x=df[mask & df['sky_status'].astype(bool)].index,
    #                             y=df[mask & df['sky_status'].astype(bool)]['GHI'],
    #                             name='NSRDB clear', mode='markers',
    #                             marker={'symbol': 'circle-open', 'line': {'width': 3}, 'size': 10}))
    #     layout = go.Layout(xaxis={'title': 'Date'}, yaxis={'title': 'W/m2'},
    #                        title='Window length: {}, mean diff: {}, max diff: {}, upper line length: {}, '
    #                              'lower line length: {}, max slope difference: {}, std slope differece: {}'
    #                        .format(window_length, mean_diff, max_diff, upper_ll, lower_ll, slopedev, vardiff))
    #     SCORES.append({'window length': window_length, 'mean diff': mean_diff, 'max diff': max_diff,
    #                    'upper line length': upper_ll, 'lower line length': lower_ll,
    #                    'std slope': vardiff, 'max slope diff': slopedev, 'F-score': score})
    #     ts_plot = dcc.Graph(id='cs-plot', figure={'data': plots, 'layout': layout})
    #     scores = [go.Scatter(x=list(range(len(SCORES))),
    #                          y=[i['F-score'] for i in SCORES],
    #                          text=[utils.dict_to_text(i) for i in SCORES], hoverinfo='text')]
    #     scores_layout = go.Layout(xaxis={'title': 'Run', 'tickvals': [i for i in range(1, len(SCORES))],
    #                                      'ticktext': [str(i + 1) for i in range(1, len(SCORES))],
    #                                      'range': [0, len(SCORES)]}, yaxis={'title': 'F-score'}, title='Previous runs')
    #     scores_plot = dcc.Graph(id='cs-scores', figure={'data': scores, 'layout': scores_layout})
    #     final = html.Div([
    #         html.Div([html.H3('Time series visual'), ts_plot], className='six columns'),
    #         html.Div([html.H3('Past runs'), scores_plot], className='six columns')
    #     ])
    #     final = [html.Div(ts_plot),
    #              html.Div(scores_plot)]

    #     return final

    # @app.callback(
    #     Output('cs-freq', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_freq(click):
    #     return 30
    #
    # @app.callback(
    #     Output('cs-window_length_slider', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_window_length(click):
    #     return 90
    #
    # @app.callback(
    #     Output('cs-mean_diff_slider', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_mean_diff(click):
    #     return 75
    #
    # @app.callback(
    #     Output('cs-max_diff_slider', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_max_diff(click):
    #     return 75
    #
    # @app.callback(
    #     Output('cs-upper_ll_slider', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_upper_ll(click):
    #     return 10
    #
    # @app.callback(
    #     Output('cs-lower_ll_slider', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_lower_ll(click):
    #     return -5
    #
    # @app.callback(
    #     Output('cs-vardiff_slider', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_vardiff(click):
    #     return 0.005
    #
    # @app.callback(
    #     Output('cs-slopedev_slider', 'value'),
    #     [Input('cs-reset', 'n_clicks')]
    # )
    # def reset_slopedev(click):
    #     return 8

    @app.callback(
        Output('cs-date_picker_start', 'value'),
        [Input('cs-file_upload', 'contents'),
         Input('cs-file_upload', 'contents')]
    )
    def set_start_date(contents, filename):
        df = utils.read_df(contents, filename)
        return df.index[0].date()

    @app.callback(
        Output('cs-date_picker_end', 'value'),
        [Input('cs-file_upload', 'contents'),
         Input('cs-file_upload', 'filename')]
    )
    def set_end_date(contents, filename):
        df = utils.read_df(contents, filename)
        return (df.index[0] + datetime.timedelta(days=7)).date()
