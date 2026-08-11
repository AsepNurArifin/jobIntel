from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from app.config import get_settings
from app.db import get_client
from app.pipeline.embedder import encode

router = APIRouter(prefix="/api", tags=["skills"])


@router.get("/skills/top", response_model=dict)
def skills_top(
    days: int = 30,
    role: str | None = None,
    category: Literal["hard", "soft", "tool"] | None = None,
    limit: int = 20,
) -> dict:
    settings = get_settings()
    client = get_client()

    role_vec = encode([role], settings)[0] if role else None

    data = (
        client.rpc(
            "top_skills",
            {
                "max_days": days,
                "role_vec": role_vec,
                "cat": category,
                "max_rows": limit,
            },
        ).execute()
    ).data or []

    # n_postings: jumlah posting dalam filter tanggal + role (konsisten dengan RPC top_skills).
    # Tanpa akses SQL untuk membuat RPC count baru, gunakan fungsi existing:
    #   - role filter: search_jobs (predikat identik dengan filter role di top_skills)
    #   - tanpa role: count_postings_in_days (existing)
    if role_vec is not None:
        rows = (
            client.rpc(
                "search_jobs",
                {
                    "qvec": role_vec,
                    "search_threshold": 0.25,
                    "max_days": days,
                    "src": "all",
                    "max_rows": 5000,
                },
            ).execute()
        ).data or []
        n_postings = len(rows)
    else:
        count_data = (
            client.rpc("count_postings_in_days", {"max_days": days}).execute()
        ).data
        n_postings = int(count_data) if count_data else 0

    return {
        "filters": {"days": days, "role": role, "category": category},
        "n_postings": n_postings,
        "skills": [
            {"name": row["name"], "category": row["category"], "freq": int(row["freq"])}
            for row in data
        ],
    }
