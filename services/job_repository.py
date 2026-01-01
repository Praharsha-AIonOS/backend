# services/job_repository.py

from db import get_db_connection
import sqlite3
from db import DB_PATH
# DB_PATH = "jobs.db"

STATUS_QUEUED = "QUEUED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"

def fetch_oldest_pending_job():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM jobs
        WHERE status = ?
        ORDER BY created_at ASC
        LIMIT 1
    """, (STATUS_QUEUED,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_job_status(job_id, status, started_at=None, completed_at=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    if started_at:
        cursor.execute(
            "UPDATE jobs SET status=?, started_at=? WHERE job_id=?",
            (status, started_at, job_id)
        )
    elif completed_at:
        cursor.execute(
            "UPDATE jobs SET status=?, completed_at=? WHERE job_id=?",
            (status, completed_at, job_id)
        )
    else:
        cursor.execute(
            "UPDATE jobs SET status=? WHERE job_id=?",
            (status, job_id)
        )

    conn.commit()
    conn.close()


def has_in_progress_job():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM jobs
        WHERE status = ?
        LIMIT 1
    """, (STATUS_IN_PROGRESS,))

    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def update_job_output(job_id, output_video, completed_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs
        SET output_video = ?, completed_at = ?
        WHERE job_id = ?
    """, (output_video, completed_at, job_id))

    conn.commit()
    conn.close()

import sqlite3
from db import DB_PATH


def get_job_by_id(job_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM jobs WHERE job_id = ?",
        (job_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)
