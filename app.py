from dotenv import load_dotenv
import os
import obsidiantools.api as otools

load_dotenv()
VAULT_LOC = os.getenv('VAULT_LOC')
vault = otools.Vault(VAULT_LOC).connect().gather()
