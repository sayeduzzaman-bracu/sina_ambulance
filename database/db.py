# database/db.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = Path("sina_main.db")

@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def execute(query: str, params: tuple = ()):
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()

def fetch_one(query: str, params: tuple = ()):
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None

def fetch_all(query: str, params: tuple = ()):
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]