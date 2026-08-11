from __future__ import annotations

import re
import time
from typing import Any

from app.models import RawJob


def _normalize_key(*parts: str | None) -> str:
    """Kunci kanonik untuk dedup: lowercase, hapus punctuation, rapikan spasi."""
    joined = " ".join(p or "" for p in parts)
    joined = joined.lower()
    joined = re.sub(r"[^\w\s]", " ", joined, flags=re.UNICODE)
    return re.sub(r"\s+", " ", joined).strip()


def upsert_raw_jobs(client: Any, jobs: list[RawJob]) -> int:
    """Insert raw jobs ke job_postings, skip yang sudah ada (idempotent).

    Menggunakan UNIQUE(source, source_id) → on conflict do nothing.
    Returns jumlah row yang benar-benar di-insert.
    """
    if not jobs:
        return 0

    rows = [
        {
            "source": j.source,
            "source_id": j.source_id,
            "title": j.title,
            "company": j.company,
            "source_url": j.source_url,
            "raw_description": j.raw_description,
            "location": j.location,
            "posted_date": j.posted_date.isoformat() if j.posted_date else None,
        }
        for j in jobs
    ]

    inserted = 0
    batch = 200
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        # Pre-check existing (batched) untuk menghindari ambiguitas hasil upsert
        # ignore_duplicates lintas versi PostgREST; hanya insert yang belum ada.
        try:
            existing = (
                client.table("job_postings")
                .select("source, source_id")
                .in_("source_id", [r["source_id"] for r in chunk])
                .execute()
            ).data or []
            existing_keys = {(e["source"], e["source_id"]) for e in existing}
        except Exception:
            existing_keys = set()
        fresh = [r for r in chunk if (r["source"], r["source_id"]) not in existing_keys]
        if not fresh:
            continue
        try:
            data = (
                client.table("job_postings")
                .upsert(fresh, on_conflict="source,source_id", ignore_duplicates=True)
                .execute()
            )
            if data.data:
                inserted += len(data.data)
        except Exception:
            for row in fresh:
                try:
                    res = (
                        client.table("job_postings")
                        .upsert([row], on_conflict="source,source_id", ignore_duplicates=True)
                        .execute()
                    )
                    if res.data:
                        inserted += 1
                except Exception:
                    continue
        time.sleep(0.05)
    return inserted


def run_dedup(client: Any, window_days: int = 90) -> int:
    """Flag posting yang sama muncul di sumber berbeda (normalized title+company).

    Hanya memproses posting tanpa is_duplicate_of, dan hanya menandai duplikat
    terhadap posting yang `is_duplicate_of IS NULL` (root) — bukan rantai.

    Terbatas pada posting dalam `window_days` terakhir agar tidak memuat seluruh
    tabel (PostgREST default limit ~1000 rows) — batas skala plan §2.3.
    """
    flagged = 0
    from datetime import datetime, timedelta, timezone

    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
    # Ambil semua posting yang belum di-flag, root dan kandidat duplikat.
    resp = (
        client.table("job_postings")
        .select("id, source, title, company, is_duplicate_of")
        .is_("is_duplicate_of", "null")
        .gte("fetched_at", cutoff)
        .execute()
    )
    if not resp.data:
        return 0

    by_key: dict[str, list[dict]] = {}
    for row in resp.data:
        key = _normalize_key(row.get("title"), row.get("company"))
        if not key:
            continue
        by_key.setdefault(key, []).append(row)

    for key, rows in by_key.items():
        if len(rows) < 2:
            continue
        # Root = yang paling lama (id terkecil); sisanya duplikat.
        rows_sorted = sorted(rows, key=lambda r: r["id"])
        root_id = rows_sorted[0]["id"]
        for row in rows_sorted[1:]:
            if row["source"] == rows_sorted[0]["source"]:
                # Posting sama dari sumber sama sudah dicegah UNIQUE;
                # kalau kunci sama beda source, ini duplikat lintas sumber.
                continue
            try:
                client.table("job_postings").update({"is_duplicate_of": root_id}).eq(
                    "id", row["id"]
                ).execute()
                flagged += 1
            except Exception:
                continue
    return flagged
