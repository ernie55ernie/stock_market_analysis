import plotly.graph_objects as go
from dash import dcc
from dash import html
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots


def create_dash(chip_data, institutional_df, price_df, buy_sell_df):
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

    # Create table with horizontal bars starting from the center
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
                    # Buy Broker Name
                    html.Td(row['buy_broker'], style={'text-align': 'center', 'color': 'red'}),
                    
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
                    
                    # Sell Broker Name
                    html.Td(row['sell_broker'], style={'text-align': 'center', 'color': 'green'}),
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

    # Dash App Layout
    app = DjangoDash('Chip_Dashboard')
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
        buy_sell_table
    ])
