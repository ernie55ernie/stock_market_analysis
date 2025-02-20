import time
import pandas as pd
import yfinance as yf
from datetime import datetime

import plotly.graph_objects as go
from dash import dcc
from dash import html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output

from dashboard_utils.common_styles import checklist_style, line_plot_style


def query_historical_price(stock_code, market_type, end_date, period=14):
    end = datetime.strptime(end_date, '%Y-%m-%d')
    end = int(time.mktime(time.strptime(end_date, '%Y-%m-%d'))) + 86400
    start = end - 86400 * 365 * 5
    print('stock_code: ', stock_code, 'end date: ', end_date)
    start_date = time.strftime('%Y-%m-%d', time.localtime(start))
    if market_type == '上市':
        data = yf.download(f"{stock_code}.TW", start=start_date, end=end_date)
    elif market_type == '上櫃':
        data = yf.download(f"{stock_code}.TWO", start=start_date, end=end_date)
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    data['Date'] = data.index.astype(str)
    data = data.reset_index(drop=True)
    data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
    data.columns = ['date', 'open', 'high', 'low', 'daily', 'volume']
    data['5MA'] = data.daily.rolling(5).mean()
    data['20MA'] = data.daily.rolling(20).mean()
    data['60MA'] = data.daily.rolling(60).mean()
    """Calculate the Stochastic Oscillator (K and D values)."""
    data['low_min'] = data['low'].rolling(window=period).min()
    data['high_max'] = data['high'].rolling(window=period).max()
    data['%K'] = ((data['daily'] - data['low_min']) /
                  (data['high_max'] - data['low_min'])) * 100
    data['%D'] = data['%K'].rolling(window=3).mean()
    data['%K'] = data['%K'].fillna(0).replace([float('inf'), -float('inf')], 0)
    data['%D'] = data['%D'].fillna(0).replace([float('inf'), -float('inf')], 0)
    return data

def create_dash(stock_code, company_name, price_df):
    price_df['date'] = pd.to_datetime(price_df['date'])
    features = ['daily', '5MA', '20MA', '60MA', 'k線']
    slider_style = {'margin-right': '-100px'}
    app = DjangoDash('Price_Dashboard')
    app.layout = html.Div(
        [
            html.H3(id='title',
                    children="近90天股價走勢",
                    style={'text-align': 'center'}),
            dcc.Checklist(
                id='checkbox',
                options=[{
                    'label': features[i],
                    'value': i
                } for i in range(len(features))],
                value=[i for i in range(len(features))],  # 預設沒有k線
                style={'display': 'flex', 'flex-wrap': 'wrap'}),
            dcc.Graph(id='line_plot', style=line_plot_style),
            dcc.Graph(id='bar_chart',
                      style={
                          'width': '100%',
                          'height': '300px',
                          'text-align': 'center'
                      }),
            dcc.Graph(id='stochastic_plot',
                      style={'width': '100%', 'height': '300px', 'text-align': 'center'}),
            dcc.RangeSlider(id='slider',
                            min=0,
                            max=len(price_df) - 1,
                            value=[len(price_df) - 90,
                                   len(price_df) - 1],
                            step=1,
                            marks={
                                0: {
                                    'label': price_df.date[0],
                                    'style': slider_style
                                },
                                len(price_df) - 90: {
                                    'label': price_df.date.iloc[-90],
                                    'style': {
                                        'margin-top': '-40px',
                                        'margin-right': '-100px'
                                    }
                                },
                                len(price_df) - 1: {
                                    'label': price_df.date.iloc[-1],
                                    'style': slider_style
                                }
                            }),
        ],
        style={
            'position': 'absolute',
            'left': '10%',
            'width': '80%',
            'text-align': 'center'
        })

    @app.callback(Output('title', 'children'), [Input('slider', 'value')])
    def update_title(date_range):
        text = f"近{date_range[1] - date_range[0] +1}天股價走勢"
        return text

    @app.callback(Output('line_plot', 'figure'),
                  [Input('checkbox', 'value'),
                   Input('slider', 'value')])
    def update_line_chart(contents, date_range):
        #        selected_features = [features[i] for i in contents]
        line_colors = ['dimgray', 'dodgerblue', 'violet', 'orange']
        fig = go.Figure()
        selected_data = price_df.iloc[date_range[0]:date_range[1] + 1]
        x = selected_data.date
        #for col in selected_features:
        for i in contents:
            col = features[i]
            if col == "k線":
                fig.add_trace(
                    go.Candlestick(x=x,
                                   open=selected_data['open'].tolist(),
                                   high=selected_data['high'].tolist(),
                                   low=selected_data['low'].tolist(),
                                   close=selected_data['daily'].tolist(),
                                   name="k線",
                                   increasing_line_color='red',
                                   decreasing_line_color='green'))

            else:
                fig.add_trace(
                    go.Scatter(x=x,
                               y=selected_data[col].tolist(),
                               mode='lines',
                               name=col,
                               marker_color=line_colors[i]))
        fig.update_layout(title={
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
        },
                          yaxis_title='$NTD',
                          xaxis_rangeslider_visible=False)
        return fig

    @app.callback(Output('slider', 'marks'), [Input('slider', 'value')])
    def update_slider_mark(date_range):
        start = price_df.date.iloc[date_range[0]]
        end = price_df.date.iloc[date_range[1]]
        return {
            0: {
                'label': price_df.date[0],
                'style': slider_style
            },
            date_range[0]: {
                'label': start,
                'style': {
                    'margin-top': '-40px',
                    'margin-right': '-100px'
                }
            },
            date_range[1]: {
                'label': end,
                'style': slider_style
            }
        }

    @app.callback(Output('bar_chart', 'figure'), [Input('slider', 'value')])
    def update_bar_chart(date_range):
        selected_data = price_df.iloc[date_range[0]:date_range[1] + 1]
        bull = selected_data[selected_data.daily > selected_data.open]
        bear = selected_data[selected_data.daily < selected_data.open]
        tie = selected_data[selected_data.daily == selected_data.open]
        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=bull.date,
                   y=(bull.volume / 1e3).tolist(),
                   marker_color='red',
                   name='漲'))
        fig.add_trace(
            go.Bar(x=bear.date,
                   y=(bear.volume / 1e3).tolist(),
                   marker_color='green',
                   name='跌'))
        fig.add_trace(
            go.Bar(x=tie.date,
                   y=(tie.volume / 1e3).tolist(),
                   marker_color='gray',
                   name='平'))
        fig.update_layout(title={
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top',
        },
                          yaxis_title='成交量(千股)')
        return fig

    @app.callback(Output('stochastic_plot', 'figure'), [Input('slider', 'value')])
    def update_stochastic_plot(date_range):
        selected_data = price_df.iloc[date_range[0]:date_range[1] + 1]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=selected_data['date'],
                y=selected_data['%K'].tolist(),
                mode='lines',
                name='%K',
                marker_color='blue'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=selected_data['date'],
                y=selected_data['%D'].tolist(),
                mode='lines',
                name='%D',
                marker_color='orange'
            )
        )
        fig.update_layout(title={
            'y': 0.9,
            'x': 0.45,
            'xanchor': 'center',
            'yanchor': 'top',
        },
        yaxis_title='Stochastic Oscillator',
        xaxis_title='Date')
        return fig
    
    return app