from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.services.attachment_service import process_attachment, process_from, process_message
from app.services.email_finder import find_emails_for_artists, parse_artists
from app.services.mailer import send_mail

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
):
    if not zip_file:
        raise HTTPException(status_code=400, detail='zip file required in "zip" field')

    attached = process_attachment(zip_file)
    msg = process_message(message)
    sender = process_from(fromEmail)
    artists_list = parse_artists(artists)
    found = await find_emails_for_artists(artists_list)

    results: list[dict[str, object]] = []
    for artist, emails in found.items():
        for email in emails:
            mail_options = {
                "from": sender,
                "to": email,
                "subject": f"Beats for {artist}",
                "text": msg["text"],
                "attachments": [{"filename": attached["filename"], "path": attached["path"]}] if attached else [],
            }
            info = await send_mail(mail_options)
            results.append({"artist": artist, "email": email, "messageId": info["messageId"], "simulated": True})

    return {
        "uploaded": zip_file.filename,
        "artists": artists_list,
        "found": found,
        "results": results,
    }
