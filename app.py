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
app.layout = html.Div(children=[
    html.H1(children='OKR Tracker - ' + okr_note,
            style={'textAlign': 'center'}),
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

if __name__ == '__main__':
    app.run(debug=True)

# EPIC: Get the OKR tracker done first
# TODO: Test the OKR data extracted and chart data
# TODO: Description of the first 3 PRs contain info missing from their respective merge commit messages
