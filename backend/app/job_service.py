from __future__ import annotations

import asyncio
import uuid
from typing import Protocol, Sequence

from app.job_events import job_events
from app.job_repository import (
    create_job as repo_create_job,
    get_contact_candidates as repo_get_contact_candidates,
    get_job as repo_get_job,
    get_people_for_job as repo_get_people_for_job,
    initialize_database,
    update_job_status,
    update_person_status,
)
from app.models import ContactSourcePage
from app.services.contact_extraction_service import ContactExtractor, extract_contact_candidates
from app.services.openai_contact_extractor import OpenAIContactExtractor
from app.services.page_fetch_service import fetch_contact_pages
from app.services.research_service import research_person


class JobNotFoundError(RuntimeError):
    def __init__(self, job_id: str):
        super().__init__(f"job not found: {job_id}")
        self.job_id = job_id


def create_research_job(
    *, upload: dict[str, str], people: list[str], message: str, from_email: str | None
) -> str:
    initialize_database()
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    repo_create_job(job_id, upload["filename"], upload["path"], message, from_email, people)
    return job_id


def get_research_job(job_id: str):
    initialize_database()
    job = repo_get_job(job_id)
    if job is None:
        raise JobNotFoundError(job_id)
    return job


def get_people_for_job(job_id: str):
    initialize_database()
    job = repo_get_job(job_id)
    if job is None:
        raise JobNotFoundError(job_id)
    return repo_get_people_for_job(job_id)


def get_contact_candidates(job_id: str):
    initialize_database()
    if repo_get_job(job_id) is None:
        raise JobNotFoundError(job_id)
    return repo_get_contact_candidates(job_id)


def _publish_job_update(job_id: str) -> None:
    job_events.publish(job_id)


class Researcher(Protocol):
    def __call__(self, job_id: str, person_name: str) -> list[dict[str, str]]: ...


class PageFetcher(Protocol):
    def __call__(self, urls: Sequence[str]) -> list[ContactSourcePage]: ...


async def run_job_cycle_async(
    job_id: str,
    *,
    researcher: Researcher = research_person,
    page_fetcher: PageFetcher = fetch_contact_pages,
    extractor: ContactExtractor | None = None,
) -> None:
    """
    Execute the full job cycle: research, email finding, and sending.
    """
    initialize_database()
    job = repo_get_job(job_id)
    if job is None:
        raise JobNotFoundError(job_id)
    
    try:
        update_job_status(job_id, "researching")
        _publish_job_update(job_id)
        people = repo_get_people_for_job(job_id)

        results_by_person: dict[str, list[dict[str, str]]] = {}
        failed_people: set[str] = set()
        for person in people:
            person_name = person["name"]
            update_person_status(job_id, person_name, "researching")
            _publish_job_update(job_id)
            try:
                results_by_person[person_name] = researcher(job_id, person_name)
            except Exception as e:
                print(f"Research failed for {person_name}: {e}")
                failed_people.add(person_name)
                update_person_status(job_id, person_name, "failed")
                _publish_job_update(job_id)

        update_job_status(job_id, "interpreting")
        _publish_job_update(job_id)

        contact_extractor = extractor or OpenAIContactExtractor()
        for person in people:
            person_name = person["name"]
            if person_name in failed_people:
                continue

            try:
                results = results_by_person.get(person_name, [])
                update_person_status(job_id, person_name, "finding_contacts")
                _publish_job_update(job_id)
                pages = await asyncio.to_thread(
                    page_fetcher,
                    [result["url"] for result in results if result.get("url")],
                )
                candidates = await extract_contact_candidates(
                    job_id,
                    person_name,
                    pages,
                    contact_extractor,
                )
                new_status = "pending_review" if candidates else "no_candidates"
                update_person_status(job_id, person_name, new_status)
            except Exception as e:
                print(f"Contact extraction failed for {person_name}: {e}")
                update_person_status(job_id, person_name, "failed")

            _publish_job_update(job_id)

        candidates = repo_get_contact_candidates(job_id)
        final_status = "awaiting_approval" if candidates else "completed"
        update_job_status(job_id, final_status)
        _publish_job_update(job_id)
        print(f"Job {job_id} finished with status {final_status}; no emails were sent")

    except Exception as e:
        print(f"Job {job_id} failed with error: {e}")
        update_job_status(job_id, "failed")
        _publish_job_update(job_id)


def run_job_cycle(
    job_id: str,
    *,
    researcher: Researcher = research_person,
    page_fetcher: PageFetcher = fetch_contact_pages,
    extractor: ContactExtractor | None = None,
) -> None:
    """
    Synchronous wrapper for run_job_cycle_async.
    """
    asyncio.run(
        run_job_cycle_async(
            job_id,
            researcher=researcher,
            page_fetcher=page_fetcher,
            extractor=extractor,
        )
    )