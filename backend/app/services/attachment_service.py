from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import UploadFile

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


def process_attachment(file: Optional[UploadFile]) -> Optional[dict[str, str]]:
    if file is None:
        return None

    print(f"file attached: {file.filename}")

    target_path = UPLOAD_DIR / (file.filename or "upload.bin")
    with target_path.open("wb") as destination:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            destination.write(chunk)
    file.file.seek(0)

    return {"filename": file.filename or "upload.bin", "path": str(target_path)}


def process_message(message: str) -> dict[str, str]:
    print(f"message included: {bool(message)}")
    return {"text": message or ""}


def process_from(from_email: Optional[str]) -> str:
    from_value = from_email or "no-reply@example.com"
    print(f"from included: {from_value}")
    return from_value
