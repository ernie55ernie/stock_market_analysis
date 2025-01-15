import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
from dash.dependencies import ALL
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots
import pandas as pd


def create_dash(chip_data, institutional_df, price_df, buy_sell_df, broker_data_map):
    pie_chart_color = [
        'cornflowerblue', 'lightcoral', 'mediumaquamarine', 'mediumpurple',
        'gold', 'lightsteelblue', 'sandybrown'
    ]

    # Pie Chart for chip data
    fig_pie = go.Figure(data=[
        go.Pie(labels=['董監', '外資', '投信', '自營商', '融資', '融券', '其他'],
               values=chip_data['amount'],
               marker_colors=pie_chart_color)
    ])
    fig_pie.update_layout(margin=dict(t=10, b=0, l=0, r=0), font=dict(size=14))

    # Bar chart with line overlay for institutional data and price
    institutional_investors = {
        'foreign': '外資',
        'invest': '投信',
        'dealer': '自營商'
    }
    fig_bar_with_line = make_subplots(specs=[[{'secondary_y': True}]])
    for col in institutional_investors:
        fig_bar_with_line.add_trace(
            go.Bar(x=institutional_df['date'],
                   y=institutional_df[col],
                   name=institutional_investors[col]))
    fig_bar_with_line.update_layout(barmode='stack', yaxis={'title': "成交量"})
    fig_bar_with_line.add_trace(go.Scatter(x=institutional_df['date'],
                                           y=price_df['close'],
                                           name='收盤價',
                                           mode='lines+markers',
                                           marker_color='gray'),
                                secondary_y=True)

    buy_sell_df = buy_sell_df.replace('', None)  # Replace '' with None (missing value)
    buy_sell_df = buy_sell_df.dropna(subset=['buy_net', 'sell_net'])  # Drop rows where these columns have missing values
    max_value = max(buy_sell_df['buy_net'].astype(int).max(), buy_sell_df['sell_net'].astype(int).max())
    buy_sell_table = html.Div([
        html.Table(
            # Table Header
            [
                html.Tr([
                    html.Th("買超券商", style={'text-align': 'center'}),
                    html.Th("買超張數", style={'text-align': 'center'}),
                    html.Th("賣超張數", style={'text-align': 'center'}),
                    html.Th("賣超券商", style={'text-align': 'center'}),
                ])
            ] +
            # Table Body
            [
                html.Tr([
                    # Buy Broker Name (clickable)
                    html.Td(
                        html.A(
                            row['buy_broker'],
                            href="javascript:void(0);",  # Prevent default behavior
                            id={'type': 'broker-name', 'index': row['buy_broker'], 'action': 'buy'},
                            style={'color': 'red', 'cursor': 'pointer'}
                        ),
                        style={'text-align': 'center'}
                    ),
                    
                    # Buy Net Bar
                    html.Td(
                        html.Div([
                            html.Span(row['buy_net'], style={'color': 'black', 'margin-right': '5px'}),
                            html.Div(
                                style={
                                    'background-color': '#fdd',
                                    'height': '20px',
                                    'width': f"{(int(row['buy_net']) / max_value) * 100}%",
                                    'display': 'inline-block',
                                }
                            )
                        ], style={'display': 'flex', 'justify-content': 'flex-end'}),
                        style={'width': '25%', 'text-align': 'center'}
                    ),
                    
                    # Sell Net Bar
                    html.Td(
                        html.Div([
                            html.Div(
                                style={
                                    'background-color': '#dfd',
                                    'height': '20px',
                                    'width': f"{(int(row['sell_net']) / max_value) * 100}%",
                                    'display': 'inline-block',
                                }
                            ),
                            html.Span(row['sell_net'], style={'color': 'black', 'margin-left': '5px'})
                        ], style={'display': 'flex', 'justify-content': 'flex-start'}),
                        style={'width': '25%', 'text-align': 'center'}
                    ),
                    
                    # Sell Broker Name (clickable)
                    html.Td(
                        html.A(
                            row['sell_broker'],
                            href="javascript:void(0);",  # Prevent default behavior
                            id={'type': 'broker-name', 'index': row['sell_broker'], 'action': 'sell'},
                            style={'color': 'green', 'cursor': 'pointer'}
                        ),
                        style={'text-align': 'center'}
                    ),
                ], style={'text-align': 'center'}) for _, row in buy_sell_df.iterrows()
            ],
            style={
                'width': '100%',
                'border-collapse': 'collapse',
                'margin': '20px auto',
                'font-family': 'Arial, sans-serif',
                'font-size': '14px',
                'border': '1px solid #ddd',
            }
        )
    ])

    # Dash App
    app = DjangoDash('Chip_Dashboard')

    # Layout
    app.layout = html.Div([
        html.H3(children="籌碼分布", style={'text-align': 'center'}),
        dcc.Graph(id='pie_chart',
                  figure=fig_pie,
                  style={
                      'width': '90%',
                      'text-align': 'center',
                      'marginTop': '5%',
                      'marginBottom': '15%',
                      'marginLeft': '5%'
                  },
                  config={'displayModeBar': False}),
        html.H3(children="近90天三大法人買賣超", style={'text-align': 'center'}),
        dcc.Graph(id='fig_bar',
                  figure=fig_bar_with_line,
                  style={
                      'width': '90%',
                      'marginLeft': '5%'
                  }),
        html.H3(children="買超與賣超明細", style={'text-align': 'center'}),
        buy_sell_table,
        html.Div(id='broker-graph', style={'display': 'none', 'marginBottom': '20px'}),  # Placeholder for the broker graph
        html.Div(id='broker-detail-table', style={'margin-top': '20px'}),
    ])

    # Callbacks
    @app.callback(
        [Output('broker-graph', 'children'),
         Output('broker-graph', 'style'),
         Output('broker-detail-table', 'children')],
        [Input({'type': 'broker-name', 'index': ALL, 'action': ALL}, 'n_clicks')],
        prevent_initial_call=True
    )
    def update_broker_graph(n_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, {'display': 'none'}, ''
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        broker_name = eval(trigger)['index']

        if broker_name in broker_data_map:
            broker_df = broker_data_map[broker_name]
            price_broker_df = broker_df.sort_values(by='日期')
            bar_colors = ['red' if value > 0 else 'green' for value in price_broker_df['買賣超(張)'].astype(int)]
            # Create the graph
            fig = make_subplots(specs=[[{'secondary_y': True}]])
            fig.add_trace(
                go.Scatter(
                    x=price_broker_df['日期'],
                    y=price_df['close'],  # Stock price
                    name="股價",
                    mode='lines+markers',
                    marker_color='blue'
                ),
                secondary_y=True
            )
            fig.add_trace(
                go.Bar(
                    x=price_broker_df['日期'],
                    y=price_broker_df['買賣超(張)'].astype(int),  # Buy-sell net
                    name="買賣超",
                    marker_color=bar_colors
                ),
                secondary_y=False
            )
            fig.update_layout(
                title=f"{broker_name} 買賣超及股價",
                yaxis_title="買賣超",
                yaxis2_title="股價",
                xaxis_title="日期",
                margin=dict(t=30, b=10),
                height=400
            )
            
            # Create broker detail table
            table = html.Div([
                html.H4(f"進出明細表 - {broker_name}", style={'text-align': 'center'}),
                dcc.Graph(
                    id='broker-detail',
                    figure={
                        'data': [go.Table(
                            header=dict(values=list(broker_df.columns)),
                            cells=dict(values=[broker_df[col] for col in broker_df.columns])
                        )],
                        'layout': {
                            'autosize': True,
                            'margin': {'l': 10, 'r': 10, 't': 10, 'b': 10},
                        }
                    }
                )
            ])

            return dcc.Graph(figure=fig), {'display': 'block'}, table

        return dash.no_update, {'display': 'none'}, ''

    return app
