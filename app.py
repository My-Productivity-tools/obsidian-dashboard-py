from dotenv import load_dotenv
import os
import obsidiantools.api as otools
from src.utils import get_okr_data, get_okr_chart_data, get_daily_notes_tasks, get_habit_tracker_data
from src.note_utils import filter_daily_tasks
import pathlib
from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import dash_bootstrap_components as dbc
import datetime as dt
import pandas as pd
from itertools import product

# Generate the vault to use
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
vault = otools.Vault(VAULT_LOC).connect().gather()

# Get the data relevant for the OKR tracker
okr_note = '2024 Nov'
okr_data, okr_start_date, okr_end_date = get_okr_data(okr_note, vault)
okr_chart_data = get_okr_chart_data(okr_data, okr_start_date, okr_end_date)

# Get the data relevant for the Habit Tracker
habits = ['#gratitude', 'gratitude']
start_dates = [dt.date.fromisoformat(date)
               for date in ['2024-01-01', '2024-01-01']]
habit_data = {habit: get_habit_tracker_data(
    habit, start_dates[i], vault) for i, habit in enumerate(habits)}

# Create the Dash app
app = Dash(__name__)

okr_layout = html.Div(children=[
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

habit_layout = html.Div(children=[
    html.H1("Habit Tracker", style={'textAlign': 'center'}),
    dcc.Link('Go to OKR Tracker', href='/okr'),
    html.Div(children=[
        dcc.Dropdown(habits, habits[0], id='dropdown-selection'),
    ]),
    dcc.Graph(id='graph-content-habit'),
])

# sidebar = html.Div(
#     [
#         html.H2("Navigation", className="display-4"),
#         html.Hr(),
#         dbc.Nav(
#             [
#                 dbc.NavLink('OKR Tracker', href='/okr', active="exact"),
#                 dbc.NavLink('Habit Tracker',
#                             href='/habit', active="exact"),
#             ],
#             vertical=True,
#             pills=True,
#         ),
#     ],
#     style={
#         "position": "fixed",
#         "top": 0,
#         "left": 0,
#         "bottom": 0,
#         "width": "200px",
#         "padding": "20px",
#         "background-color": "#f8f9fa",
#     },
# )

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    # sidebar,
    html.Div(id='page-content',
             style={"margin-left": "220px", "padding": "20px"}),
    html.Div(okr_layout, id='okr-container', style={'display': 'none'}),
    html.Div(habit_layout, id='habit-container', style={'display': 'none'})
])


@app.callback(
    [Output('okr-container', 'style'),
     Output('habit-container', 'style')],
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/okr' or pathname == '/':
        return {'display': 'block'}, {'display': 'none'}
    elif pathname == '/habit':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}


# @app.callback(
#     Output('page-content', 'children'),
#     [Input('url', 'pathname')]
# )
# def display_page(pathname):
#     if pathname == '/okr' or pathname == '/':
#         return get_okr_layout()
#     elif pathname == '/habit':
#         return get_habit_layout()
#     else:
#         return html.H1("404: Page not found")  # Default 404 message


@app.callback(
    Output('graph-content-habit', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    dff = habit_data[value]
    return px.line(dff, x='date', y='score')


if __name__ == '__main__':
    app.run(debug=True)

# EPIC: Get the OKR tracker done first
# TODO: Test the OKR data extracted and chart data
# TODO: Description of the first 3 PRs contain info missing from their respective merge commit messages

# @app.callback(
#     Output("offcanvas", "is_open"),
#     [Input("open-offcanvas", "n_clicks")],
#     [State("offcanvas", "is_open")]
# )
# def toggle_offcanvas(n_clicks, is_open):
#     if n_clicks:
#         return not is_open
#     return is_open
