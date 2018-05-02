

import pvlib

import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

from clearsky import utils
from clearsky.clearsky_detection import utils as cs_utils

from sklearn import metrics
import pandas as pd

# all_params = []

def add_callbacks(app):
    @app.callback(
        Output('cs-hidden', 'children'),
        [Input('cs-site', 'value'),
         Input('cs-date_picker_start', 'value'),
         Input('cs-date_picker_end', 'value'),
         Input('cs-freq', 'value'),
         Input('cs-window_length_slider', 'value'),
         Input('cs-mean_diff_slider', 'value'),
         Input('cs-max_diff_slider', 'value'),
         Input('cs-upper_ll_slider', 'value'),
         Input('cs-lower_ll_slider', 'value'),
         Input('cs-vardiff_slider', 'value'),
         Input('cs-slopedev_slider', 'value')],
        [State('cs-hidden', 'children')]
    )
    def update_table(site, start_date, end_date, freq, window_length, mean_diff, max_diff,
                     upper_ll, lower_ll, vardiff, slopedev, prev_params):
        window_length = int(window_length)
        mean_diff = float(mean_diff)
        max_diff = float(max_diff)
        upper_ll = float(upper_ll)
        lower_ll = float(lower_ll)
        vardiff = float(vardiff)
        slopedev = float(slopedev)
        # ground_master, mask = utils.read_df(site, start_date, end_date, freq)
        # df = ground_master.df
        # is_clear = \
        #     pvlib.clearsky.detect_clearsky(df['GHI'], df['Clearsky GHI pvlib'], df.index,
        #                                    window_length=window_length, mean_diff=mean_diff,
        #                                    max_diff=max_diff, upper_line_length=upper_ll, lower_line_length=lower_ll,
        #                                    slope_dev=slopedev, var_diff=vardiff)
        # score = metrics.fbeta_score(ground_master.df[mask]['sky_status'], is_clear[mask], beta=.5)

        new_params = {'Window length': window_length,
                      'Mean difference': mean_diff,
                      'Max difference': max_diff,
                      'Upper line length': upper_ll,
                      'Lower line length': lower_ll,
                      'Variance of slopes': vardiff,
                      'Max difference of slopes': slopedev,}
                      # 'F-score': score}
        # get old runs (if they exist)
        try:
            prev_runs = pd.read_json(prev_params)
        except:
            prev_runs = pd.DataFrame()

        # add new runs to previous
        new_params['Run'] = len(prev_runs) + 1
        prev_runs = pd.concat([prev_runs, pd.DataFrame([new_params])], ignore_index=True)

        return prev_runs.to_json()

    @app.callback(
        Output('cs-output', 'children'),
        [Input('cs-date_picker_start', 'value'),
         Input('cs-date_picker_end', 'value'),
         Input('cs-freq', 'value'),
         Input('cs-window_length_slider', 'value'),
         Input('cs-hidden', 'children')]
    )
    def update_plot(start_date, end_date, freq, window, params):
        params = pd.read_json(params)
        params = params.apply(pd.to_numeric)
        params = params.sort_values('Run')

        window_length = params['Window length'].values[-1]
        mean_diff = params['Mean difference'].values[-1]
        max_diff = params['Max difference'].values[-1]
        upper_ll = params['Upper line length'].values[-1]
        lower_ll = params['Lower line length'].values[-1]
        slopedev = params['Max difference of slopes'].values[-1]
        vardiff = params['Variance of slopes'].values[-1]

        ground_master, mask = utils.read_df(None, start_date, end_date, freq)
        df = ground_master.df
        is_clear, components, _ = \
            cs_utils.detect_clearsky(df['GHI'], df['Clearsky GHI pvlib'], df.index,
                                     window_length=window_length, mean_diff=mean_diff,
                                     max_diff=max_diff, upper_line_length=upper_ll, lower_line_length=lower_ll,
                                     slope_dev=slopedev, var_diff=vardiff, return_components=True)
            # pvlib.clearsky.detect_clearsky(df['GHI'], df['Clearsky GHI pvlib'], df.index,
            #                                window_length=window_length, mean_diff=mean_diff,
            #                                max_diff=max_diff, upper_line_length=upper_ll, lower_line_length=lower_ll,
            #                                slope_dev=slopedev, var_diff=vardiff)

        ground_master.calc_all_metrics(int(window))

        plots = []
        plots.append(go.Scatter(x=df.index, y=df['GHI'], name='GHI'))
        # plots.append(go.Scatter(x=df.index, y=df['GHI nsrdb'].interpolate(), name='GHI(NSRDB)'))
        plots.append(go.Scatter(x=df.index, y=df['Clearsky GHI pvlib'], name='GHI(CS)'))
        plots.append(go.Scatter(x=df[is_clear].index, y=df[is_clear]['GHI'], name='PVLib clear', mode='markers'))
        plots.append(go.Scatter(x=df[mask & df['sky_status'].astype(bool)].index,
                                y=df[mask & df['sky_status'].astype(bool)]['GHI'],
                                name='NSRDB clear', mode='markers',
                                marker={'symbol': 'circle-open', 'line': {'width': 3}, 'size': 10}))
        plots.append(go.Scatter(x=df.index, y=components['mean_diff'],
                                name='Mean difference', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['max_diff'],
                                name='Max difference', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['line_length'],
                                name='Line length', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['slope_nstd'],
                                name='Standard deviation of slopes', visible='legendonly'))
        plots.append(go.Scatter(x=df.index, y=components['slope_max'],
                                name='Max deviation of slopes', visible='legendonly'))
        layout = go.Layout(xaxis={'title': 'Date'}, yaxis={'title': 'W/m2'},
                           title='Window length: {}, mean diff: {}, max diff: {}, upper line length: {}, '
                                 'lower line length: {}, max slope difference: {}, std slope differece: {}'
                                  .format(window_length, mean_diff, max_diff, upper_ll, lower_ll, slopedev, vardiff))
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
            html.Div(ts_plot),
             # html.H3('Previous runs'),
             # html.Div([
             #     html.Div(scores_plot, className='four columns'),
             #     html.Div(table, className='eight columns',
             #              style={'margin': {'r': 20, 't': 40, 'b': 20, 'l': 20, 'pad': 0}})
             # ], className='row')
        ])

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

        return final
