from __future__ import annotations

import json
import os
from typing import Any

import requests

SERPER_API_URL = "https://google.serper.dev/search"


def fetch_serper_results(query: str) -> list[dict[str, Any]]:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY is required")

    payload = json.dumps({"q": query, "num": 10})
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    print(f"[SERPER] Query: {query}")
    response = requests.post(SERPER_API_URL, headers=headers, data=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    print(f"[SERPER] Raw response: {json.dumps(data, indent=2)}")

    return [
        {
            "title": item.get("title"),
            "url": item.get("link"),
            "description": item.get("snippet"),
        }
        for item in data.get("organic", [])
        if item.get("title") and item.get("link")
    ]
