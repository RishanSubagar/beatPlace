from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models import ContactSourcePage
from app.services.openai_contact_extractor import (
    MODEL,
    OpenAIContactExtractor,
    _prepare_page_payload,
)


class OpenAIContactExtractorTests(unittest.IsolatedAsyncioTestCase):
    def test_payload_counts_signals_and_sends_relevant_excerpt(self) -> None:
        text = (
            "x" * 500
            + " Management booking inquiries: booking@artist.example or call +1 (555) 123-4567."
            + " unrelated text" * 1000
        )
        page = ContactSourcePage(
            source_url="https://artist.example/contact",
            text=text,
            http_status=200,
            content_type="text/html",
            redirect_history=["https://artist.example/contact"],
            mailto_count=1,
        )

        payload = _prepare_page_payload([page])

        self.assertEqual(len(payload), 1)
        self.assertLess(len(payload[0]["text"]), len(text))
        self.assertIn("booking@artist.example", payload[0]["text"])
        self.assertEqual(payload[0]["metrics"]["text_length"], len(text))
        self.assertEqual(payload[0]["metrics"]["email_candidates"], 1)
        self.assertEqual(payload[0]["metrics"]["mailto_links"], 1)
        self.assertEqual(payload[0]["metrics"]["phone_candidates"], 1)
        self.assertEqual(payload[0]["metrics"]["http_status"], 200)

    def test_skips_empty_pages_but_keeps_short_pages_with_email(self) -> None:
        empty_page = ContactSourcePage(
            source_url="https://social.example/artist",
            text="Profile",
        )
        short_contact_page = ContactSourcePage(
            source_url="https://artist.example/contact",
            text="Email booking@artist.example",
        )

        payload = _prepare_page_payload([empty_page, short_contact_page])

        self.assertEqual(len(payload), 1)
        self.assertIn("booking@artist.example", payload[0]["text"])

    async def test_requests_structured_candidates_from_gpt_4o_mini(self) -> None:
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=(
                            '{"candidates":[{"email":"booking@artist.example",'
                            '"confidence":0.9,"source_url":"https://artist.example/contact",'
                            '"evidence":"booking@artist.example"}]}'
                        )
                    )
                )
            ]
        )
        create = MagicMock(return_value=response)
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        extractor = OpenAIContactExtractor(client=client)
        page = ContactSourcePage(
            source_url="https://artist.example/contact",
            text="Email booking@artist.example",
        )

        candidates = await extractor.extract_candidates("Artist One", [page])

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].email, "booking@artist.example")
        self.assertEqual(create.call_args.kwargs["model"], MODEL)
        self.assertEqual(MODEL, "gpt-4o-mini")
        self.assertEqual(create.call_args.kwargs["response_format"]["type"], "json_schema")

    async def test_missing_api_key_fails_clearly(self) -> None:
        extractor = OpenAIContactExtractor()
        page = ContactSourcePage(
            source_url="https://artist.example/contact",
            text="Email booking@artist.example",
        )

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is required"):
                await extractor.extract_candidates("Artist One", [page])


if __name__ == "__main__":
    unittest.main()
