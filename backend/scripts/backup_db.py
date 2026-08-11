"""Backup darurat tabel inti ke file JSON lokal (sebelum re-seed/re-normalize)."""
import json
import pathlib
import sys
import time

sys.path.insert(0, ".")

from app.db import get_client

OUT = pathlib.Path("data/backup_audit")
OUT.mkdir(parents=True, exist_ok=True)

client = get_client()

TABLES = ["job_postings", "extracted_requirements", "skills", "unmatched_skills"]


def fetch_all(table: str) -> list:
    rows: list = []
    page = 0
    per = 1000
    while True:
        resp = (
            client.table(table)
            .select("*")
            .range(page * per, (page + 1) * per - 1)
            .execute()
        )
        data = resp.data or []
        rows.extend(data)
        if len(data) < per:
            break
        page += 1
        time.sleep(0.1)
    return rows


for t in TABLES:
    rows = fetch_all(t)
    (OUT / f"{t}.json").write_text(
        json.dumps(rows, indent=1, default=str), encoding="utf-8"
    )
    print(f"{t}: {len(rows)} rows -> {OUT / (t + '.json')}")

print("BACKUP SELESAI")
