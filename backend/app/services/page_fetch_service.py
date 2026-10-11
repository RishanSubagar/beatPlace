from __future__ import annotations

import ipaddress
import socket
from collections.abc import Iterable
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from pydantic import ValidationError

from app.models import ContactSourcePage

MAX_PAGES = 5
MAX_RESPONSE_BYTES = 2_000_000
MAX_PAGE_TEXT_CHARS = 30_000
MAX_REDIRECTS = 3
REQUEST_TIMEOUT_SECONDS = (3.05, 8)
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
HTML_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}


class UnsafeTargetError(ValueError):
    """Raised when a URL could target a non-public network address."""


def _validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeTargetError("only absolute HTTP(S) URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeTargetError("URLs with embedded credentials are not allowed")

    hostname = parsed.hostname.rstrip(".")
    try:
        literal_address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            addresses = {
                ipaddress.ip_address(info[4][0])
                for info in socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
            }
        except (OSError, ValueError) as error:
            raise UnsafeTargetError("hostname could not be resolved safely") from error
    else:
        addresses = {literal_address}

    if not addresses or any(not address.is_global for address in addresses):
        raise UnsafeTargetError("URL must resolve only to public IP addresses")


def _read_limited_response(response: requests.Response) -> bytes:
    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = 0
        if declared_size > MAX_RESPONSE_BYTES:
            raise ValueError("response exceeds the maximum download size")

    body = bytearray()
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        body.extend(chunk)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("response exceeds the maximum download size")
    return bytes(body)


def _fetch_html(url: str) -> tuple[str, str, str] | None:
    current_url = url

    for redirect_count in range(MAX_REDIRECTS + 1):
        _validate_public_url(current_url)
        response = requests.get(
            current_url,
            headers={"User-Agent": "BeatPlaceContactResearch/1.0"},
            timeout=REQUEST_TIMEOUT_SECONDS,
            stream=True,
            allow_redirects=False,
        )
        try:
            if response.status_code in REDIRECT_STATUSES:
                location = response.headers.get("Location")
                if not location or redirect_count == MAX_REDIRECTS:
                    return None
                current_url = urljoin(current_url, location)
                continue

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type not in HTML_CONTENT_TYPES:
                return None

            content = _read_limited_response(response)
            encoding = response.encoding or "utf-8"
            return current_url, content.decode(encoding, errors="replace"), content_type
        finally:
            response.close()

    return None


def _extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript", "svg", "template"]):
        element.decompose()

    text_parts = [soup.get_text(" ", strip=True)]
    for link in soup.select('a[href^="mailto:"]'):
        address = link.get("href", "")[len("mailto:"):].split("?", 1)[0].strip()
        if address:
            text_parts.append(f"Email: {address}")

    return "\n".join(part for part in text_parts if part)[:MAX_PAGE_TEXT_CHARS]


def fetch_contact_pages(urls: Iterable[str]) -> list[ContactSourcePage]:
    """Fetch up to five public HTML pages and return bounded, readable text.

    Individual URL failures are skipped so one unavailable search result does
    not prevent processing the remaining pages.
    """
    pages: list[ContactSourcePage] = []
    seen_urls: set[str] = set()
    attempted_urls = 0

    for url in urls:
        if attempted_urls >= MAX_PAGES:
            break
        if url in seen_urls:
            continue
        seen_urls.add(url)
        attempted_urls += 1

        try:
            fetched = _fetch_html(url)
            if fetched is None:
                continue
            final_url, html, _content_type = fetched
            text = _extract_page_text(html)
            if not text:
                continue
            pages.append(ContactSourcePage(source_url=final_url, text=text))
        except (requests.RequestException, UnsafeTargetError, ValidationError, ValueError) as error:
            print(f"[PAGE_FETCH] Skipping {url}: {error}")

    return pages