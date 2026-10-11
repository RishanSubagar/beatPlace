from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import requests

from app.services import page_fetch_service
from app.services.page_fetch_service import UnsafeTargetError, fetch_contact_pages


class PageFetchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.public_dns = patch(
            "app.services.page_fetch_service.socket.getaddrinfo",
            return_value=[(None, None, None, None, ("93.184.216.34", 80))],
        )
        self.public_dns.start()
        self.addCleanup(self.public_dns.stop)

    @staticmethod
    def response(
        *,
        body: bytes = b"",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            status_code=status_code,
            headers=headers or {"Content-Type": "text/html; charset=utf-8"},
            encoding="utf-8",
            iter_content=lambda chunk_size: iter([body]),
            raise_for_status=lambda: None,
            close=lambda: None,
        )

    @patch("app.services.page_fetch_service.requests.get")
    def test_fetches_readable_text_and_mailto_addresses(self, mock_get) -> None:
        mock_get.return_value = self.response(
            body=(
                b"<html><head><script>tracking code</script></head>"
                b"<body><h1>Contact</h1><p>Booking information</p>"
                b"<a href='mailto:booking@artist.example'>Email the team</a>"
                b"</body></html>"
            )
        )

        pages = fetch_contact_pages(["https://artist.example/contact"])

        self.assertEqual(len(pages), 1)
        self.assertIn("Contact", pages[0].text)
        self.assertIn("booking@artist.example", pages[0].text)
        self.assertNotIn("tracking code", pages[0].text)
        self.assertEqual(str(pages[0].source_url), "https://artist.example/contact")
        mock_get.assert_called_once()
        self.assertEqual(mock_get.call_args.kwargs["allow_redirects"], False)
        self.assertTrue(mock_get.call_args.kwargs["stream"])

    @patch("app.services.page_fetch_service.requests.get")
    def test_rejects_private_literal_ip_without_request(self, mock_get) -> None:
        with self.assertRaises(UnsafeTargetError):
            page_fetch_service._fetch_html("http://127.0.0.1/private")

        mock_get.assert_not_called()

    @patch("app.services.page_fetch_service.requests.get")
    @patch(
        "app.services.page_fetch_service.socket.getaddrinfo",
        return_value=[(None, None, None, None, ("10.0.0.8", 80))],
    )
    def test_rejects_hostname_resolving_to_private_ip(self, mock_dns, mock_get) -> None:
        pages = fetch_contact_pages(["https://internal.example/contact"])

        self.assertEqual(pages, [])
        mock_dns.assert_called_once()
        mock_get.assert_not_called()

    @patch("app.services.page_fetch_service.requests.get")
    def test_revalidates_redirect_target(self, mock_get) -> None:
        mock_get.return_value = self.response(
            status_code=302,
            headers={"Location": "http://127.0.0.1/admin"},
        )

        pages = fetch_contact_pages(["https://artist.example/contact"])

        self.assertEqual(pages, [])
        mock_get.assert_called_once()

    @patch("app.services.page_fetch_service.requests.get")
    def test_skips_non_html_and_oversized_pages(self, mock_get) -> None:
        mock_get.side_effect = [
            self.response(headers={"Content-Type": "application/pdf"}),
            self.response(
                body=b"a" * 11,
                headers={"Content-Type": "text/html", "Content-Length": "11"},
            ),
        ]

        with patch.object(page_fetch_service, "MAX_RESPONSE_BYTES", 10):
            pages = fetch_contact_pages(
                ["https://artist.example/file", "https://artist.example/large"]
            )

        self.assertEqual(pages, [])
        self.assertEqual(mock_get.call_count, 2)

    @patch("app.services.page_fetch_service.requests.get")
    def test_skips_individual_network_failures_and_continues(self, mock_get) -> None:
        mock_get.side_effect = [
            requests.Timeout("request timed out"),
            self.response(body=b"<p>Contact booking@artist.example</p>"),
        ]

        pages = fetch_contact_pages(
            ["https://artist.example/slow", "https://artist.example/contact"]
        )

        self.assertEqual(len(pages), 1)
        self.assertIn("booking@artist.example", pages[0].text)
        self.assertEqual(mock_get.call_count, 2)

    @patch("app.services.page_fetch_service.requests.get")
    def test_caps_number_of_url_attempts(self, mock_get) -> None:
        mock_get.side_effect = requests.Timeout("request timed out")
        urls = [f"https://artist.example/page-{index}" for index in range(10)]

        pages = fetch_contact_pages(urls)

        self.assertEqual(pages, [])
        self.assertEqual(mock_get.call_count, page_fetch_service.MAX_PAGES)


if __name__ == "__main__":
    unittest.main()
