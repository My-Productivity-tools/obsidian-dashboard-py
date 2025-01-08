from dotenv import load_dotenv
import os
import obsidiantools.api as otools
from src.utils import get_okr_data, get_okr_pivot_data, get_daily_notes_tasks, get_habit_tracker_data
from src.note_utils import filter_daily_tasks
import pathlib
from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import dash_bootstrap_components as dbc
import datetime as dt
import pandas as pd
import pickle
from src.ui_utils import get_okr_graph_data, get_habit_graph_data, display_page

# Load the environment variables
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
CRITERIA_STORY_POINTS = os.getenv('CRITERIA_STORY_POINTS')
CRITERIA_COUNT = os.getenv('CRITERIA_COUNT')
CRITERIA_DURATION = os.getenv('CRITERIA_DURATION')
OKR_NOTE = os.getenv('OKR_NOTE')
HABITS = [habit.strip() for habit in os.getenv('HABITS').split(',')]
CRITERIA = [criterion.strip()
            for criterion in os.getenv('CRITERIA').split(',')]
START_DATES = [date.strip() for date in os.getenv(
    'START_DATES').split(',')]  # Start dates for each habit

ENV = os.getenv('ENV')
PATH_PREFIX = os.getenv('PATH_PREFIX')

# Generate the vault to use
vault = otools.Vault(VAULT_LOC).connect().gather()

# Get the data relevant for the OKR & Habit Trackers
okr_data, okr_start_date, okr_end_date = get_okr_data(OKR_NOTE, vault)
okrs = [k for k, v in sorted(
    okr_data.items(), key=lambda item: item[1]['priority'])]
okr_pivot_data = get_okr_pivot_data(
    okr_data, okr_start_date, okr_end_date)
habit_data = {habit: get_habit_tracker_data(habit, CRITERIA[i], dt.date.fromisoformat(
    START_DATES[i]), vault) for i, habit in enumerate(HABITS)}

# # For efficient testing & debugging - Disable in production
# with open('all_data.pkl', 'rb') as f:
#     vault, okr_data, okr_start_date, okr_end_date, okr_pivot_data, habit_data = \
#         pickle.load(f)

# Create the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
           requests_pathname_prefix=PATH_PREFIX,
           routes_pathname_prefix=PATH_PREFIX)
app.title = "My Productivity Dashboard"
server = app.server

# Define the layout
okr_layout = html.Div(children=[
    html.H1('OKR Tracker - ' + OKR_NOTE, style={'textAlign': 'center'}),
    dcc.Link('Go to Habit Tracker', href='/habit'),
    html.Div(children=[
        dcc.Graph(id='graph-content-' + okr,
                  figure=get_okr_graph_data(okr, okr_data, okr_pivot_data))
        for okr in okrs
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
        dcc.Dropdown(HABITS, HABITS[0], id='dropdown-selection'),
    ]),
    dcc.Graph(id='graph-content-habit'),
    dcc.Graph(id='graph-content-habit-weekly'),
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
#     style = {
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
    # html.Div(id='page-content',
    #          style={"margin-left": "220px", "padding": "20px"}),
    html.Button('Reload Data', id='reload-button', n_clicks=0,
                className="btn btn-primary"),
    html.Div(okr_layout, id='okr-container', style={'display': 'none'}),
    html.Div(habit_layout, id='habit-container', style={'display': 'none'})
], style={'fontFamily': 'Open Sans, sans-serif'})


# Callbacks to update the page / data based on URL / link / button clicks
@ app.callback(
    [Output('okr-container', 'style'),
     Output('habit-container', 'style')],
    Input('url', 'pathname')
)
def display_page_callback(pathname):
    return display_page(pathname)


@ app.callback(
    [Output('graph-content-habit', 'figure', allow_duplicate=True),
     Output('graph-content-habit-weekly', 'figure', allow_duplicate=True)],
    Input('dropdown-selection', 'value'), prevent_initial_call='initial_duplicate'
)
def update_graph(value):
    return get_habit_graph_data(value, habit_data)


@ app.callback(
    [Output('graph-content-habit', 'figure', allow_duplicate=True),
     Output('graph-content-habit-weekly', 'figure', allow_duplicate=True)] +
    [Output('graph-content-' + okr, 'figure')
     for okr in okr_pivot_data.okr.unique()],
    [Input('reload-button', 'n_clicks'),
     Input('dropdown-selection', 'value')], prevent_initial_call=True
)
def reload_data(n_clicks, value):
    global okr_data, okr_start_date, okr_end_date, okr_pivot_data, habit_data
    vault = otools.Vault(VAULT_LOC).connect().gather()
    okr_data, okr_start_date, okr_end_date = get_okr_data(OKR_NOTE, vault)
    okr_pivot_data = get_okr_pivot_data(
        okr_data, okr_start_date, okr_end_date)
    habit_data = {habit: get_habit_tracker_data(
        habit, CRITERIA[i], dt.date.fromisoformat(START_DATES[i]), vault)
        for i, habit in enumerate(HABITS)}
    return list(get_habit_graph_data(value, habit_data)) + \
        [get_okr_graph_data(okr, okr_data, okr_pivot_data)
         for okr in okr_pivot_data.okr.unique()]


# Run the app
if __name__ == '__main__':
    if ENV == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True)

# TODO: Description of the first 3 PRs contain info missing from their respective merge commit messages
