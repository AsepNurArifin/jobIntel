"""Seed tabel skills dari ESCO labels + alias table.

Usage:
    python -m scripts.seed_skills

Sumber data:
  - data/esco/skills_en_label.txt  (13.896 label ESCO, satu per baris)
  - data/alias_table.csv            (alias tech custom: canonical,alias,...)

Deviasi pragmatic dari plan: karena CSV ESCO resmi (dengan kategori & altLabels)
terhalang redirect-session, MVP memakai label ESCO sebagai canonical_name dan
mengklasifikasi hard/soft via keyword sederhana. ESCO penuh = perbaikan Fase 2.
"""

from __future__ import annotations

import csv
import pathlib
import time

from app.config import get_settings
from app.db import get_client
from app.pipeline.embedder import encode
from app.pipeline.normalizer import categorize_label

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
ESCO_LABELS = DATA_DIR / "esco" / "skills_en_label.txt"
ALIAS_CSV = DATA_DIR / "alias_table.csv"


def _load_esco_labels() -> list[str]:
    if not ESCO_LABELS.exists():
        print(f"WARN: {ESCO_LABELS} tidak ada — skip label ESCO")
        return []
    lines = ESCO_LABELS.read_text(encoding="utf-8").splitlines()
    out = [ln.strip() for ln in lines if ln.strip()]
    print(f"ESCO labels: {len(out)}")
    return out


def _load_aliases() -> dict[str, str]:
    """alias (lowercase) → canonical_name (lowercase)."""
    if not ALIAS_CSV.exists():
        print(f"WARN: {ALIAS_CSV} tidak ada — tanpa custom alias")
        return {}
    mapping: dict[str, str] = {}
    with ALIAS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or not row[0]:
                continue
            canonical = row[0].strip().lower()
            for alias in row[1:]:
                a = alias.strip().lower()
                if a:
                    mapping[a] = canonical
    print(f"Alias mappings: {len(mapping)}")
    return mapping


def main() -> None:
    settings = get_settings()
    client = get_client()

    esco_labels = _load_esco_labels()
    alias_map = _load_aliases()

    # Kumpulkan semua canonical name (ESCO + canonical dari alias table)
    canonical_names: dict[str, str] = {}  # name -> origin
    for label in esco_labels:
        canonical_names[label.lower()] = "esco"
    for canonical in alias_map.values():
        canonical_names.setdefault(canonical, "custom_alias")

    names = list(canonical_names.keys())
    print(f"Total canonical skill: {len(names)}")

    # Precompute embedding dalam batch
    print("Encoding embeddings (ini bisa beberapa menit)...")
    vectors = encode(names, settings)

    inserted = 0
    updated = 0
    BATCH = 100
    for i in range(0, len(names), BATCH):
        chunk_names = names[i : i + BATCH]
        chunk_vecs = vectors[i : i + BATCH]
        rows = []
        for name, vec in zip(chunk_names, chunk_vecs):
            origin = canonical_names[name]
            aliases = [a for a, c in alias_map.items() if c == name]
            rows.append(
                {
                    "canonical_name": name,
                    "category": categorize_label(name),
                    "aliases": aliases,
                    "origin": origin,
                    "embedding": vec,
                }
            )
        data = (
            client.table("skills")
            .upsert(rows, on_conflict="canonical_name")
            .execute()
        ).data or []
        inserted += len(data)
        updated += len(chunk_names) - len(data)
        time.sleep(0.1)

    print(f"Selesai. inserted={inserted} (updated/matched={updated})")
    print("Verifikasi: SELECT count(*) FROM skills;")


if __name__ == "__main__":
    main()
