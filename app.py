from dotenv import load_dotenv
import os
import obsidiantools.api as otools
from markdown_it import MarkdownIt
from src.utils import get_okr_data, get_okr_chart_data
import pathlib
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
vault = otools.Vault(VAULT_LOC).connect().gather()

# Get the data relevant for the OKR tracker
okr_note = '2024 Nov'
okr_chart_data = get_okr_chart_data(okr_note, vault)

df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash(__name__)
app.layout = [
    html.H1(children=okr_note + " tracker", style={'textAlign': 'center'}),
    dcc.Dropdown(list(okr_chart_data.okr.unique()),
                 okr_chart_data.okr.unique()[0], id='dropdown-selection'),
    dcc.Graph(id='graph-content')
]


@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    dff = okr_chart_data[okr_chart_data.okr == value]
    return px.line(dff, x='date', y='score')


if __name__ == '__main__':
    app.run(debug=True)

# EPIC: Get the OKR tracker done first
# TODO: Create the OKR tracker GUI for a single OKR cycle
# TODO: Test the OKR data extracted and chart data
# TODO: Description of the first 3 PRs contain info missing from their respective merge commit messages
