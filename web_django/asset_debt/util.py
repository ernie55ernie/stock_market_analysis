import plotly.graph_objects as go
from dash import dcc
from dash import html
from plotly.subplots import make_subplots
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output

from dashboard_utils.terms import terms
from dashboard_utils.common_functions import plot_table
from dashboard_utils.common_styles import checklist_style, line_plot_style, table_style, layout_style


def create_dash(df):
    app = DjangoDash('Asset_Debt_Dashboard')
    df['season'] = df['season'].apply(
        lambda s: f"{s.split('_')[0]}第{s.split('_')[1]}季" if '_' in s else s
    )
    pbr = '每股參考淨值'
    share_capital = '股本'
    df1 = df.drop(columns=['PBR', 'share_capital'])
    df1.columns = [terms[col] for col in df1.columns]
    
    df1_for_table = df1.copy()
    columns_with_commas = [col for col in df1_for_table.columns if col != '季']
    for col in columns_with_commas:
        if col in df1_for_table.columns:
            df1_for_table[col] = df1_for_table[col].apply(lambda x: f"{x:,}")
    asset_debt_table = plot_table(df1_for_table)
    #    features = [col for col in df1.columns if col != '季']
    one_line_plot = make_subplots(rows=3,
                                  cols=1,
                                  subplot_titles=('負債比率', pbr, share_capital),
                                  shared_xaxes=True)
    one_line_plot.append_trace(go.Scatter(
        x=df['season'],
        y=(100 * (df['total_debt'] / df['total_assets'])).tolist(),
        mode='lines+markers'),
                               row=1,
                               col=1)
    one_line_plot.append_trace(go.Scatter(x=df['season'],
                                          y=df['PBR'].tolist(),
                                          mode='lines+markers'),
                               row=2,
                               col=1)
    one_line_plot.append_trace(go.Scatter(x=df['season'],
                                          y=(df['share_capital'] /
                                             1e4).values.reshape(-1),
                                          mode='lines+markers'),
                               row=3,
                               col=1)
    one_line_plot.update_yaxes(title_text='%', row=1, col=1)
    one_line_plot.update_yaxes(title_text='$NTD', row=2, col=1)
    one_line_plot.update_yaxes(title_text='$NTD 萬', row=3, col=1)
    one_line_plot.update_layout(showlegend=False)

    div_children = [
        html.H3(children='近年資產負債表', style={'text_align': 'center'}),
        html.P(children='單位: 千元', style={'marginLeft': '85%'}),
        dcc.Checklist(id='checkbox',
                      options=[{
                          'label': df1.columns[i],
                          'value': i
                      } for i in range(len(df1.columns))
                               if df1.columns[i] != '季'],
                      value=[
                          i for i in range(len(df1.columns))
                          if df1.columns[i] != '季'
                      ],
                      style=checklist_style),
        dcc.Graph(id='asset_debt_line_plot', style=line_plot_style),
        html.Div([asset_debt_table], style=table_style),
        dcc.Graph(figure=one_line_plot,
                  style={
                      'width': '900px',
                      'left': '10%',
                      'height': '10%',
                      'text-align': 'center'
                  })
    ]
    app.layout = html.Div(div_children, style=layout_style)

    @app.callback(Output('asset_debt_line_plot', 'figure'),
                  [Input('checkbox', 'value')])
    def update_line_chart(contents):
        features = [df1.columns[i] for i in contents]
        fig = go.Figure()

        for col in features:
            fig.add_trace(
                go.Scatter(x=df1['季'],
                           y=df1[col].tolist(),
                           mode='lines+markers',
                           name=col))

        fig.update_layout(title={
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
        },
                          yaxis_title='$NTD 千')
        fig.update_xaxes(tickangle=45)
        return fig
