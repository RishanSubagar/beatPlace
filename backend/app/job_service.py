from __future__ import annotations

import uuid

from app.job_repository import create_job, get_job, initialize_database


def create_research_job(
    *, upload: dict[str, str], people: list[str], message: str, from_email: str | None
) -> str:
    initialize_database()
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    create_job(job_id, upload["filename"], upload["path"], message, from_email, people)
    return job_id


def get_research_job(job_id: str):
    initialize_database()
    return get_job(job_id)