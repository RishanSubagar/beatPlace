from __future__ import annotations

import unittest
from unittest.mock import patch

from app.job_repository import DB_PATH, initialize_database, create_job
from app.services.research_service import research_person


class ResearchCachingTests(unittest.TestCase):
    def setUp(self) -> None:
        if DB_PATH.exists():
            DB_PATH.unlink()
        initialize_database()

    def test_research_uses_cache_on_second_call(self) -> None:
        """Verify that researching the same artist twice uses cache on second call."""
        
        # Create two jobs
        job1_id = "job_001"
        job2_id = "job_002"
        
        create_job(job1_id, "beats1.zip", "/tmp/beats1.zip", "msg1", "from1@example.com", ["Drake"])
        create_job(job2_id, "beats2.zip", "/tmp/beats2.zip", "msg2", "from2@example.com", ["Drake"])
        
        with patch("app.services.research_service.serper_client.fetch_serper_results") as mock_fetch:
            # Mock should return what serper_client.fetch_serper_results returns (after normalization)
            mock_fetch.return_value = [
                {
                    "title": "Drake | Wikipedia",
                    "url": "https://en.wikipedia.org/wiki/Drake",
                    "description": "Canadian rapper",
                }
            ]
            
            # First research call - should hit Serper API
            print("\n[TEST] First research call for Drake...")
            results1 = research_person(job1_id, "Drake")
            self.assertEqual(len(results1), 1)
            self.assertEqual(mock_fetch.call_count, 1)
            print(f"  Serper API calls: {mock_fetch.call_count} (expected: 1)")
            
            # Second research call for same artist - should use cache
            print("[TEST] Second research call for Drake (should use cache)...")
            results2 = research_person(job2_id, "Drake")
            self.assertEqual(len(results2), 1)
            self.assertEqual(mock_fetch.call_count, 1)  # Still 1, didn't increase
            print(f"  Serper API calls: {mock_fetch.call_count} (expected: still 1 - cached!)")
            
            # Results should be the same
            self.assertEqual(results1[0]["url"], results2[0]["url"])
            print("  ✓ Cache hit successful - same results, no extra API call")


if __name__ == "__main__":
    unittest.main()
