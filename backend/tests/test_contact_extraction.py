from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.job_repository import DB_PATH, create_job, get_contact_candidates, initialize_database
from app.models import ContactSourcePage
from app.services.contact_extraction_service import extract_contact_candidates


class ContactExtractionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        if DB_PATH.exists():
            DB_PATH.unlink()
        initialize_database()
        create_job(
            "job_contacts",
            "beats.zip",
            "/tmp/beats.zip",
            "Hello",
            "producer@example.com",
            ["Artist One"],
        )

    async def test_valid_candidate_is_persisted_pending_review(self) -> None:
        page = ContactSourcePage(
            source_url="https://artist.example/contact",
            text="For bookings, email booking@artist.example.",
        )
        extractor = SimpleNamespace(
            extract_candidates=AsyncMock(
                return_value=[
                    {
                        "email": "booking@artist.example",
                        "confidence": 0.91,
                        "source_url": "https://artist.example/contact",
                        "evidence": "booking@artist.example",
                    }
                ]
            )
        )

        candidates = await extract_contact_candidates(
            "job_contacts", "Artist One", [page], extractor
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].email, "booking@artist.example")
        persisted = get_contact_candidates("job_contacts", "Artist One")
        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0]["status"], "pending")
        self.assertEqual(persisted[0]["source_url"], "https://artist.example/contact")
        self.assertEqual(persisted[0]["evidence"], "booking@artist.example")
        extractor.extract_candidates.assert_awaited_once()

    async def test_candidate_with_unverifiable_evidence_is_not_saved(self) -> None:
        page = ContactSourcePage(
            source_url="https://artist.example/contact",
            text="Contact the artist's management team.",
        )
        extractor = SimpleNamespace(
            extract_candidates=AsyncMock(
                return_value=[
                    {
                        "email": "manager@artist.example",
                        "confidence": 0.8,
                        "source_url": "https://artist.example/contact",
                        "evidence": "manager@artist.example",
                    }
                ]
            )
        )

        with self.assertRaisesRegex(ValueError, "evidence must appear verbatim"):
            await extract_contact_candidates(
                "job_contacts", "Artist One", [page], extractor
            )

        self.assertEqual(get_contact_candidates("job_contacts"), [])

    async def test_empty_pages_skip_provider(self) -> None:
        extractor = SimpleNamespace(extract_candidates=AsyncMock())

        candidates = await extract_contact_candidates(
            "job_contacts", "Artist One", [], extractor
        )

        self.assertEqual(candidates, [])
        extractor.extract_candidates.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
