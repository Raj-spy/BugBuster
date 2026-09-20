"""SQLite setup for the demo app."""
import sqlite3

DB_PATH = "demo.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, balance INTEGER)"
    )
    conn.commit()
    conn.close()
