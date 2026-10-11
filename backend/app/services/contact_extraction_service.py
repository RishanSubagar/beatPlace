from __future__ import annotations

from typing import Protocol, Sequence

from app.job_repository import create_contact_candidates
from app.models import ContactCandidate, ContactSourcePage


class ContactExtractor(Protocol):
    async def extract_candidates(
        self,
        person_name: str,
        pages: Sequence[ContactSourcePage],
    ) -> Sequence[ContactCandidate | dict[str, object]]:
        """Return candidate contact details grounded in the supplied page text."""
        ...


async def extract_contact_candidates(
    job_id: str,
    person_name: str,
    pages: Sequence[ContactSourcePage],
    extractor: ContactExtractor,
) -> list[ContactCandidate]:
    """Extract, validate, and persist candidates without sending any email."""
    if not pages:
        return []

    candidates = [
        ContactCandidate.model_validate(candidate)
        for candidate in await extractor.extract_candidates(person_name, pages)
    ]
    pages_by_url = {str(page.source_url): page for page in pages}

    for candidate in candidates:
        source_page = pages_by_url.get(str(candidate.source_url))
        if source_page is None:
            raise ValueError("candidate source_url must match one of the supplied pages")
        if candidate.evidence not in source_page.text:
            raise ValueError("candidate evidence must appear verbatim in its source page")

    if not candidates:
        return []

    create_contact_candidates(
        job_id,
        person_name,
        candidates,
    )
    return candidates