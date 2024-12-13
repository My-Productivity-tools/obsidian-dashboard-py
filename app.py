from dotenv import load_dotenv
import os
import obsidiantools.api as otools
from src.utils import get_okr_data, get_okr_chart_data
import pathlib
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px

load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
vault = otools.Vault(VAULT_LOC).connect().gather()

# Get the data relevant for the OKR tracker
okr_note = '2024 Nov'
okr_data, okr_start_date, okr_end_date = get_okr_data(okr_note, vault)
okr_chart_data = get_okr_chart_data(okr_data, okr_start_date, okr_end_date)

app = Dash(__name__)
page1_layout = html.Div(children=[
    html.H1('OKR Tracker - ' + okr_note,
            style={'textAlign': 'center'}),
    dcc.Link('Go to Habit Tracker', href='/habit'),
    html.Div(children=[
        dcc.Graph(id='graph-content-' + okr,
                  figure={'data': [
                      {'x': okr_chart_data[okr_chart_data.okr == okr]['date'],
                       'y': okr_chart_data[okr_chart_data.okr == okr][col],
                          'type': 'line', 'name': name}
                      for col, name in zip(['score', 'target_70_pct', 'target'],
                                           ['score', '70% of target', 'target'])],
                      'layout': {'title': okr, 'showlegend': False, 'font': {'size': 18},
                                 'yaxis': {'title': okr_data[okr]['criteria']}}})
        for okr in okr_chart_data.okr.unique()
    ], style={'display': 'grid',
              'gap': '0px',  # Spacing between items
              # 2 columns
              'grid-template-columns': " ".join(['1fr'] * ((len(okr_data.keys())+1)//2)),
              'grid-auto-flow': 'row dense',  # Ensures children fill rows first
              'align-items': 'start'  # Align items to the start of the row
              })
])

page2_layout = html.Div(children=[
    html.H1("Habit Tracker"),
    dcc.Link('Go to OKR Tracker', href='/okr')])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callback to update page content based on URL


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/okr' or pathname == '/':
        return page1_layout
    elif pathname == '/habit':
        return page2_layout
    else:
        return html.H1("404: Page not found")  # Default 404 message


if __name__ == '__main__':
    app.run(debug=True)

# EPIC: Get the OKR tracker done first
# TODO: Test the OKR data extracted and chart data
# TODO: Description of the first 3 PRs contain info missing from their respective merge commit messages
