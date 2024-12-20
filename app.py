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

# Load the environment variables
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
CRITERIA_STORY_POINTS = os.getenv('CRITERIA_STORY_POINTS')
CRITERIA_COUNT = os.getenv('CRITERIA_COUNT')
CRITERIA_DURATION = os.getenv('CRITERIA_DURATION')

# Generate the vault to use
vault = otools.Vault(VAULT_LOC).connect().gather()

# Define the requirements for the OKR & Habit Tracker
okr_note = '2024 Dec'
habits = ['#gratitude', 'gratitude', 'self-compassion']
criteria = [CRITERIA_COUNT, CRITERIA_COUNT, CRITERIA_DURATION]
start_dates = ['2024-11-16', '2024-11-16',
               '2024-02-23']  # Start dates for each habit

# # For efficient testing & debugging - Disable in production
# with open('all_data.pkl', 'rb') as f:
#     vault, okr_data, okr_start_date, okr_end_date, okr_pivot_data, habit_data = \
#         pickle.load(f)

# Get the data relevant for the OKR & Habit Trackers
okr_data, okr_start_date, okr_end_date = get_okr_data(okr_note, vault)
okr_pivot_data = get_okr_pivot_data(
    okr_data, okr_start_date, okr_end_date)
habit_data = {habit: get_habit_tracker_data(habit, criteria[i], dt.date.fromisoformat(
    start_dates[i]), vault) for i, habit in enumerate(habits)}


# Functions to generate graph data for the OKR & Habit Trackers
def get_okr_graph_data(okr, okr_data, okr_pivot_data):
    """Get graph data to be used in okr_layout

    Args:
        okr (str): OKR name
        okr_data (dict): OKR data
        okr_pivot_data (DataFrame): OKR pivot data to be used to generate OKR chart data

    Returns:
        dict: Graph data to be used in okr_layout
    """
    return {'data': [
        {'x': okr_pivot_data[okr_pivot_data.okr == okr]['date'],
         'y': okr_pivot_data[okr_pivot_data.okr == okr][col],
         'type': 'line', 'name': name}
        for col, name in zip(['score', 'target_70_pct', 'target'],
                             ['score', '70% of target', 'target'])],
        'layout': {'title': okr, 'showlegend': False, 'font': {'size': 18},
                   'yaxis': {'title': okr_data[okr]['criteria']}}}


def get_habit_graph_data(habit, habit_data):
    """Get graph data to be used in habit_layout

    Args:
        habit (str): Habit name
        habit_data (dict): Habit data - dict of DataFrame objects

    Returns:
        dict: Graph data to be used in habit_layout
    """
    df = habit_data[habit]
    return {'data': [
        {'x': df['date'], 'y': df['score'],
         'type': 'bar', 'name': 'score'},
    ], 'layout': {'title': habit if habit.startswith('#') else
                  habit.title(), 'showlegend': False, 'font': {'size': 18},
                  'yaxis': {'title': 'count'}}}, \
        {'data': [
            {'x': df['week'].unique(), 'y': df.groupby('week')['score'].sum(),
             'type': 'bar', 'name': 'score'},
        ], 'layout': {'title': habit if habit.startswith('#') else
                      habit.title(), 'showlegend': False, 'font': {'size': 18},
                      'yaxis': {'title': 'count'}}}


# Create the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "My Productivity Dashboard"

# Define the layout
okr_layout = html.Div(children=[
    html.H1('OKR Tracker - ' + okr_note, style={'textAlign': 'center'}),
    dcc.Link('Go to Habit Tracker', href='/habit'),
    html.Div(children=[
        dcc.Graph(id='graph-content-' + okr,
                  figure=get_okr_graph_data(okr, okr_data, okr_pivot_data))
        for okr in okr_pivot_data.okr.unique()
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
    # html.Div(id='page-content',
    #          style={"margin-left": "220px", "padding": "20px"}),
    html.Button('Reload Data', id='reload-button', n_clicks=0,
                className="btn btn-primary"),
    html.Div(okr_layout, id='okr-container', style={'display': 'none'}),
    html.Div(habit_layout, id='habit-container', style={'display': 'none'})
], style={'fontFamily': 'Open Sans, sans-serif'})


# Callbacks to update the page / data based on URL / link / button clicks
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


@app.callback(
    [Output('graph-content-habit', 'figure', allow_duplicate=True),
     Output('graph-content-habit-weekly', 'figure', allow_duplicate=True)],
    Input('dropdown-selection', 'value'), prevent_initial_call='initial_duplicate'
)
def update_graph(value):
    return get_habit_graph_data(value, habit_data)


@app.callback(
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
    okr_data, okr_start_date, okr_end_date = get_okr_data(okr_note, vault)
    okr_pivot_data = get_okr_pivot_data(
        okr_data, okr_start_date, okr_end_date)
    habit_data = {habit: get_habit_tracker_data(
        habit, criteria[i], dt.date.fromisoformat(start_dates[i]), vault)
        for i, habit in enumerate(habits)}
    return list(get_habit_graph_data(value, habit_data)) + \
        [get_okr_graph_data(okr, okr_data, okr_pivot_data)
            for okr in okr_pivot_data.okr.unique()]


# Run the app
if __name__ == '__main__':
    app.run(debug=True)

# TODO: Description of the first 3 PRs contain info missing from their respective merge commit messages
