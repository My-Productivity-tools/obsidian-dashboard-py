from dotenv import load_dotenv
import os
import obsidiantools.api as otools
from markdown_it import MarkdownIt
from src.utils import get_okr_data
from src.note_utils import parse_note_for_tasks
import pathlib
import json

md = MarkdownIt()
load_dotenv()
VAULT_LOC = pathlib.Path(os.getenv('VAULT_LOC'))

vault = otools.Vault(VAULT_LOC).connect().gather()

# EPIC: Get the OKR tracker done first
# Get the data relevant for the OKR tracker
okr = '2024 Nov'
okr_path = VAULT_LOC / vault.md_file_index[okr]
okr_data = get_okr_data(okr, vault)

# TODO: Create the OKR tracker GUI for a single OKR
# TODO: Test the OKR data extracted and chart data

# note = 'Deep Learning'
# note_path = VAULT_LOC / vault.md_file_index[note]
# task_tree = parse_note_for_tasks(note, vault).to_json(with_data=True)
# with open('tasks.json', 'w', encoding='utf-8') as f:
#     json.dump(json.loads(task_tree.to_json(with_data=True)),
#               f, indent=4, separators=(',', ': '))
