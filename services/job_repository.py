# services/job_repository.py

import psycopg2.extras
from db import get_db_connection, return_db_connection

STATUS_QUEUED = "QUEUED"
STATUS_IN_PROGRESS = "IN_PROGRESS"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"

def fetch_oldest_pending_job():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT * FROM jobs
        WHERE status = %s
        ORDER BY created_at ASC
        LIMIT 1
    """, (STATUS_QUEUED,))

    row = cursor.fetchone()
    # RealDictRow is already dict-like (subclass of dict), can be used directly
    # But convert explicitly using items() for compatibility
    if row:
        # RealDictRow supports .items() method
        result = {k: v for k, v in row.items()}
    else:
        result = None
    return_db_connection(conn)
    return result


def update_job_status(job_id, status, started_at=None, completed_at=None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        if started_at:
            cursor.execute(
                "UPDATE jobs SET status=%s, started_at=%s WHERE job_id=%s",
                (status, started_at, job_id)
            )
        elif completed_at:
            cursor.execute(
                "UPDATE jobs SET status=%s, completed_at=%s WHERE job_id=%s",
                (status, completed_at, job_id)
            )
        else:
            cursor.execute(
                "UPDATE jobs SET status=%s WHERE job_id=%s",
                (status, job_id)
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        return_db_connection(conn)


def has_in_progress_job():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT 1 FROM jobs
        WHERE status = %s
        LIMIT 1
    """, (STATUS_IN_PROGRESS,))

    exists = cursor.fetchone() is not None
    return_db_connection(conn)
    return exists

def update_job_output(job_id, output_video, completed_at):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        cursor.execute("""
            UPDATE jobs
            SET output_video = %s, completed_at = %s
            WHERE job_id = %s
        """, (output_video, completed_at, job_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        return_db_connection(conn)


def get_job_by_id(job_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(
        "SELECT * FROM jobs WHERE job_id = %s",
        (job_id,)
    )

    row = cursor.fetchone()
    # RealDictRow is already dict-like (subclass of dict), can be used directly
    # But convert explicitly using items() for compatibility
    if row:
        # RealDictRow supports .items() method
        result = {k: v for k, v in row.items()}
    else:
        result = None
    return_db_connection(conn)
    return result
