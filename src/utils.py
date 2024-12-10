from markdown_it import MarkdownIt
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pathlib
import os
from src.note_utils import parse_note_for_tasks
from treelib import Tree
from datetime import datetime as dt

md = MarkdownIt()
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
DAILY_NOTES_LOC = pathlib.Path(os.getenv('DAILY_NOTES_LOC'))


def get_okr_data(okr_note, vault):
    # TODO: Generate chart data for each OKR

    okr_note = '2024 Nov'

    front_matter = vault.get_front_matter(okr_note)
    okr_start_date = front_matter['start_date']
    okr_end_date = front_matter['end_date']

    okr_info = parse_okr_note(okr_note, vault)

    for obj in okr_info.keys():
        for kr in okr_info[obj]['kr_info'].keys():
            okr_info[obj]['kr_info'][kr]['data'] = get_kr_tagged_tasks(
                okr_info[obj]['kr_info'][kr]['okr_tag'], vault)
    return okr_info, okr_start_date, okr_end_date


def parse_okr_note(okr_note, vault):
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
    okr_info = {m[1].strip(): {'name': m[2].strip(), 'kr_info': {}}
                for m in obj_matches}

    # Get the Key Results
    kr_pattern = r'(O\d+)\s(KR\d+):(.+)'
    kr_elem_matches = [e for e in soup.findAll(
        'h3', recursive=False) if re.search(kr_pattern, e.text)]
    kr_matches = [re.search(kr_pattern, e.text)
                  for e in soup.findAll('h3', recursive=False)]

    criteria_pattern = r'\[criteria::(.+?)\]\s*(?:\(keywords::(.+?)\))?'
    criteria_matches = [re.search(
        criteria_pattern, e.next_sibling.next_sibling.text) for e in kr_elem_matches]

    for i, match in enumerate(kr_matches):
        print(i)
        okr_info[match[1]]['kr_info'][match[2]] = {
            'name': match[3].strip(),
            'okr_tag': '[[' + okr_note + '#' +
            match[0].replace(':', '').replace('[', '').replace(']', '') + ']]',
            'criteria': criteria_matches[i][1].strip()
        }
        if criteria_matches[i][2] is not None:
            okr_info[match[1]]['kr_info'][match[2]]['keywords'] = ast.literal_eval(
                criteria_matches[i][2].strip())
    return okr_info


def get_kr_tagged_tasks(okr_tag, vault):
    note_metadata = vault.get_note_metadata()
    tasks = Tree()
    tasks.create_node("Master Root", 'master_root')
    for note in vault.md_file_index.keys():
        print(note)
        if note_metadata.loc[note_metadata.index == note, 'note_exists'].iloc[0]:
            note_tasks = \
                parse_note_for_tasks(note, vault, okr_tag)
            tasks.paste('master_root', note_tasks)
            tasks.link_past_node('root')
    return tasks


def get_daily_notes_tasks(vault):
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
        title = task.data['title']
        date_string = task.data['file_name'].split(' ')[0]
        event_data = read_event(date_string, title)
        if event_data is not None:
            task.data.update(event_data)

    return tasks


def read_event(date_string, title):
    # pattern_event = r'\b(\d{1,2}:\d{2}\s?(AM|PM)\s?)-(\s?\d{1,2}:\d{2}\s?(AM|PM))'
    pattern_event = r'^\b(\d{1,2}(:\d{2})?\s*(AM|PM)?)\s*-\s*(\d{1,2}(:\d{2})?\s*(AM|PM)?)\b'
    match = re.search(pattern_event, title)

    # Start time
    if match is not None:
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
        event_start = dt.strptime(
            date_string + ' ' + str(hours) + ':' + str(minutes), '%Y-%m-%d %H:%M')

        # End time
        minutes = int(match[5][1:])
        hours = int(match[4].split(':')[0])
        am_pm = match[6]
        if am_pm is not None:
            if am_pm == 'PM' and hours != 12:
                hours += 12
            elif am_pm == 'AM' and hours == 12:
                hours = 0
        event_end = dt.strptime(
            date_string + ' ' + str(hours) + ':' + str(minutes), '%Y-%m-%d %H:%M')

        if event_end < event_start:  # If the event ends on the next day
            event_end += dt.timedelta(days=1)
        duration = (event_end - event_start).total_seconds()/3600

        return {'event_start': event_start, 'event_end': event_end, 'duration': duration}
    else:
        return None
