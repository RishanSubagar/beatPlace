from __future__ import annotations

from typing import Any

from app.job_repository import create_research_result, get_recent_research_results, initialize_database
from app.services import serper_client


def build_research_query(person_name: str) -> str:
    return f'"{person_name}" profile OR team OR company'


def research_person(job_id: str, person_name: str) -> list[dict[str, Any]]:
    """
    Research a person. First checks cache (last 15 days), then calls Serper if not cached.
    Always inserts results for this job's tracking.
    """
    initialize_database()
    
    # Check if we have recent research results (within 15 days)
    cached_results = get_recent_research_results(person_name, days=15)
    
    if cached_results:
        print(f"[CACHE HIT] {person_name}: Using cached results from previous research")
        normalized = [
            {
                "title": result["title"] or "",
                "url": result["url"] or "",
                "description": result["description"] or "",
            }
            for result in cached_results
        ]
    else:
        print(f"[CACHE MISS] {person_name}: Calling Serper API")
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

    print(f"[RESEARCH] {person_name}: Found {len(normalized)} results")
    for i, result in enumerate(normalized, 1):
        print(f"  [{i}] {result['title']}")
        print(f"      URL: {result['url']}")
        desc_preview = result['description'][:100] + "..." if len(result['description']) > 100 else result['description']
        print(f"      Desc: {desc_preview}")

    # Always insert for this job (even if cached, we track per-job)
    for result in normalized:
        create_research_result(job_id, person_name, result["title"], result["url"], result["description"])

    return normalized
