def parse_note(note, vault):
    note = '2024 Oct'
    text = vault.get_source_text(note)
    lines = [line for line in text.split('\n') if line.strip()]
