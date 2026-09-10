from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from app.job_repository import (
    create_job as repo_create_job,
    get_job as repo_get_job,
    get_job_details,
    get_people_for_job as repo_get_people_for_job,
    initialize_database,
    update_job_status,
    update_person_status,
)
from app.services.email_finder import find_emails_for_artists
from app.services.mailer import send_mail
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


async def run_job_cycle_async(job_id: str) -> None:
    """
    Execute the full job cycle: research, email finding, and sending.
    """
    initialize_database()
    job = repo_get_job(job_id)
    if job is None:
        raise JobNotFoundError(job_id)
    
    # Get full job details for upload path and message
    job_details = get_job_details(job_id)
    if job_details is None:
        raise JobNotFoundError(job_id)

    try:
        # Phase 1: Research
        update_job_status(job_id, "researching")
        people = repo_get_people_for_job(job_id)
        
        for person in people:
            update_person_status(job_id, person["name"], "researching")
        
        # Research each artist
        for person in people:
            try:
                print(f"\n=== Researching {person['name']} ===")
                research_person(job_id, person["name"])
                print(f"=== Research complete for {person['name']} ===")
            except Exception as e:
                print(f"❌ Research failed for {person['name']}: {e}")
                # Continue with others even if one fails
        
        # Phase 2: Find emails and send
        update_job_status(job_id, "interpreting")
        
        # Get email mappings for all artists
        artist_names = [p["name"] for p in people]
        email_map = await find_emails_for_artists(artist_names)
        
        # Send emails to each person
        upload_path = Path(job_details["upload_path"])
        from_email = job_details["from_email"]
        message = job_details["message"]
        
        for person in people:
            person_name = person["name"]
            emails = email_map.get(person_name, [])
            
            if not emails:
                print(f"No emails found for {person_name}")
                update_person_status(job_id, person_name, "failed")
                continue
            
            try:
                for email in emails:
                    subject = f"Beat Submission for {person_name}"
                    body = f"""Hi {person_name},

{message}

Check out these beats!

Best regards"""
                    
                    await send_mail({
                        "to": email,
                        "from": from_email,
                        "subject": subject,
                        "text": body,
                        "attachment_path": str(upload_path) if upload_path.exists() else None,
                    })
                    print(f"Email sent to {email} for {person_name}")
                
                update_person_status(job_id, person_name, "completed")
            except Exception as e:
                print(f"Failed to send email for {person_name}: {e}")
                update_person_status(job_id, person_name, "failed")
        
        update_job_status(job_id, "completed")
        print(f"Job {job_id} completed")
    
    except Exception as e:
        print(f"Job {job_id} failed with error: {e}")
        update_job_status(job_id, "failed")


def run_job_cycle(job_id: str) -> None:
    """
    Synchronous wrapper for run_job_cycle_async.
    """
    asyncio.run(run_job_cycle_async(job_id))