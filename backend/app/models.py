from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field

JobStatus = Literal["queued", "researching", "interpreting", "completed", "failed"]


class UploadResponse(BaseModel):
    job_id: str
    people_found: int
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    people_found: int
    people_completed: int
    created_at: datetime


class PersonInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ContactCandidate(BaseModel):
    email: EmailStr
    confidence: float = Field(ge=0, le=1)
    source_url: AnyHttpUrl
    evidence: str = Field(min_length=1, max_length=1000)


class ContactSourcePage(BaseModel):
    source_url: AnyHttpUrl
    text: str = Field(max_length=30000)


class StoredContactCandidate(ContactCandidate):
    id: int
    person_name: str
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime