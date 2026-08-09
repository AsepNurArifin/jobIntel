from __future__ import annotations

import time
from typing import Any

from app.config import Settings
from app.pipeline.embedder import encode

SOFT_SKILL_KEYWORDS = {
    "communication", "teamwork", "leadership", "collaboration", "adaptability",
    "problem solving", "critical thinking", "creativity", "time management",
    "organization", "negotiation", "mentoring", "coaching", "presentation",
    "empathy", "decision making", "flexibility", "initiative", "motivation",
    "attention to detail", "interpersonal", "conflict resolution",
    "active listening", "emotional intelligence", "resilience",
}


def categorize_label(label: str) -> str:
    """Klasifikasi sederhana hard/soft untuk seed ESCO (deviasi pragmatic plan)."""
    low = label.lower()
    if any(k in low for k in SOFT_SKILL_KEYWORDS):
        return "soft"
    return "hard"


def _match_by_alias(client: Any, raw: str) -> int | None:
    resp = (
        client.rpc("get_skill_id_by_alias", {"raw_name": raw})
        .execute()
    )
    return resp.data if resp.data else None


def _match_by_embedding(client: Any, raw: str, settings: Settings) -> int | None:
    vec = encode([raw], settings)[0]
    resp = client.rpc("find_closest_skill", {"qvec": vec, "threshold": settings.skill_match_threshold}).execute()
    return resp.data if resp.data else None


def _record_unmatched(client: Any, raw: str) -> None:
    try:
        client.table("unmatched_skills").upsert(
            {"raw_name": raw, "occurrences": 1},
            on_conflict="raw_name",
            ignore_duplicates=True,
        ).execute()
    except Exception:
        pass


async def run_normalization(client: Any, settings: Settings) -> int:
    """Mapping raw skills (hasil LLM) ke skill_ids via alias → embedding.

    Returns jumlah posting yang skill_ids-nya berhasil diisi.
    """
    rows = (
        client.table("extracted_requirements")
        .select("job_posting_id, hard_skills_raw, soft_skills_raw, tools_raw, skill_ids")
        .is_("skill_ids", "null")
        .limit(200)
        .execute()
    ).data or []

    n = 0
    for row in rows:
        raw_skills = [
            *(row.get("hard_skills_raw") or []),
            *(row.get("soft_skills_raw") or []),
            *(row.get("tools_raw") or []),
        ]
        ids: list[int] = []
        for raw in raw_skills:
            if not raw:
                continue
            raw = str(raw).strip().lower()
            skill_id = _match_by_alias(client, raw)
            if skill_id is None:
                skill_id = _match_by_embedding(client, raw, settings)
            if skill_id is not None:
                ids.append(int(skill_id))
            else:
                _record_unmatched(client, raw)
        # dedup ids & urutkan stabil
        seen: set[int] = set()
        unique_ids = [x for x in ids if not (x in seen or seen.add(x))]

        if unique_ids:
            client.table("extracted_requirements").update({"skill_ids": unique_ids}).eq(
                "job_posting_id", row["job_posting_id"]
            ).execute()
            n += 1
        time.sleep(0.03)
    return n
