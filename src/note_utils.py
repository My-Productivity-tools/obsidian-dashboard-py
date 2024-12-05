from markdown_it import MarkdownIt
import pypandoc
import json
from bs4 import BeautifulSoup
from itertools import chain
import json
import re

md = MarkdownIt()


def parse_note_via_html(note, vault):
    note = 'Deep Learning'
    note_path = VAULT_LOC / vault.md_file_index[note]
    with open(note_path, 'r', encoding="utf-8") as f:
        text = f.read()
    html = md.render(text)
    soup = BeautifulSoup(html, 'html.parser')
    tasks = parse_html_for_tasks(soup)
    with open('tasks.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=4, separators=(',', ': '))
    return tasks


def parse_html_for_tasks(elem):
    """
    Recursively filters the element tree to retain only the required tasks 
    while retaining the tree structure.

    :param elem: A HTML element tree that needs to be parsed for tasks.
    :return: A new HTML element tree with only the required tasks.
    """
    # Filter the children recursively
    filtered_children = list(chain.from_iterable(parse_html_for_tasks(child) 
                                                 for child in elem.findChildren(recursive=False)))

    # If the current node is a required task type, include it
    if elem.name == "li" and elem.text.startswith('['):
        return [convert_to_task(elem, filtered_children)]
    else:
        return filtered_children


def convert_to_task(elem, children=[]):
    """
    Converts a HTML element into a task object.

    :param elem: A HTML element to be converted into a task.
    :return: A task object.
    """
    task = {}
    task['raw_text'] = elem.text  # storing raw text
        
    for child in elem.find_all():
        if child.name not in ['a', 'span', 'strong']:
            child.decompose()
    text = elem.get_text()
    task['title'] = text[3:].strip()
    status_map = {
        '[ ]': 'Todo',
        '[x]': 'Done',
        '[/]': 'In Progress',
        '[-]': 'Cancelled', 
        '[|]': 'Blocked', 
    }
    priority_map = {  # Normal priority is when no symbol is specified
        '\\u23ec': 'Lowest', 
        '\\ud83d\\udd3d': 'Low', 
        '\\ud83d\\udd3c': 'Medium', 
        '\\u23eb': 'High', 
        '\\ud83d\\udd3a': 'Highest'
    }
    dates_map = {
        '\\u2795': 'Created Date', 
        '\\ud83d\\udeeb': 'Started Date', 
        '\\u23f3': 'Scheduled Date', 
        '\\ud83d\\udcc5': 'Due Date', 
        '\\u2705': 'Done Date', 
        '\\u274c': 'Cancelled Date'
    }
    task['status'] = status_map.get(text[:3], None)

    task['tags'] = [word.strip('#') for word in task['title'].split() 
                    if word.startswith('#')]
    title_words = json.dumps(task['title']).strip('"').split()
    task['fields'] = [word for word in title_words if word.startswith('\\u')]
    
    priority = [priority_map.get(field) for field in task['fields'] 
                if field in priority_map]
    task['priority'] = priority[0] if priority else None

    date_fields_utf = [field for field in task['fields'] if field in dates_map]
    for date_field in date_fields_utf:
        task[dates_map.get(date_field)] = title_words[title_words.index(date_field)+1]
    
    pattern_okr = r'\(([a-zA-Z\s]+)::(.+)\)'
    matches_okr = re.findall(pattern_okr, task['title'])
    for match in matches_okr:
        task[match[0].strip()] = match[1].strip()
    task['title'] = re.sub(pattern_okr, '', task['title']).strip()

    pattern_dv = r'[\[\(]([a-zA-Z\s]+)::(.+)[\]\)]'
    matches_dv = re.findall(pattern_dv, task['title'])
    for match in matches_dv:
        key, val = match[0].strip(), match[1].strip()
        if key in ['Story Points', 'Duration']:
            val = float(val)
        task[key] = val

    task_types = [tag for tag in task['tags'] if tag in ['epic', 'story', 'task']]
    if len(task_types) == 1:
        task['type'] = task_types[0]
    elif len(task_types) == 0:
        task['type'] = 'todo'
    else:
        print(elem)
        raise ValueError(f"Multiple task types found: {task_types}")
    
    # TODO: Add Dataview fields - okr, Story Points, duration etc. 
    # TODO: Add additional fields if required - description
    task['children'] = children
    return task


def parse_note_via_json(note, vault):
    note = '2024 Oct'
    note_path = VAULT_LOC / vault.md_file_index[note]
    text_dict = json.loads(pypandoc.convert_file(note_path, to='json'))


def parse_note_via_text(note, vault):
    note = '2024 Oct'
    note_path = VAULT_LOC / vault.md_file_index[note]
    text = vault.get_source_text(note)  # Doesn't identify bullet points as separate lines
    lines = [line for line in text.split('\n') if line.strip()]
