import sqlite3

from app.models.database import get_db


def upsert_job_ready(video_id: str, filename: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO video_jobs (video_id, filename, status, error_message, updated_at)
            VALUES (?, ?, 'ready', NULL, datetime('now'))
            ON CONFLICT(video_id) DO UPDATE SET
                status = 'ready',
                error_message = NULL,
                updated_at = datetime('now')
            """,
            (video_id, filename),
        )


def upsert_job_processing(video_id: str, filename: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO video_jobs (video_id, filename, status, error_message, updated_at)
            VALUES (?, ?, 'processing', NULL, datetime('now'))
            ON CONFLICT(video_id) DO UPDATE SET
                status = 'processing',
                error_message = NULL,
                updated_at = datetime('now')
            """,
            (video_id, filename),
        )


def update_job_ready(video_id: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE video_jobs
            SET status = 'ready', error_message = NULL, updated_at = datetime('now')
            WHERE video_id = ?
            """,
            (video_id,),
        )


def update_job_error(video_id: str, message: str) -> None:
    with get_db() as conn:
        conn.execute(
            """
            UPDATE video_jobs
            SET status = 'error', error_message = ?, updated_at = datetime('now')
            WHERE video_id = ?
            """,
            (message, video_id),
        )


def fetch_job_row(video_id: str) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute(
            "SELECT status, error_message FROM video_jobs WHERE video_id = ?",
            (video_id,),
        ).fetchone()
