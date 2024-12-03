from mistune.plugins.task_lists import task_lists
import mistune
import pypandoc
import json

markdown = mistune.create_markdown(plugins=['task_lists'])


def parse_note_via_html(note, vault):
    note = '2024 Oct'
    note_path = VAULT_LOC / vault.md_file_index[note]
    with open(note_path, 'r', encoding="utf8") as f:
        text = f.read()
    tasks = markdown(text)


def parse_note_via_json(note, vault):
    note = '2024 Oct'
    note_path = VAULT_LOC / vault.md_file_index[note]
    text_dict = json.loads(pypandoc.convert_file(note_path, to='json'))
    lines = [line for line in text_dict['blocks'] if line.strip()]
    tasks = task_lists(text)


def parse_note_via_text(note, vault):
    note = '2024 Oct'
    note_path = VAULT_LOC / vault.md_file_index[note]
    text = vault.get_source_text(note)  # Doesn't identify bullet points as separate lines
    lines = [line for line in text.split('\n') if line.strip()]
