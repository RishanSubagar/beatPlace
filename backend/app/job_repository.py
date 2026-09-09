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
    connection = _connect()
    try:
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
            CREATE TABLE IF NOT EXISTS research_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL REFERENCES jobs(id),
                person_name TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def create_job(
    job_id: str,
    upload_filename: str,
    upload_path: str,
    message: str,
    from_email: str | None,
    people: list[str],
) -> None:
    created_at = datetime.now(timezone.utc).isoformat()
    connection = _connect()
    try:
        connection.execute(
            "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, upload_filename, upload_path, message, from_email, "queued", created_at),
        )
        connection.executemany(
            "INSERT INTO people (job_id, name) VALUES (?, ?)",
            [(job_id, person) for person in people],
        )
        connection.commit()
    finally:
        connection.close()


def get_job(job_id: str) -> sqlite3.Row | None:
    connection = _connect()
    try:
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
    finally:
        connection.close()


def get_job_details(job_id: str) -> sqlite3.Row | None:
    """Get full job details including upload path, message, and from_email."""
    connection = _connect()
    try:
        return connection.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (job_id,),
        ).fetchone()
    finally:
        connection.close()


def get_people_for_job(job_id: str) -> list[sqlite3.Row]:
    connection = _connect()
    try:
        return connection.execute(
            "SELECT id, job_id, name, status FROM people WHERE job_id = ? ORDER BY id",
            (job_id,),
        ).fetchall()
    finally:
        connection.close()


def update_job_status(job_id: str, status: str) -> None:
    connection = _connect()
    try:
        connection.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        connection.commit()
    finally:
        connection.close()


def update_person_status(job_id: str, name: str, status: str) -> None:
    connection = _connect()
    try:
        connection.execute(
            "UPDATE people SET status = ? WHERE job_id = ? AND name = ?",
            (status, job_id, name),
        )
        connection.commit()
    finally:
        connection.close()


def create_research_result(
    job_id: str,
    person_name: str,
    title: str,
    url: str,
    description: str,
) -> None:
    created_at = datetime.now(timezone.utc).isoformat()
    connection = _connect()
    try:
        connection.execute(
            "INSERT INTO research_results (job_id, person_name, title, url, description, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, person_name, title, url, description, created_at),
        )
        connection.commit()
    finally:
        connection.close()


def get_research_results(job_id: str, person_name: str | None = None) -> list[sqlite3.Row]:
    connection = _connect()
    try:
        if person_name is None:
            rows = connection.execute(
                "SELECT * FROM research_results WHERE job_id = ? ORDER BY id",
                (job_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM research_results WHERE job_id = ? AND person_name = ? ORDER BY id",
                (job_id, person_name),
            ).fetchall()
        return rows
    finally:
        connection.close()