from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

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