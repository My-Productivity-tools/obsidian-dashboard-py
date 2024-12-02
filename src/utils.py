from src.note_utils import parse_note

def get_okr_data(okr, vault):
    okr = '2024 Oct'
    
    front_matter = vault.get_front_matter(okr)
    start_date = front_matter['start_date']
    end_date = front_matter['end_date']

    kr_list = parse_okr(okr, vault)
    return get_kr_data(kr_list, vault)


def parse_okr(okr, vault):
    pass


def get_kr_data(kr_list, vault):
    pass
