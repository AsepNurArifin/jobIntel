"""Eksperimen threshold (plan §13). Jalankan setelah data riil ada.

Usage:
    python -m scripts.validate_thresholds --queries "data scientist,backend python,ml engineer"
    python -m scripts.validate_thresholds --skill-sample 50
"""

from __future__ import annotations

import argparse
import asyncio

from app.config import get_settings
from app.db import get_client
from app.pipeline.embedder import encode


async def _validate_search(queries: list[str]) -> None:
    settings = get_settings()
    client = get_client()
    print("VALIDASI SEARCH_THRESHOLD")
    print("=" * 80)
    for q in queries:
        vec = encode([q], settings)[0]
        data = (
            client.rpc(
                "search_jobs",
                {
                    "qvec": vec,
                    "search_threshold": 0.0,
                    "max_days": 90,
                    "src": "all",
                    "max_rows": 15,
                },
            ).execute()
        ).data or []
        print(f"\nQuery: {q!r}")
        for row in data:
            marker = "  " if row["similarity"] >= settings.search_threshold else " <"
            print(f"  [{row['similarity']:.3f}]{marker} {row['title']} @ {row['company']}")


async def _validate_skill_match(sample: int) -> None:
    settings = get_settings()
    client = get_client()
    print(f"\nVALIDASI SKILL_MATCH_THRESHOLD (sample={sample})")
    print("=" * 80)
    rows = (
        client.table("extracted_requirements")
        .select("hard_skills_raw, soft_skills_raw, tools_raw")
        .not_.is_("hard_skills_raw", "null")
        .limit(sample)
        .execute()
    ).data or []

    raw_skills = []
    for row in rows:
        raw_skills.extend(row.get("hard_skills_raw") or [])
        raw_skills.extend(row.get("soft_skills_raw") or [])
        raw_skills.extend(row.get("tools_raw") or [])
    raw_skills = list(dict.fromkeys(raw_skills))[:sample]

    for threshold in (0.70, 0.75, 0.80, 0.85, 0.90):
        matched = 0
        vecs = encode(raw_skills, settings)
        for raw, vec in zip(raw_skills, vecs):
            res = client.rpc("find_closest_skill", {"qvec": vec, "threshold": threshold}).execute()
            if res.data:
                matched += 1
        print(f"  threshold={threshold:.2f}: matched {matched}/{len(raw_skills)} ({matched/len(raw_skills):.0%})")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", default="data scientist,backend python,machine learning engineer,devops")
    parser.add_argument("--skill-sample", type=int, default=50)
    args = parser.parse_args()
    await _validate_search([q.strip() for q in args.queries.split(",") if q.strip()])
    await _validate_skill_match(args.skill_sample)


if __name__ == "__main__":
    asyncio.run(main())
