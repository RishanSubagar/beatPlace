from __future__ import annotations

from typing import Any

from app.job_repository import create_research_result, initialize_database
from app.services import serper_client


def build_research_query(person_name: str) -> str:
    return f'"{person_name}" ("beat email" OR "send beats" OR "producer email" OR "email" OR "contact" OR "submissions" OR "@gmail.com")'


def research_person(job_id: str, person_name: str) -> list[dict[str, Any]]:
    initialize_database()
    raw_results = serper_client.fetch_serper_results(build_research_query(person_name))
    normalized = [
        {
            "title": result.get("title") or "",
            "url": result.get("url") or "",
            "description": result.get("description") or "",
        }
        for result in raw_results
        if result.get("url")
    ]

    print(f"[RESEARCH] {person_name}: Found {len(normalized)} normalized results")
    for i, result in enumerate(normalized, 1):
        print(f"  [{i}] {result['title']}")
        print(f"      URL: {result['url']}")
        desc_preview = result['description'][:100] + "..." if len(result['description']) > 100 else result['description']
        print(f"      Desc: {desc_preview}")

    for result in normalized:
        create_research_result(job_id, person_name, result["title"], result["url"], result["description"])

    return normalized
