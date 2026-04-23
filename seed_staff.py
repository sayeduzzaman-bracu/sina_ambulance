"""
seed_staff.py
-------------
Run this ONCE from your project root to insert the 3 admin accounts
and 5 demo drivers into sina_main.db.

    python seed_staff.py

Safe to run on an existing database — uses INSERT OR IGNORE so it
will never duplicate or overwrite existing records.
"""

import sqlite3
from werkzeug.security import generate_password_hash
from pathlib import Path

DB_PATH = Path("sina_main.db")

ADMINS = [
    ("AdminShafi",  "Shafi123"),
    ("AdminSultan", "Sultan123"),
    ("AdminSayed",  "Sayed123"),
]

DRIVERS = [
    ("Rahim Uddin",   "01711-100001", "Driver1234"),
    ("Karim Miah",    "01711-100002", "Driver1234"),
    ("Jamal Hossain", "01711-100003", "Driver1234"),
    ("Faruk Ahmed",   "01711-100004", "Driver1234"),
    ("Nabil Islam",   "01711-100005", "Driver1234"),
]

def seed():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at '{DB_PATH}'. "
              "Run your app once first so init_tables() creates it.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Seeding admins...")
    for username, password in ADMINS:
        hashed = generate_password_hash(password)
        cursor.execute(
            "INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        status = "inserted" if cursor.rowcount else "already exists (skipped)"
        print(f"  {username}: {status}")

    print("\nSeeding demo drivers...")
    for full_name, phone, password in DRIVERS:
        hashed = generate_password_hash(password)
        cursor.execute(
            """INSERT OR IGNORE INTO drivers (full_name, phone, password)
               VALUES (?, ?, ?)""",
            (full_name, phone, hashed)
        )
        status = "inserted" if cursor.rowcount else "already exists (skipped)"
        print(f"  {full_name} ({phone}): {status}")

    conn.commit()
    conn.close()
    print("\nDone. All staff seeded successfully.")

if __name__ == "__main__":
    seed()
