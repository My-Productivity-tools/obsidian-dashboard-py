from markdown_it import MarkdownIt
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pathlib
import os
from src.note_utils import parse_note_for_tasks
from itertools import chain

md = MarkdownIt()
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))


def get_okr_data(okr_note, vault):
    okr_note = '2024 Oct'
    
    front_matter = vault.get_front_matter(okr_note)
    start_date = front_matter['start_date']
    end_date = front_matter['end_date']

    okr_list = parse_okr_note(okr_note, vault)
    return get_kr_data(okr_list, vault)


def parse_okr_note(okr_note, vault):
    # Get the HTML
    okr_note_path = VAULT_LOC / vault.md_file_index[okr_note]
    with open(okr_note_path, 'r', encoding="utf-8") as f:
        text = f.read()
    html = md.render(text)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get the Objectives
    o_pattern = r'(O\d+):(.+)'
    o_matches = [re.search(o_pattern, e.text) 
               for e in soup.findAll('h1', recursive=False)]
    okr_info = {m[1].strip(): {'name': m[2].strip(), 'kr_info': {}} for m in o_matches}
    
    # Get the Key Results
    kr_pattern = r'(O\d+)\s(KR\d+):(.+)'
    kr_matches = [re.search(kr_pattern, e.text) 
               for e in soup.findAll('h3', recursive=False)]
    for match in kr_matches:
        okr_info[match[1]]['kr_info'][match[2]] = match[3].strip()
    
    return okr_info


def get_kr_data(okr_list, vault):
    pass
