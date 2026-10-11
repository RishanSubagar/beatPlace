from __future__ import annotations

import unittest
from collections.abc import Sequence
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from app.job_repository import (
    DB_PATH,
    get_contact_candidates,
    get_research_results,
    initialize_database,
)
from app.job_service import create_research_job, get_research_job, get_people_for_job, run_job_cycle
from app.models import ContactCandidate, ContactSourcePage
from app.services.research_service import research_person


class FakeContactExtractor:
    def __init__(self, candidates: list[dict[str, Any]]) -> None:
        self.candidates = candidates

    async def extract_candidates(
        self,
        person_name: str,
        pages: Sequence[ContactSourcePage],
    ) -> Sequence[ContactCandidate | dict[str, object]]:
        return self.candidates


class WorkerFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        if DB_PATH.exists():
            DB_PATH.unlink()
        initialize_database()

    def test_job_saves_candidates_pending_without_sending(self) -> None:
        job_id = create_research_job(
            upload={"filename": "beats.zip", "path": "/tmp/beats.zip"},
            people=["John Smith", "Jane Doe"],
            message="hello",
            from_email="demo@example.com",
        )

        page = ContactSourcePage.model_validate(
            {
                "source_url": "https://artist.example/contact",
                "text": "Booking inquiries: booking@artist.example",
            }
        )
        researcher = Mock(
            return_value=[
                {
                    "title": "Artist contact",
                    "url": "https://artist.example/contact",
                    "description": "Official contact page",
                }
            ]
        )
        page_fetcher = Mock(return_value=[page])
        extractor = FakeContactExtractor(
            [
                {
                    "email": "booking@artist.example",
                    "confidence": 0.9,
                    "source_url": "https://artist.example/contact",
                    "evidence": "booking@artist.example",
                }
            ]
        )
        with patch("app.services.mailer.send_mail", new_callable=AsyncMock) as mock_send:
            run_job_cycle(
                job_id,
                researcher=researcher,
                page_fetcher=page_fetcher,
                extractor=extractor,
            )
        mock_send.assert_not_awaited()

        job = get_research_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job["status"], "awaiting_approval")

        people = get_people_for_job(job_id)
        self.assertEqual(
            {row["name"]: row["status"] for row in people},
            {"John Smith": "pending_review", "Jane Doe": "pending_review"},
        )

        candidates = get_contact_candidates(job_id)
        self.assertEqual(len(candidates), 2)
        self.assertTrue(all(candidate["status"] == "pending" for candidate in candidates))

    def test_job_completes_when_no_candidates_are_found(self) -> None:
        job_id = create_research_job(
            upload={"filename": "beats.zip", "path": "/tmp/beats.zip"},
            people=["Artist One"],
            message="hello",
            from_email="demo@example.com",
        )
        page = ContactSourcePage.model_validate(
            {
                "source_url": "https://artist.example/contact",
                "text": "Contact form available.",
            }
        )
        extractor = FakeContactExtractor([])

        run_job_cycle(
            job_id,
            researcher=Mock(return_value=[{"url": "https://artist.example/contact"}]),
            page_fetcher=Mock(return_value=[page]),
            extractor=extractor,
        )

        self.assertEqual(get_research_job(job_id)["status"], "completed")
        self.assertEqual(get_people_for_job(job_id)[0]["status"], "no_candidates")
        self.assertEqual(get_contact_candidates(job_id), [])

    def test_research_service_persists_normalized_results(self) -> None:
        job_id = create_research_job(
            upload={"filename": "beats.zip", "path": "/tmp/beats.zip"},
            people=["John Smith"],
            message="hello",
            from_email="demo@example.com",
        )

        with patch("app.services.research_service.serper_client.fetch_serper_results") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "title": "John Smith | Acme Team",
                    "url": "https://acme.com/team/john-smith",
                    "description": "John Smith leads product at Acme Inc.",
                }
            ]

            results = research_person(job_id, "John Smith")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "https://acme.com/team/john-smith")
        self.assertEqual(results[0]["title"], "John Smith | Acme Team")

        persisted = get_research_results(job_id, "John Smith")
        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0]["url"], "https://acme.com/team/john-smith")


if __name__ == "__main__":
    unittest.main()
