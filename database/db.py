# database/db.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
 
DATABASE_PATH = Path("sina_main.db")
 
@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent read/write performance
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()
 
def execute(query: str, params: tuple = ()):
    """Execute a write query (INSERT, UPDATE, DELETE). Returns lastrowid."""
    with get_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid
 
def fetch_one(query: str, params: tuple = ()):
    """Fetch a single row as a dict, or None if not found."""
    with get_connection() as conn:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None
 
def fetch_all(query: str, params: tuple = ()):
    """Fetch all matching rows as a list of dicts."""
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]