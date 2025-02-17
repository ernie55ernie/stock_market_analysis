import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
from dash.dependencies import ALL
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots
import pandas as pd
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Referer": "https://concords.moneydj.com/",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

def fetch_broker_data(stock_code, period="近一日"):
    url_map = {
        "近一日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}.djhtm",
        "近五日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}_2.djhtm",
        "近十日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}_3.djhtm",
        "近20日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}_4.djhtm",
        "近40日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}_5.djhtm",
        "近60日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}_6.djhtm",
        "近120日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}_7.djhtm",
        "近240日": f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}_8.djhtm",
    }
    url = url_map.get(period)
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    last_update = soup.find("div", class_="t11").text.split("：")[-1].strip()
    table = soup.find("table", {"id": "oMainTable"})
    rows = table.find_all("tr")[3:]
    buy_sell_data = []
    for row in rows:
        cells = row.find_all("td", class_=["t4t1", "t3n1"])
        if len(cells) >= 10:
            buy_broker_href = cells[0].find("a")["href"] if cells[0].find("a") else None
            sell_broker_href = cells[5].find("a")["href"] if cells[5].find("a") else None
            buy_sell_data.append({
                "buy_broker": cells[0].text.strip(),
                "buy_net": cells[3].text.strip(),
                "buy_href": f"https://concords.moneydj.com{buy_broker_href}" if buy_broker_href else None,
                "sell_broker": cells[5].text.strip(),
                "sell_net": cells[8].text.strip(),
                "sell_href": f"https://concords.moneydj.com{sell_broker_href}" if sell_broker_href else None,
            })
    buy_sell_df = pd.DataFrame(buy_sell_data)
    buy_sell_df = pd.DataFrame(buy_sell_data)
    return last_update, buy_sell_df

def fetch_broker_details(broker_href, period):
    period_map = {
        "近20日": "",
        "近40日": "&C=2",
        "近60日": "&C=3"
    }
    url = broker_href + period_map.get(period, "")
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    detail_table = soup.find("table", {"id": "oMainTable"})
    
    if detail_table:
        detail_rows = detail_table.find_all("tr")[1:]  # Skip header row
        details = []
        for detail_row in detail_rows:
            detail_cells = detail_row.find_all("td")
            if len(detail_cells) >= 5:
                details.append({
                    "日期": detail_cells[0].text.strip(),
                    "買進(張)": detail_cells[1].text.strip().replace(',', ''),
                    "賣出(張)": detail_cells[2].text.strip().replace(',', ''),
                    "買賣總額(張)": detail_cells[3].text.strip().replace(',', ''),
                    "買賣超(張)": detail_cells[4].text.strip().replace(',', '')
                })
        broker_df = pd.DataFrame(details)
        return broker_df
    return pd.DataFrame()

def create_dash(chip_data, institutional_df, price_df, stock_code):
    price_df['date'] = pd.to_datetime(price_df['date'], format='%Y-%m-%d')
    institutional_df['date'] = pd.to_datetime(institutional_df['date'], format='%Y-%m-%d')

    last_update, buy_sell_df = fetch_broker_data(stock_code)
    broker_data_map = {}
    broker_name = None
    
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
                   name=institutional_investors[col], 
                   orientation='v'))
    fig_bar_with_line.update_layout(barmode='stack', yaxis={'title': "成交量"})
    fig_bar_with_line.add_trace(go.Scatter(x=institutional_df['date'],
                                           y=price_df['close'],
                                           name='收盤價',
                                           mode='lines+markers',
                                           marker_color='gray'),
                                secondary_y=True)

    # Dash App
    app = DjangoDash('Chip_Dashboard')

    # Layout
    app.layout = html.Div([
        dcc.Tabs([
            dcc.Tab(label='籌碼分布與近90天三大法人買賣超', children=[
                html.H3(children="籌碼分布", style={'text-align': 'center'}),
                dcc.Graph(id='pie_chart',
                          figure=fig_pie,
                          style={'width': '90%', 'text-align': 'center', 'marginTop': '5%', 'marginBottom': '15%', 'marginLeft': '5%'},
                          config={'displayModeBar': False}),
                html.H3(children="近90天三大法人買賣超", style={'text-align': 'center'}),
                dcc.Graph(id='fig_bar',
                          figure=fig_bar_with_line,
                          style={'width': '90%', 'marginLeft': '5%'})
            ]),
            dcc.Tab(label='券商分點進出明細', children=[
                html.Div([
                    dcc.Dropdown(
                        id='date-range-dropdown',
                        options=[
                            {'label': period, 'value': period} for period in [
                                "近一日", "近五日", "近十日", "近20日", "近40日", "近60日", "近120日", "近240日"
                            ]
                        ],
                        value="近一日",
                        clearable=False,
                        style={'width': '150px', 'display': 'inline-block', 'margin-right': '10px'}
                    ),
                    html.Span(id='last-update-text', style={'font-size': '12px', 'color': 'gray'})
                ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin-bottom': '10px'}),
                html.Div(id='buy-sell-table'),
                dcc.Dropdown(
                    id='broker-period-dropdown',
                    options=[
                        {'label': '近20日', 'value': '近20日'},
                        {'label': '近40日', 'value': '近40日'},
                        {'label': '近60日', 'value': '近60日'}
                    ],
                    value='近20日',
                    clearable=False,
                    style={'width': '150px', 'display': 'inline-block', 'margin-right': '10px'}
                ),
                html.Div(id='broker-graph', style={'display': 'none'}),
                html.Div(id='broker-detail-table', style={'margin-top': '20px'}),
            ])
        ])
    ])
    
    @app.callback(
        [Output('last-update-text', 'children'),
         Output('buy-sell-table', 'children')],
        [Input('date-range-dropdown', 'value')]
    )
    def update_buy_sell_table(period):
        global buy_sell_df
        last_update, buy_sell_df = fetch_broker_data(stock_code, period)
        buy_sell_df = buy_sell_df.replace('', None)  # Replace '' with None (missing value)
        #buy_sell_df = buy_sell_df.dropna(subset=['buy_net', 'sell_net'])  # Drop rows where these columns have missing values
        max_value = max(buy_sell_df['buy_net'].str.replace(',', '').astype(int).max(), buy_sell_df['sell_net'].str.replace(',', '').astype(int).max())
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
                                        'width': f"{(int(row['buy_net'].replace(',', '')) / max_value) * 100}%",
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
                                        'width': f"{(int(row['sell_net'].replace(',', '')) / max_value) * 100}%",
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
        return f"最後更新日: {last_update}", buy_sell_table

    # Callbacks
    @app.callback(
        [Output('broker-graph', 'children'),
         Output('broker-graph', 'style'),
         Output('broker-detail-table', 'children')],
        [Input({'type': 'broker-name', 'index': ALL, 'action': ALL}, 'n_clicks'), 
         Input('broker-period-dropdown', 'value')],
        prevent_initial_call=True
    )
    def update_broker_graph(n_clicks, period):
        global broker_name, buy_sell_df
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, {'display': 'none'}, ''
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        if 'broker-name' in trigger:
            broker_name = eval(trigger)['index']
            
        if (broker_name, period) in broker_data_map:
            broker_df = broker_data_map[(broker_name, period)]
        else:
            broker_href = buy_sell_df.loc[buy_sell_df['buy_broker'] == broker_name, 'buy_href'].values
            if not broker_href:
                broker_href = buy_sell_df.loc[buy_sell_df['sell_broker'] == broker_name, 'sell_href'].values
            if broker_href:
                broker_df = fetch_broker_details(broker_href[0], period)
                broker_data_map[broker_name] = broker_df
            else:
                return dash.no_update, {'display': 'none'}, ''
        
        rev_broker_df = broker_df.sort_values(by='日期', ascending=True)
        fig = make_subplots(specs=[[{'secondary_y': True}]])
        rev_broker_df['日期'] = pd.to_datetime(rev_broker_df['日期'], format='%Y/%m/%d')
        # merged_df = rev_broker_df.merge(price_df, left_on='日期', right_on='date', how='left')
        fig.add_trace(
            go.Scatter(
                x=price_df['date'],
                y=price_df['close'],
                name="股價",
                mode='lines+markers',
                marker_color='blue'
            ),
            secondary_y=True
        )
        fig.add_trace(
            go.Bar(
                x=rev_broker_df['日期'],
                y=rev_broker_df['買賣超(張)'].astype(int),
                name="買賣超",
                marker_color=['red' if x > 0 else 'green' for x in rev_broker_df['買賣超(張)'].astype(int)], 
                orientation='v'
            ),
            secondary_y=False
        )
        fig.update_layout(title=f"{broker_name} 買賣超及股價", yaxis_title="買賣超", yaxis2_title="股價", xaxis_title="日期")
        
        table = html.Div([
            html.H4(f"進出明細表 - {broker_name}", style={'text-align': 'center'}),
            dcc.Graph(
                figure={
                    'data': [go.Table(
                        header=dict(values=list(broker_df.columns)),
                        cells=dict(values=[broker_df[col] for col in broker_df.columns])
                    )],
                }
            )
        ])
        
        return dcc.Graph(figure=fig), {'display': 'block'}, table

    return app
