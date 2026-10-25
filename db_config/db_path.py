import sqlite3
from pathlib import Path

# Localiza a raiz do projeto (um nível acima de db_config)
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "rock_telefonia.db"


def get_connection():
    return sqlite3.connect(DB_PATH)