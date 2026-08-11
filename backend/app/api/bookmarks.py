from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import get_client

router = APIRouter(prefix="/api", tags=["bookmarks"])


@router.get("/bookmarks")
def list_bookmarks() -> dict:
    client = get_client()
    rows = (
        client.table("bookmarks")
        .select("id, job_posting_id, created_at")
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    ).data or []
    ids = [r["job_posting_id"] for r in rows]

    jobs = {}
    if ids:
        for i in range(0, len(ids), 50):
            chunk = ids[i : i + 50]
            postings = (
                client.table("job_postings")
                .select("id, title, company, source, source_url, posted_date, location, raw_description")
                .in_("id", chunk)
                .execute()
            ).data or []
            for p in postings:
                p["similarity"] = 1.0
                p["top_skills"] = []
                p["description"] = p.get("raw_description") or ""
                jobs[p["id"]] = p

    results = []
    for r in rows:
        pid = r["job_posting_id"]
        job = jobs.get(pid)
        if job:
            results.append(job)

    return {"count": len(results), "results": results}


@router.post("/bookmarks")
def add_bookmark(posting_id: int) -> dict:
    client = get_client()
    # Pastikan posting ada
    exists = (
        client.table("job_postings").select("id").eq("id", posting_id).execute()
    ).data
    if not exists:
        raise HTTPException(status_code=404, detail="Loker tidak ditemukan")
    try:
        data = (
            client.table("bookmarks").insert({"job_posting_id": posting_id}).execute()
        ).data or []
        return {"status": "saved", "bookmark": data[0] if data else None}
    except Exception:
        # Duplikat / already bookmarked
        return {"status": "exists"}


@router.delete("/bookmarks/{posting_id}")
def remove_bookmark(posting_id: int) -> dict:
    client = get_client()
    client.table("bookmarks").delete().eq("job_posting_id", posting_id).execute()
    return {"status": "removed"}
