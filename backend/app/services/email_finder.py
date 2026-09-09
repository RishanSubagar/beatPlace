from __future__ import annotations

import re
from typing import Any


def parse_artists(artists_str: str | None) -> list[str]:
    artists = (artists_str or "").split(r"[\n,]+") if False else re.split(r"[\n,]+", artists_str or "")
    parsed = [artist.strip() for artist in artists if artist and artist.strip()]
    print(f"artists done parsing: {len(parsed)} {parsed}")
    return parsed


async def find_emails_for_artists(artists: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}

    for artist in artists:
        name = artist.strip()
        if not name:
            continue
        # For now, generate placeholder emails but log a warning
        # TODO: Extract real emails from research results
        normalized = name.lower().replace(" ", ".").replace("-", ".")
        normalized = re.sub(r"[^a-z0-9.]", "", normalized)
        emails = [f"{normalized}@example.com", f"contact@{normalized}music.com"]
        out[name] = emails
        print(f"[EMAIL_FINDER] {name}: Generated placeholder emails (should extract from research results)")
        for email in emails:
            print(f"  - {email}")

    total = sum(len(emails) for emails in out.values())
    print(f"[EMAIL_FINDER] Total placeholder emails: {total}")
    print(f"[EMAIL_FINDER] ⚠️  WARNING: Using placeholder emails - implement extraction from research results!")

    return out
