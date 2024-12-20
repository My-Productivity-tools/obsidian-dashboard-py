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


def display_page(pathname):
    if pathname == '/okr' or pathname == '/':
        return {'display': 'block'}, {'display': 'none'}
    elif pathname == '/habit':
        return {'display': 'none'}, {'display': 'block'}
    return {'display': 'none'}, {'display': 'none'}
