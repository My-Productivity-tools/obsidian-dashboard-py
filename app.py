from dotenv import load_dotenv
import os
import obsidiantools.api as otools
from src.utils import get_okr_chart_data
import pathlib
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px

load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
vault = otools.Vault(VAULT_LOC).connect().gather()

# Get the data relevant for the OKR tracker
okr_note = '2024 Nov'
okr_chart_data = get_okr_chart_data(okr_note, vault)

app = Dash(__name__)
app.layout = html.Div(children=[
    html.H1(children='OKR Tracker - ' + okr_note,
            style={'textAlign': 'center'}),
    html.Div(children=[
        dcc.Graph(id='graph-content-' + okr,
                  figure=px.line(okr_chart_data[okr_chart_data.okr == okr],
                                 x='date', y=['score', 'target', 'target_70_pct'],
                                 labels={'value': 'Score',
                                         'variable': 'Metrics'}))
        for okr in okr_chart_data.okr.unique()
    ], style={'columnCount': 2})
])


if __name__ == '__main__':
    app.run(debug=True)

# EPIC: Get the OKR tracker done first
# TODO: Create the OKR tracker GUI for a single OKR cycle
# TODO: Test the OKR data extracted and chart data
# TODO: Description of the first 3 PRs contain info missing from their respective merge commit messages
