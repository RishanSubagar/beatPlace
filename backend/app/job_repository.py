from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "jobs.sqlite3"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                upload_filename TEXT NOT NULL,
                upload_path TEXT NOT NULL,
                message TEXT NOT NULL,
                from_email TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL REFERENCES jobs(id),
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                UNIQUE(job_id, name)
            );
            """
        )


def create_job(
    job_id: str,
    upload_filename: str,
    upload_path: str,
    message: str,
    from_email: str | None,
    people: list[str],
) -> None:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute(
            "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, upload_filename, upload_path, message, from_email, "queued", created_at),
        )
        connection.executemany(
            "INSERT INTO people (job_id, name) VALUES (?, ?)",
            [(job_id, person) for person in people],
        )


def get_job(job_id: str) -> sqlite3.Row | None:
    with _connect() as connection:
        return connection.execute(
            """
            SELECT jobs.id, jobs.status, jobs.created_at,
                   COUNT(people.id) AS people_found,
                   SUM(CASE WHEN people.status = 'completed' THEN 1 ELSE 0 END) AS people_completed
            FROM jobs LEFT JOIN people ON people.job_id = jobs.id
            WHERE jobs.id = ? GROUP BY jobs.id
            """,
            (job_id,),
        ).fetchone()