# backend/db.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            input_video TEXT NOT NULL,
            input_audio TEXT NOT NULL,
            output_video TEXT NOT NULL,
            status TEXT NOT NULL,
            feature TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT
        )
    """)

    conn.commit()
    conn.close()
