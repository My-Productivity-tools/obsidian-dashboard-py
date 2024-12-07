from dotenv import load_dotenv
import os
import obsidiantools.api as otools
from src.utils import get_okr_data
import pathlib

load_dotenv()
VAULT_LOC = os.getenv('VAULT_LOC')
vault = otools.Vault(pathlib.Path(VAULT_LOC)).connect().gather()

# EPIC: Get the OKR tracker done first

# TODO: Get the data relevant for the OKR tracker
okr = '2024 Oct'
okr_data = get_okr_data(okr, vault)

# TODO: Create any required utility functions

# TODO: Create the OKR tracker GUI for a single OKR