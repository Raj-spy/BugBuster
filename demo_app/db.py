"""SQLite setup for the demo app."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("demo.db")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, balance INTEGER)"
    )
    conn.execute("INSERT OR IGNORE INTO accounts (id, balance) VALUES (1, 1000)")
    conn.execute("INSERT OR IGNORE INTO accounts (id, balance) VALUES (2, 1000)")
    conn.commit()
    conn.close()
