from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.job_service import create_research_job, get_research_job
from app.models import JobStatusResponse, UploadResponse
from app.services.attachment_service import process_attachment
from app.services.email_finder import parse_artists

app = FastAPI(title="BeatPlace", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index() -> FileResponse:
    frontend_path = Path(__file__).resolve().parents[2] / "frontend" / "public" / "index.html"
    if not frontend_path.exists():
        raise HTTPException(status_code=404, detail="Frontend page not found")
    return FileResponse(frontend_path)


@app.post("/upload")
async def upload(
    zip_file: UploadFile = File(..., alias="zip"),
    artists: str = Form(""),
    message: str = Form(""),
    fromEmail: Optional[str] = Form(None),
) -> dict[str, object]:
    if not zip_file:
        raise HTTPException(status_code=400, detail='zip file required in "zip" field')

    artists_list = list(dict.fromkeys(parse_artists(artists)))
    if not artists_list:
        raise HTTPException(status_code=400, detail="at least one artist is required")

    try:
        attached = process_attachment(zip_file)
        if attached is None:
            raise ValueError("ZIP file is required")
        job_id = create_research_job(
            upload=attached, people=artists_list, message=message, from_email=fromEmail
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    response = UploadResponse(job_id=job_id, people_found=len(artists_list), status="queued")
    return response.model_dump()


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def job_status(job_id: str) -> JobStatusResponse:
    job = get_research_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(
        job_id=job["id"],
        status=job["status"],
        people_found=job["people_found"],
        people_completed=job["people_completed"] or 0,
        created_at=job["created_at"],
    )
