from __future__ import annotations

import uuid
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
MAX_UPLOAD_BYTES = 100 * 1024 * 1024


def process_attachment(file: Optional[UploadFile]) -> Optional[dict[str, str]]:
    if file is None:
        return None

    filename = Path(file.filename or "upload.zip").name
    if Path(filename).suffix.lower() != ".zip":
        raise ValueError("only ZIP files are accepted")

    target_path = UPLOAD_DIR / f"{uuid.uuid4().hex}.zip"
    bytes_written = 0
    try:
        with target_path.open("wb") as destination:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > MAX_UPLOAD_BYTES:
                    raise ValueError("ZIP file exceeds the 25 MB limit")
                destination.write(chunk)

        if not zipfile.is_zipfile(target_path):
            raise ValueError("uploaded file is not a valid ZIP archive")
        with zipfile.ZipFile(target_path) as archive:
            if any(Path(name).is_absolute() or ".." in Path(name).parts for name in archive.namelist()):
                raise ValueError("ZIP archive contains an unsafe path")
    except Exception:
        target_path.unlink(missing_ok=True)
        raise

    file.file.seek(0)

    return {"filename": filename, "path": str(target_path)}
