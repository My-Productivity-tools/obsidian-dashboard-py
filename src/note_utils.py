from markdown_it import MarkdownIt
from bs4 import BeautifulSoup
import json
import re
from treelib import Node, Tree
from dotenv import load_dotenv
import pathlib
import os
import datetime as dt

md = MarkdownIt()
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))
# Maps for different fields
STATUS_MAP = {
    '[ ]': 'Todo',
    '[x]': 'Done',
    '[/]': 'In Progress',
    '[-]': 'Cancelled',
    '[|]': 'Blocked',
}
PRIORITY_MAP = {  # Normal priority is when no symbol is specified
    '\\u23ec': 'Lowest',
    '\\ud83d\\udd3d': 'Low',
    '\\ud83d\\udd3c': 'Medium',
    '\\u23eb': 'High',
    '\\ud83d\\udd3a': 'Highest'
}
DATES_MAP = {
    '\\u2795': 'Created Date',
    '\\ud83d\\udeeb': 'Started Date',
    '\\u23f3': 'Scheduled Date',
    '\\ud83d\\udcc5': 'Due Date',
    '\\u2705': 'Done Date',
    '\\u274c': 'Cancelled Date'
}


def parse_note_for_tasks(note, vault, okr=None):
    """Parse any note in the vault to get all its tasks.

    Args:
        note (str): Name of the note in the vault.
        vault (Vault): The vault object containing the note.
        okr (str, optional): The OKR tag used in the tasks to mark for a specific OKR.
            Defaults to None.

    Returns:
        Tree: Tasks tree object containing the tasks from the note.
    """
    note_path = VAULT_LOC / vault.md_file_index[note]
    with open(note_path, 'r', encoding="utf-8") as f:
        text = f.read()
    html = md.render(text)
    soup = BeautifulSoup(html, 'html.parser')
    task_tree = Tree()
    task_tree.create_node("Root", 'root')
    # Passing an empty Tree with just the root node, it'll be filled with the tasks by the function
    parse_html_for_tasks(soup, task_tree, 'root', note, okr)
    return task_tree


def parse_html_for_tasks(elem, task_tree, root, note, okr=None):
    """Recursively filters the element tree to retain only the required tasks
    while retaining the tree structure.

    Args:
        elem (BeautifulSoup): A HTML element tree that needs to be parsed for tasks.
        task_tree (Tree): A basic Tree object with just the master / root node.
        root (str): Identifier of the root node in the task tree.
        note (str): Name of the note in the vault.
        okr (str, optional): The OKR tag used in the tasks to mark for a specific OKR.
            Defaults to None.
    """
    # Recursion just to one level below in this step
    children = elem.findChildren(recursive=False)

    # It is a todo/task if it is a Checkbox
    if elem.name == "li" and elem.text.startswith('['):
        task = convert_to_task(elem.__copy__(), note)
        if okr is not None:
            # Check if the task is marked for the OKR
            if 'okr' in task.data and task.data['okr'] == okr:
                task_tree.add_node(task, root)
                # Children SHOULD NOT be checked for OKR if the parent is marked for the OKR
                [parse_html_for_tasks(
                    child, task_tree, task.identifier, note) for child in children]
            else:  # Skip the task if it is not marked for the OKR
                [parse_html_for_tasks(child, task_tree, root, note, okr)
                 for child in children]
        else:  # If OKR check is not needed, just add the task and parse the children
            task_tree.add_node(task, root)
            [parse_html_for_tasks(
                child, task_tree, task.identifier, note, okr) for child in children]
    else:  # If it is not a checkbox item, just parse the children
        [parse_html_for_tasks(child, task_tree, root, note, okr)
         for child in children]


def convert_to_task(elem, note):
    """Converts a HTML element into a task object.

    Args:
        elem (Tag): A HTML element to be converted into a task.
        note (str): Name of the note in the vault containing elem.

    Raises:
        ValueError: If the task text contains multiple task types, perhaps due to its child elements.

    Returns:
        dict: Dict object containing the task details.
    """
    # TODO: Consider refactoring this function to make it more readable and maintainable
    # TODO: Add comments in this function body
    task_node = Node()
    task = {}
    task['raw_text'] = elem.text  # storing raw text

    # Extract task title
    for child in elem.find_all():
        if child.name not in ['a', 'span', 'strong']:
            child.decompose()
    text = elem.get_text()
    md_comment_pattern = r'%%(.+)[%%]?'
    text = re.sub(md_comment_pattern, '', text, flags=re.DOTALL)
    task['title'] = text[3:].strip()

    task['status'] = STATUS_MAP.get(text[:3], None)

    task['tags'] = [word.strip('#') for word in task['title'].split()
                    if word.startswith('#')]
    title_words = json.dumps(task['title']).strip('"').split()
    task['fields'] = [word for word in title_words if word.startswith('\\u')]

    # Priority field (Tasks Obsidian plugin)
    priority = [PRIORITY_MAP.get(field) for field in task['fields']
                if field in PRIORITY_MAP]
    task['priority'] = priority[0] if priority else None

    # Date fields (Tasks Obsidian plugin)
    date_fields_utf = [field for field in task['fields'] if field in DATES_MAP]
    for date_field in date_fields_utf:
        task[DATES_MAP.get(date_field)] = dt.datetime.fromisoformat(
            title_words[title_words.index(date_field)+1])

    # OKR field (Dataview Obsidian plugin)
    pattern_okr = r'\(([a-zA-Z\s]+)::(.+)\)'
    matches_okr = re.findall(pattern_okr, task['title'])
    for match in matches_okr:
        task[match[0].strip()] = match[1].strip()
    task['title'] = re.sub(pattern_okr, '', task['title']).strip()

    # Dataview fields (Dataview Obsidian plugin)
    pattern_dv = r'[\[\(]([a-zA-Z\s]+)::(.+)[\]\)]'
    matches_dv = re.findall(pattern_dv, task['title'])
    for match in matches_dv:
        key, val = match[0].strip(), match[1].strip()
        if key in ['Story Points', 'duration']:
            val = float(val)
        task[key] = val

    # Task type field
    task_types = [tag for tag in task['tags']
                  if tag in ['epic', 'story', 'task']]
    if len(task_types) == 1:
        task['type'] = task_types[0]
    elif len(task_types) == 0:
        task['type'] = 'todo'
    else:
        print(elem)
        raise ValueError(f"Multiple task types found: {task_types}")

    # Story Points field (Dataview Obsidian plugin)
    if task['type'] in ['epic', 'story']:
        task['Story Points'] = task.get('Story Points', 0)
    elif task['type'] == 'task':
        task['Story Points'] = task.get('Story Points', 1)

    task['file_name'] = note

    task_node.data = task
    return task_node


def filter_daily_tasks(task_tree, keywords, start_date=None, end_date=None):
    """Filter a task tree, likely containing all the tasks from daily notes, based on keywords and date range.

    Args:
        task_tree (Tree): Tree object containing the tasks from daily notes.
        keywords (list): List of keywords to filter tasks.
        start_date (datetime.date, optional): Start date for filtering. Defaults to None.
        end_date (datetime.date, optional): End date for filtering. Defaults to None.

    Returns:
        Tree: Filtered task tree.
    """
    subtree = Tree(task_tree, deep=True)
    for node in subtree.expand_tree():
        if subtree.depth(node) > 0:
            date = subtree[node].data.get('file_name_date')
            if (start_date is None or date >= start_date) and \
                (end_date is None or date <= end_date) and \
                    any(keyword.lower() in subtree[node].data.get('title').lower() for keyword in keywords):
                continue
            else:
                subtree.link_past_node(node)
    return subtree
