"""Spot-check akurasi extraction (NFR-4). Usage:

    python -m scripts.validate_extraction --sample 10 --evidence
"""

from __future__ import annotations

import argparse
import asyncio
import json

from groq import Groq

from app.config import get_settings
from app.db import get_client
from app.pipeline.extractor import extract_one


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=10)
    parser.add_argument("--evidence", action="store_true", help="minta kutipan bukti per skill")
    parser.add_argument("--sql-filter", default=None, help="filter SQL tambahan (mis. source.eq.remoteok)")
    args = parser.parse_args()

    settings = get_settings()
    db = get_client()

    query = (
        db.table("job_postings")
        .select("id, title, raw_description")
        .eq("is_duplicate_of", "null")
        .limit(args.sample)
    )
    if args.sql_filter:
        query = query.filter(args.sql_filter)
    rows = query.execute().data or []

    groq = Groq(api_key=settings.groq_api_key)
    print(f"Spot-check {len(rows)} posting (evidence={args.evidence})")
    print("=" * 100)

    for row in rows:
        try:
            result = extract_one(
                groq,
                settings.groq_model,
                row.get("title", ""),
                row.get("raw_description", ""),
                max_chars=settings.max_description_chars,
                include_evidence=args.evidence,
            )
            print(f"\n#{row['id']} — {row.get('title', '')}")
            print(f"  hard: {result.hard_skills}")
            print(f"  soft: {result.soft_skills}")
            print(f"  tools: {result.tools}")
            print(f"  level={result.experience_level} years={result.min_years_experience} type={result.employment_type}")
        except Exception as exc:  # noqa: BLE001
            print(f"\n#{row['id']} — {row.get('title', '')}")
            print(f"  ERROR: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
