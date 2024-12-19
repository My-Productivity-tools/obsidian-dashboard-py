from markdown_it import MarkdownIt
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pathlib
import os
from src.note_utils import parse_note_for_tasks, filter_daily_tasks
from treelib import Tree
import datetime as dt
import ast
import pandas as pd
from itertools import product

md = MarkdownIt()
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
DAILY_NOTES_LOC = pathlib.Path(os.getenv('DAILY_NOTES_LOC'))
CRITERIA_STORY_POINTS = os.getenv('CRITERIA_STORY_POINTS')
CRITERIA_COUNT = os.getenv('CRITERIA_COUNT')
CRITERIA_DURATION = os.getenv('CRITERIA_DURATION')


def get_okr_pivot_data(okr_data, okr_start_date, okr_end_date):
    """Get the chart data for a specific OKR cycle.

    Args:
        okr_note (str): Name of the OKR note in the vault.
        vault (Vault): The vault object containing the OKR note and data.

    Returns:
        DataFrame: DataFrame object containing the chart data for the OKR cycle.
    """
    date_list = pd.date_range(okr_start_date, okr_end_date)
    today = dt.datetime.today()
    chart_data = pd.DataFrame(
        list(product(okr_data.keys(), date_list)), columns=['okr', 'date'])

    for okr in okr_data.keys():
        score_list = []
        node_list = okr_data[okr]['data'].all_nodes()[1:]
        if okr_data[okr]['criteria'] == CRITERIA_COUNT:
            for date in date_list[date_list <= today]:
                score_list.append(
                    len([n for n in node_list if n.data['file_name_date'] == date]))
        elif okr_data[okr]['criteria'] == CRITERIA_DURATION:
            for date in date_list[date_list <= today]:
                score_list.append(sum([n.data.get(
                    'duration', 0) for n in node_list if n.data['file_name_date'] == date]))
        elif okr_data[okr]['criteria'] == CRITERIA_STORY_POINTS:
            for date in date_list[date_list <= today]:
                score_list.append(sum([n.data.get('Story Points', 0) for
                                       n in node_list if 'Done Date' in n.data
                                       and n.data['Done Date'] == date and
                                       n.data['status'] != 'Cancelled']))
            okr_data[okr]['target'] = sum(
                [n.data.get('Story Points') for n in node_list if n.data['status'] != 'Cancelled'])

        chart_data.loc[chart_data['okr'] == okr, 'score'] = score_list + \
            [None] * (len(date_list) - len(score_list))
        chart_data.loc[chart_data['okr'] == okr, 'target'] = [
            ((i+1) * okr_data[okr]['target']) / len(date_list) for i, date in enumerate(date_list)]

    chart_data['score'] = chart_data.groupby(
        'okr')['score'].transform(pd.Series.cumsum)
    chart_data['target_70_pct'] = chart_data['target'] * 0.7

    return chart_data


def get_okr_data(okr_note, vault):
    """Get all relevant data for a specific OKR cycle.

    Args:
        okr_note (str): Name of the OKR note in the vault.
        vault (Vault): The vault object containing the OKR note.

    Returns:
        dict: Dict object containing the OKR info & data, uses Tree objects for
         storing the KR data.
    """
    # okr_note = '2024 Nov'
    front_matter = vault.get_front_matter(okr_note)
    okr_start_date = front_matter['start_date']
    okr_end_date = front_matter['end_date']

    # Get the KR info from the OKR note
    okr_data = parse_okr_note(okr_note, vault)

    # Get the task / event / action data for each KR
    daily_notes_tasks = get_daily_notes_tasks(vault)
    for okr in okr_data.keys():
        keywords = okr_data[okr].get('keywords')
        if okr_data[okr]['criteria'] == CRITERIA_STORY_POINTS:
            okr_data[okr]['data'] = get_kr_tagged_tasks(
                okr_data[okr]['okr_tag'], vault)
        elif okr_data[okr]['criteria'] == CRITERIA_COUNT:
            okr_data[okr]['data'] = filter_daily_tasks(
                daily_notes_tasks, keywords, okr_start_date, okr_end_date)
        elif okr_data[okr]['criteria'] == CRITERIA_DURATION:
            okr_data[okr]['data'] = filter_daily_tasks(
                daily_notes_tasks, keywords, okr_start_date, okr_end_date)
    return okr_data, okr_start_date, okr_end_date


def parse_okr_note(okr_note, vault):
    """Get all the relevant OKR info from the OKR note for a specific OKR cycle.

    Args:
        okr_note (str): Name of the OKR note in the vault.
        vault (Vault): The vault object containing the OKR note.

    Returns:
        dict: Dict object containing the OKR info.
    """
    # Get the HTML
    okr_note_path = VAULT_LOC / vault.md_file_index[okr_note]
    with open(okr_note_path, 'r', encoding="utf-8") as f:
        text = f.read()
    html = md.render(text)
    soup = BeautifulSoup(html, 'html.parser')

    # Get the Objectives
    obj_pattern = r'(O\d+):(.+)'
    obj_matches = [re.search(obj_pattern, e.text)
                   for e in soup.findAll('h1', recursive=False)]
    obj_map = {m[1].strip(): m[2].strip() for m in obj_matches}

    # Get the Key Results
    kr_pattern = r'(O\d+)\s(KR\d+):(.+)'
    kr_elem_matches = [e for e in soup.findAll(
        'h3', recursive=False) if re.search(kr_pattern, e.text)]
    kr_matches = [re.search(kr_pattern, e.text)
                  for e in soup.findAll('h3', recursive=False)]

    # Get the KR Criteria, Keywords and Targets
    criteria_pattern = r'\[criteria::(.+?)\]\s*(?:\[target::(.+?)\])?\s*(?:\(keywords::(.+?)\))?'
    criteria_matches = [re.search(
        criteria_pattern, e.next_sibling.next_sibling.text) for e in kr_elem_matches]

    # Create okr_info
    okr_info = {}
    for i, match in enumerate(kr_matches):
        print(i)
        okr = match[1] + ' ' + match[2] + ' ' + match[3].strip()
        okr_info[okr] = {'obj_key': match[1], 'obj_name': obj_map[match[1]],
                         'kr_key': match[2], 'kr_name': match[3].strip(),
                         'okr_tag': '[[' + okr_note + '#' + match[0].replace(':', '').replace('[', '').replace(']', '') + ']]',
                         'criteria': criteria_matches[i][1].strip()}
        if criteria_matches[i][2] is not None:
            okr_info[okr]['target'] = float(criteria_matches[i][2].strip())
        if criteria_matches[i][3] is not None:
            okr_info[okr]['keywords'] = ast.literal_eval(
                criteria_matches[i][3].strip())

    return okr_info


def get_habit_tracker_data(habit, criteria, start_date, vault):
    today = dt.date.today()
    dates = pd.date_range(start_date, today)

    daily_notes_tasks = get_daily_notes_tasks(vault)
    habit_tasks = filter_daily_tasks(
        daily_notes_tasks, [habit], start_date, today)
    if criteria == CRITERIA_COUNT:
        scores = [len([n for n in habit_tasks.all_nodes()[1:]
                      if n.data['file_name_date'] == date.date()]) for date in dates]
    elif criteria == CRITERIA_DURATION:
        scores = [sum([n.data.get('duration', 0) for n in habit_tasks.all_nodes()[
                      1:] if n.data['file_name_date'] == date.date()]) for date in dates]

    scores_df = pd.DataFrame({'date': dates, 'score': scores})
    scores_df['week'] = scores_df['date'].dt.to_period('W').dt.start_time
    return scores_df


# Functions to get the KR data for different KR criteria types
def get_kr_tagged_tasks(okr_tag, vault):
    """Get KR tagged tasks from the vault for KRs that depends on OKR tags.

    Args:
        okr_tag (str): The OKR tag used in the tasks to mark for a specific OKR.
        vault (Vault): The vault object containing the OKR note and the tasks.

    Returns:
        Tree: Tasks tree object containing the tasks tagged for a specific OKR.
    """
    note_metadata = vault.get_note_metadata()
    tasks = Tree()
    tasks.create_node("Master Root", 'master_root')
    for note in vault.md_file_index.keys():
        print(note)
        if note_metadata.loc[note_metadata.index == note, 'note_exists'].iloc[0]:
            note_tasks = parse_note_for_tasks(note, vault, okr_tag)
            tasks.paste('master_root', note_tasks)
            tasks.link_past_node('root')
    return tasks


def get_daily_notes_tasks(vault):
    """Get all the tasks from the daily notes.

    Args:
        vault (Vault): The vault object containing the daily notes.

    Returns:
        Tree: Tasks tree object containing the tasks from the daily notes.
    """
    # Parse all Daily notes for all kinds of tasks / events
    note_metadata = vault.get_note_metadata()
    tasks = Tree()
    tasks.create_node("Master Root", 'master_root')
    for note in vault.md_file_index.keys():
        print(note)
        note_path = note_metadata.loc[note_metadata.index ==
                                      note, 'abs_filepath'].iloc[0]
        if note_path.is_relative_to(DAILY_NOTES_LOC):
            note_tasks = parse_note_for_tasks(note, vault)
            tasks.paste('master_root', note_tasks)
            tasks.link_past_node('root')

    # Extract duration from all events
    for task in tasks.all_nodes()[1:]:
        date_string = task.data['file_name'].split()[0]
        task.data['file_name_date'] = dt.date.fromisoformat(date_string)
        event_data = read_event(date_string, task.data['title'])
        if event_data is not None:
            task.data.update(event_data)

    return tasks


def read_event(date_string, title):
    """Read the event start, end date-times from the title of a task if it is an event.

    Args:
        date_string (str): The date string in ISO format of the task/event.
        title (str): The title of the task.

    Returns:
        dict: A dict containing the event start & end date-times and duration.
    """
    pattern_event = r'^\b(\d{1,2}(:\d{2})?\s*(AM|PM)?)\s*-\s*(\d{1,2}(:\d{2})?\s*(AM|PM)?)\b'
    match = re.search(pattern_event, title)

    if match is not None:
        # Extract the event start time
        if match[2] is not None:
            minutes = int(match[2][1:])
        else:
            minutes = 0
        hours = int(match[1].split(':')[0].split()[0])
        am_pm = match[3]
        if am_pm is not None:
            if am_pm == 'PM' and hours != 12:
                hours += 12
            elif am_pm == 'AM' and hours == 12:
                hours = 0
        event_start = dt.datetime.strptime(
            date_string + ' ' + str(hours) + ':' + str(minutes), '%Y-%m-%d %H:%M')

        # Extract the event end time
        if match[5] is not None:
            minutes = int(match[5][1:])
        else:
            minutes = 0
        hours = int(match[4].split(':')[0].split()[0])
        am_pm = match[6]
        if am_pm is not None:
            if am_pm == 'PM' and hours != 12:
                hours += 12
            elif am_pm == 'AM' and hours == 12:
                hours = 0
        event_end = dt.datetime.strptime(
            date_string + ' ' + str(hours) + ':' + str(minutes), '%Y-%m-%d %H:%M')

        # If the event ends on the next day
        if event_end < event_start:
            event_end += dt.timedelta(days=1)
        duration = (event_end - event_start).total_seconds()/3600

        return {'event_start': event_start, 'event_end': event_end, 'duration': duration}
    else:
        return None
