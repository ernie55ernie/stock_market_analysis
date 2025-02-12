import pandas as pd
import plotly.express as px
from dash import dcc
from dash import html
from django_plotly_dash import DjangoDash

from dashboard_utils.terms import terms
from dashboard_utils.common_functions import plot_table
from dashboard_utils.common_styles import layout_style, table_style


def summary_by_year(df):
    years = [i for i in df.year.unique()]
    total = []
    for year in years:
        total.append([year, '現金股利', sum(df[df.year == year].cash_dividend)])
        total.append([year, '股票股利', sum(df[df.year == year].stock_dividend)])
    total = pd.DataFrame(total, columns=['年', '股利', '數量'])
    return total


def create_dash(df):
    app = DjangoDash('Dividend_Dashboard')
    if not len(df):
        app.layout = html.Div([html.H3(children='此公司近十年都沒有發放股利:/')],
                              style=layout_style)
    else:
        df_total = summary_by_year(df)
        print(df_total)
        df.columns = [terms[col] for col in df.columns]
        dividend_table = plot_table(df)
        fig_bar = px.bar(df_total, x='年', y='數量', color='股利')
        fig_bar.update_traces(width=0.5)
        fig_bar.update_xaxes(tickvals=df_total['年'].unique())
        app.layout = html.Div([
            html.H3(children='歷年股利', style={'text_align': 'center'}),
            dcc.Graph(id='bar_chart',
                      figure=fig_bar,
                      style={
                          'width': '100%',
                          'text-align': 'center'
                      }),
            html.Div([dividend_table], style=table_style),
        ],
                              style=layout_style)
