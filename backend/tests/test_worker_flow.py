from __future__ import annotations

import unittest
from unittest.mock import patch

from app.job_repository import DB_PATH, get_research_results, initialize_database
from app.job_service import create_research_job, get_research_job, get_people_for_job, run_job_cycle
from app.services.research_service import research_person


class WorkerFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        if DB_PATH.exists():
            DB_PATH.unlink()
        initialize_database()

    def test_job_moves_from_queued_to_completed(self) -> None:
        job_id = create_research_job(
            upload={"filename": "beats.zip", "path": "/tmp/beats.zip"},
            people=["John Smith", "Jane Doe"],
            message="hello",
            from_email="demo@example.com",
        )

        run_job_cycle(job_id)

        job = get_research_job(job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job["status"], "completed")

        people = get_people_for_job(job_id)
        self.assertEqual({row["name"]: row["status"] for row in people}, {
            "John Smith": "completed",
            "Jane Doe": "completed",
        })

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
