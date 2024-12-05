# from mistune.plugins.task_lists import task_lists
# import mistune
# import markdown as md
from markdown_it import MarkdownIt
import pypandoc
import json
from bs4 import BeautifulSoup
from itertools import chain

# markdown = mistune.create_markdown(plugins=['task_lists'])
# mdx = md.Markdown(extensions=['pymdownx.tasklist'])
md = MarkdownIt()


def parse_note_via_html(note, vault):
    note = 'Deep Learning'
    note_path = VAULT_LOC / vault.md_file_index[note]
    with open(note_path, 'r', encoding="utf8") as f:
        text = f.read()
    # html = markdown(text)
    # html = md.markdown(text, extensions=['pymdownx.task_lists'])
    html = md.render(text)
    soup = BeautifulSoup(html, 'html.parser')
    return parse_html_for_tasks(soup)


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
    task['status'] = status_map.get(text[:3], None)

    task['tags'] = [word.strip('#') for word in task['title'].split() 
                    if word.startswith('#')]
    
    task_types = [tag for tag in task['tags'] if tag in ['epic', 'story', 'task']]
    if len(task_types) == 1:
        task['type'] = task_types[0]
    elif len(task_types) == 0:
        task['type'] = 'todo'
    else:
        print(elem)
        raise ValueError(f"Multiple task types found: {task_types}")
    
    # TODO: Add the required fields - priority,
    # done date, scheduled date, due date, created date, start date, cancelled 
    # date etc.
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