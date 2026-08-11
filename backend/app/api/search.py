from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.db import get_client
from app.models import SearchResult
from app.pipeline.embedder import encode

router = APIRouter(prefix="/api", tags=["search"])


def _top_skills(client, posting_id: int, limit: int = 5) -> list[str]:
    resp = (
        client.table("extracted_requirements")
        .select("skill_ids")
        .eq("job_posting_id", posting_id)
        .execute()
    ).data
    if not resp or not resp[0].get("skill_ids"):
        return []
    ids = resp[0]["skill_ids"][:limit]
    names = (
        client.table("skills")
        .select("id, canonical_name")
        .in_("id", ids)
        .execute()
    ).data or []
    by_id = {s["id"]: s["canonical_name"] for s in names}
    return [by_id[i] for i in ids if i in by_id]


@router.get("/search", response_model=list[SearchResult])
def search_jobs(
    q: str,
    days: int = 30,
    source: Literal["remoteok", "wwr", "all"] = "all",
    limit: int = 20,
) -> list[SearchResult]:
    settings = get_settings()
    client = get_client()

    if limit > 100:
        raise HTTPException(status_code=422, detail="limit max 100")
    if not q.strip():
        raise HTTPException(status_code=422, detail="q tidak boleh kosong")

    vec = encode([q], settings)[0]
    data = (
        client.rpc(
            "search_jobs",
            {
                "qvec": vec,
                "search_threshold": settings.search_threshold,
                "max_days": days,
                "src": source,
                "max_rows": limit,
            },
        ).execute()
    ).data or []

    results: list[SearchResult] = []
    for row in data:
        results.append(
            SearchResult(
                id=row["id"],
                title=row["title"],
                company=row["company"],
                source=row["source"],
                source_url=row["source_url"],
                posted_date=row["posted_date"],
                location=row["location"],
                similarity=row["similarity"],
                top_skills=_top_skills(client, row["id"]),
            )
        )
    return results
