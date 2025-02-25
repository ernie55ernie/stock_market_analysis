import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from dash import html
from django_plotly_dash import DjangoDash

from dashboard_utils.terms import terms
from dashboard_utils.common_functions import plot_table
from dashboard_utils.common_styles import layout_style, table_style


def summary_by_year(df):
    """ Aggregate cash and stock dividends by year """
    years = [i for i in df.year.unique()]
    total = []
    for year in years:
        total.append([year, '現金股利', sum(df[df.year == year].cash_dividend)])
        total.append([year, '股票股利', sum(df[df.year == year].stock_dividend)])
    total = pd.DataFrame(total, columns=['年', '股利', '股利數量'])
    return total


def create_dash(df):
    app = DjangoDash('Dividend_Dashboard')

    if df.empty:
        app.layout = html.Div([html.H3(children='此公司近十年都沒有發放股利:/')],
                              style=layout_style)
    else:
        df_total = summary_by_year(df)
        df.columns = [terms[col] for col in df.columns]
        dividend_table = plot_table(df)

        # Ensure correct data types
        df_total['年'] = df_total['年'].astype(str)  # Convert 年 to string for categorical x-axis
        df_total['股利數量'] = pd.to_numeric(df_total['股利數量'], errors='coerce')  # Ensure 股利數量 is numeric
        df_total['股利'] = df_total['股利'].astype(str)  # Ensure 股利 is categorical

        print(df_total)  # Debugging print

        # **Create Figure Using `go.Bar`**
        fig_bar = go.Figure()

        # **Add Traces Manually for Each `股利` Type**
        for category in df_total['股利'].unique():
            df_filtered = df_total[df_total['股利'] == category]
            fig_bar.add_trace(
                go.Bar(
                    x=df_filtered['年'], 
                    y=df_filtered['股利數量'].tolist(), 
                    name=category
                )
            )

        # **Update Layout for Better Display**
        fig_bar.update_layout(
            title="歷年股利",
            xaxis_title="年",
            yaxis_title="股利數量",
            barmode='group',  # Stacked: 'stack', Side-by-Side: 'group'
            bargap=0.2,
            bargroupgap=0.1
        )

        # **Set Up Dash Layout**
        app.layout = html.Div([
            html.H3(children='歷年股利', style={'text-align': 'center'}),
            dcc.Graph(id='bar_chart',
                      figure=fig_bar,
                      style={'width': '100%', 'text-align': 'center'}),
            html.Div([dividend_table], style=table_style),
        ], style=layout_style)

    return app
