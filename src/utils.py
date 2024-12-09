from markdown_it import MarkdownIt
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pathlib
import os
from src.note_utils import parse_note_for_tasks
from treelib import Tree
from datetime import datetime

md = MarkdownIt()
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
DAILY_NOTES_LOC = pathlib.Path(os.getenv('DAILY_NOTES_LOC'))


def get_okr_data(okr_note, vault):
    # okr_note = '2024 Nov'

    # front_matter = vault.get_front_matter(okr_note)
    # okr_start_date = front_matter['start_date']
    # okr_end_date = front_matter['end_date']

    okr_info = parse_okr_note(okr_note, vault)
    okr_data = get_kr_tagged_tasks(okr_info, vault)
    return okr_data  # okr_start_date, okr_end_date


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
    kr_matches = [re.search(kr_pattern, e.text)
                  for e in soup.findAll('h3', recursive=False)]
    for match in kr_matches:
        okr_info[match[1]]['kr_info'][match[2]] = {
            'name': match[3].strip(),
            'okr_tag': '[[' + okr_note + '#' + match[0].replace(':', '')
                       .replace('[', '').replace(']', '') + ']]'
        }
    return okr_info


def get_kr_tagged_tasks(okr_info, vault):
    okr_data = okr_info.copy()

    note_metadata = vault.get_note_metadata()
    for obj in okr_data.keys():
        print(obj)
        for kr in okr_data[obj]['kr_info'].keys():
            print(kr)
            tasks = Tree()
            tasks.create_node("Master Root", 'master_root')
            for note in vault.md_file_index.keys():
                print(note)
                if note_metadata.loc[note_metadata.index == note, 'note_exists'].iloc[0]:
                    note_tasks = \
                        parse_note_for_tasks(
                            note, vault, okr_data[obj]['kr_info'][kr]['okr_tag'])
                    tasks.paste('master_root', note_tasks)
                    tasks.link_past_node('root')
            okr_data[obj]['kr_info'][kr]['kr_data'] = tasks
    return okr_data


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

    # TODO: Extract duration from all events
    for task in tasks.all_nodes()[1:]:
        title = task.data['title']
        date_string = task.data['file_name'].split(' ')[0]
        task.data['event_start'], task.data['event_end'], task.data['duration'] = read_event(
            date_string, title)

    return tasks


def read_event(date_string, title):
    # pattern_event = r'\b(\d{1,2}:\d{2}\s?(AM|PM)\s?)-(\s?\d{1,2}:\d{2}\s?(AM|PM))'
    pattern_event = r'\b(\d{1,2}(:\d{2})?\s*(AM|PM)?)\s*-\s*(\d{1,2}(:\d{2})?\s*(AM|PM)?)\b'
    match = re.search(pattern_event, title)

    # Start time
    minutes = int(match[2][1:])
    hours = int(match[1].split(':')[0])
    am_pm = match[3]
    if am_pm is not None:
        if am_pm == 'PM' and hours != 12:
            hours += 12
        elif am_pm == 'AM' and hours == 12:
            hours = 0
    event_start = datetime.strptime(date_string + ' ' +
                                    str(hours) + ':' + str(minutes), '%Y-%m-%d %H:%M')

    # End time
    minutes = int(match[5][1:])
    hours = int(match[4].split(':')[0])
    am_pm = match[6]
    if am_pm is not None:
        if am_pm == 'PM' and hours != 12:
            hours += 12
        elif am_pm == 'AM' and hours == 12:
            hours = 0
    event_end = datetime.strptime(date_string + ' ' +
                                  str(hours) + ':' + str(minutes), '%Y-%m-%d %H:%M')

    duration = (event_end - event_start).total_seconds()/3600

    # TODO: Account for the use case for an event extending into the next day

    return event_start, event_end, duration


# TODO: OKR-specific steps to use relevant data, including criteria in OKR note
# TODO: Generate chart data for each OKR
