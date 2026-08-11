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


def _enrich_results(client, data: list[dict]) -> list[SearchResult]:
    """Gabungkan data search dengan deskripsi & requirements extraction (batch query)."""
    if not data:
        return []
    ids = [row["id"] for row in data]

    # Deskripsi mentah (raw_description) — batch fetch per posting
    desc_map: dict[int, str] = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        desc_rows = (
            client.table("job_postings")
            .select("id, raw_description")
            .in_("id", chunk)
            .execute()
        ).data or []
        desc_map.update({r["id"]: r.get("raw_description") or "" for r in desc_rows})

    # Requirements extraction — batch fetch
    req_map: dict[int, dict] = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i : i + 50]
        req_rows = (
            client.table("extracted_requirements")
            .select(
                "job_posting_id, hard_skills_raw, soft_skills_raw, tools_raw, "
                "experience_level, min_years_experience, employment_type"
            )
            .in_("job_posting_id", chunk)
            .execute()
        ).data or []
        req_map.update({r["job_posting_id"]: r for r in req_rows})

    # Skill names untuk semua ids sekaligus
    skill_name_map: dict[int, str] = {}
    skill_ids_to_fetch: set[int] = set()
    for pid, req in req_map.items():
        skill_ids_to_fetch.update(req.get("skill_ids") or [])
    if skill_ids_to_fetch:
        id_list = list(skill_ids_to_fetch)
        for i in range(0, len(id_list), 100):
            chunk = id_list[i : i + 100]
            srows = (
                client.table("skills")
                .select("id, canonical_name")
                .in_("id", chunk)
                .execute()
            ).data or []
            skill_name_map.update({s["id"]: s["canonical_name"] for s in srows})

    results: list[SearchResult] = []
    for row in data:
        pid = row["id"]
        req = req_map.get(pid, {})
        skill_ids = req.get("skill_ids") or []
        all_skills = [skill_name_map.get(sid) for sid in skill_ids]
        all_skills = [s for s in all_skills if s]
        results.append(
            SearchResult(
                id=pid,
                title=row["title"],
                company=row["company"],
                source=row["source"],
                source_url=row["source_url"],
                posted_date=row["posted_date"],
                location=row["location"],
                similarity=row["similarity"],
                top_skills=all_skills[:5],
                description=desc_map.get(pid, ""),
                hard_skills=req.get("hard_skills_raw") or [],
                soft_skills=req.get("soft_skills_raw") or [],
                tools=req.get("tools_raw") or [],
                experience_level=req.get("experience_level") or "unknown",
                min_years_experience=req.get("min_years_experience"),
                employment_type=req.get("employment_type") or "unknown",
            )
        )
    return results


@router.get("/search")
def search_jobs(
    q: str,
    days: int = 30,
    source: Literal["remoteok", "wwr", "adzuna", "all"] = "all",
    limit: int = 20,
    level: Literal["junior", "mid", "senior", ""] = "",
    employment_type: Literal["remote", "onsite", "hybrid", ""] = "",
) -> dict:
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
                "max_rows": limit * 3,  # over-fetch lalu filter level/type
            },
        ).execute()
    ).data or []

    results = _enrich_results(client, data)

    # Filter level & employment type (dari extraction)
    if level:
        results = [r for r in results if r.experience_level == level]
    if employment_type:
        results = [r for r in results if r.employment_type == employment_type]

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/jobs/{posting_id}")
def job_detail(posting_id: int) -> dict:
    client = get_client()

    job = (
        client.table("job_postings")
        .select("*")
        .eq("id", posting_id)
        .maybe_single()
        .execute()
    ).data
    if not job:
        raise HTTPException(status_code=404, detail="Loker tidak ditemukan")

    req = (
        client.table("extracted_requirements")
        .select(
            "hard_skills_raw, soft_skills_raw, tools_raw, "
            "experience_level, min_years_experience, employment_type, skill_ids"
        )
        .eq("job_posting_id", posting_id)
        .maybe_single()
        .execute()
    ).data or {}

    skill_ids = req.get("skill_ids") or []
    skill_names: list[str] = []
    if skill_ids:
        names = (
            client.table("skills")
            .select("canonical_name")
            .in_("id", skill_ids[:50])
            .execute()
        ).data or []
        skill_names = [s["canonical_name"] for s in names]

    return {
        "id": job["id"],
        "title": job.get("title", ""),
        "company": job.get("company"),
        "source": job.get("source"),
        "source_url": job.get("source_url"),
        "posted_date": job.get("posted_date"),
        "location": job.get("location"),
        "description": job.get("raw_description") or "",
        "hard_skills": req.get("hard_skills_raw") or [],
        "soft_skills": req.get("soft_skills_raw") or [],
        "tools": req.get("tools_raw") or [],
        "top_skills": skill_names,
        "experience_level": req.get("experience_level") or "unknown",
        "min_years_experience": req.get("min_years_experience"),
        "employment_type": req.get("employment_type") or "unknown",
    }
