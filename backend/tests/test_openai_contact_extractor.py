from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models import ContactSourcePage
from app.services.openai_contact_extractor import MODEL, OpenAIContactExtractor


class OpenAIContactExtractorTests(unittest.IsolatedAsyncioTestCase):
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
