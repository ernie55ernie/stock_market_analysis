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
        df.columns = [terms[col] for col in df.columns]
        dividend_table = plot_table(df)
        df_total['年'] = df_total['年'].astype(str)
        df_total['數量'] = pd.to_numeric(df_total['數量'], errors='coerce')
        df_total['股利'] = df_total['股利'].astype(str)
        df_total.set_index(['年', '股利'], inplace=True)
        print(df_total)
        fig_bar = px.bar(df_total, x=df_total.index.get_level_values(0), y='數量', color=df_total.index.get_level_values(1))
        fig_bar.update_traces(width=0.5)
        #fig_bar.update_xaxes(tickvals=df_total.index.get_level_values(0).unique())
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
