"""Seed tabel skills dari whitelist tech + ESCO labels yang relevan + alias table.

Usage:
    python -m scripts.seed_skills

Sumber data (prioritas):
  1. data/tech_whitelist.csv   — kamus inti IT (canonical,aliases...,category).
                                 canonical wajib; kategori hard/soft/tool eksplisit.
  2. data/alias_table.csv      — alias tech custom (kanonik lama, dipertahankan).
  3. data/esco/skills_en_label.txt — label ESCO yang MATCH whitelist/kata kunci IT,
                                 dimasukkan sebagai hard skill pelengkap.

Label ESCO yang tidak relevan IT (seluruh 13.896) tidak lagi dimasukkan mentah —
menghilangkan noise seperti "curl hair", "advise on hair style", "accounting".
"""

from __future__ import annotations

import csv
import pathlib
import re
import time

from app.config import get_settings
from app.db import get_client
from app.pipeline.embedder import encode

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
TECH_WHITELIST = DATA_DIR / "tech_whitelist.csv"
ALIAS_CSV = DATA_DIR / "alias_table.csv"
ESCO_LABELS = DATA_DIR / "esco" / "skills_en_label.txt"

# Kata kunci yang menandakan label ESCO relevan-IT (kalau tidak cocok whitelist).
ESCO_IT_KEYWORDS = [
    "software", "program", "code", "coding", "script", "database", "data ",
    "analys", "engineer", "algorithm", "api", "web", "frontend", "front-end",
    "backend", "back-end", "full stack", "cloud", "network", "security",
    "cyber", "devops", "testing", "test ", "deploy", "container", "machine learning",
    "artificial intelligence", "computer", "system ", "information technology",
    "digital", "app development", "mobile", "ux", "ui ", "product design",
    "cybersecurity", "infrastructure", "server", "architecture",
    "integration", "automation", "robotics", "database", "query", "sql",
    "programming", "web develop", "frontend", "backend",
]

SOFT_SKILL_KEYWORDS = {
    "communication", "teamwork", "leadership", "collaboration", "adaptability",
    "problem solving", "critical thinking", "creativity", "time management",
    "organization", "negotiation", "mentoring", "coaching", "presentation",
    "empathy", "decision making", "flexibility", "initiative", "motivation",
    "attention to detail", "interpersonal", "conflict resolution",
    "active listening", "emotional intelligence", "resilience",
}


def _load_tech_whitelist() -> list[tuple[str, list[str], str]]:
    """Load whitelist: list of (canonical, aliases, category)."""
    if not TECH_WHITELIST.exists():
        print(f"WARN: {TECH_WHITELIST} tidak ada")
        return []
    rows: list[tuple[str, list[str], str]] = []
    with TECH_WHITELIST.open(newline="", encoding="utf-8") as f:
        for line in f:
            row = next(csv.reader([line]))
            if not row or not row[0]:
                continue
            canonical = row[0].strip().lower()
            category = row[-1].strip().lower() if len(row) > 2 else "hard"
            if category not in ("hard", "soft", "tool"):
                category = "hard"
            aliases = [a.strip().lower() for a in row[1:-1] if a.strip()]
            rows.append((canonical, aliases, category))
    print(f"Tech whitelist entries: {len(rows)}")
    return rows


def _load_aliases() -> dict[str, str]:
    """alias (lowercase) → canonical_name (lowercase) dari alias_table.csv lama."""
    if not ALIAS_CSV.exists():
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
    print(f"Alias (legacy) mappings: {len(mapping)}")
    return mapping


def _esco_relevant(name: str, whitelist_names: set[str]) -> bool:
    """Apakah label ESCO layak masuk sebagai skill IT pelengkap."""
    low = name.lower()
    if low in whitelist_names:
        return True
    return any(k in low for k in ESCO_IT_KEYWORDS)


def _load_esco_relevant(whitelist_names: set[str]) -> list[str]:
    if not ESCO_LABELS.exists():
        print(f"WARN: {ESCO_LABELS} tidak ada — tanpa pelengkap ESCO")
        return []
    lines = ESCO_LABELS.read_text(encoding="utf-8").splitlines()
    relevant = [ln.strip() for ln in lines if ln.strip() and _esco_relevant(ln, whitelist_names)]
    print(f"ESCO labels: {len(lines)} baris -> relevan-IT: {len(relevant)}")
    return relevant


def categorize_label(label: str) -> str:
    """Klasifikasi hard/soft untuk seed ESCO (label ESCO pelengkap, bukan whitelist)."""
    low = label.lower()
    if any(k in low for k in SOFT_SKILL_KEYWORDS):
        return "soft"
    return "hard"


def main() -> None:
    settings = get_settings()
    client = get_client()

    whitelist = _load_tech_whitelist()
    alias_map = _load_aliases()

    # Build skill set: canonical -> (aliases, category, origin)
    skills: dict[str, dict] = {}
    for canonical, aliases, category in whitelist:
        skills.setdefault(
            canonical,
            {"aliases": set(), "category": category, "origin": "custom_alias"},
        )["aliases"].update(aliases)
    whitelist_names = set(skills.keys())

    # Tambahkan ESCO labels relevan (hard/soft heuristik)
    for label in _load_esco_relevant(whitelist_names):
        low = label.lower()
        if low not in skills:
            skills[low] = {
                "aliases": set(),
                "category": categorize_label(low),
                "origin": "esco",
            }

    # Alias legacy map ke canonical yang sudah ada; bila belum ada, tambahkan.
    for alias, canonical in alias_map.items():
        if canonical in skills:
            skills[canonical]["aliases"].add(alias)
        else:
            skills[canonical] = {
                "aliases": {alias},
                "category": "hard",
                "origin": "custom_alias",
            }

    names = list(skills.keys())
    print(f"Total canonical skill: {len(names)}")

    # Hapus skill lama yang tidak lagi ada di kamus baru (noise seperti "curl hair").
    # Hanya hapus yang TIDAK direferensikan extracted_requirements.skill_ids.
    all_old = (
        client.table("skills").select("id, canonical_name").limit(5000).execute()
    ).data or []
    keep_names = set(names)
    stale_ids = [row["id"] for row in all_old if row["canonical_name"] not in keep_names]
    # Batasi per batch & lindungi referensi skill_ids (hapus hanya bila tidak dipakai)
    deleted = 0
    if stale_ids:
        referenced = set()
        page = 0
        while True:
            er = (
                client.table("extracted_requirements")
                .select("skill_ids")
                .range(page * 200, (page + 1) * 200 - 1)
                .execute()
            ).data or []
            for row in er:
                referenced.update(row.get("skill_ids") or [])
            if len(er) < 200:
                break
            page += 1
        deletable = [sid for sid in stale_ids if sid not in referenced]
        BATCH_DEL = 500
        for i in range(0, len(deletable), BATCH_DEL):
            chunk = deletable[i : i + BATCH_DEL]
            try:
                client.table("skills").delete().in_("id", chunk).execute()
                deleted += len(chunk)
            except Exception:
                pass
            time.sleep(0.1)
    print(f"Deleted stale skills: {deleted}")

    print("Encoding embeddings (bisa beberapa menit)...")
    vectors = encode(names, settings)

    inserted = 0
    BATCH = 100
    for i in range(0, len(names), BATCH):
        chunk_names = names[i : i + BATCH]
        chunk_vecs = vectors[i : i + BATCH]
        rows = []
        for name, vec in zip(chunk_names, chunk_vecs):
            meta = skills[name]
            rows.append(
                {
                    "canonical_name": name,
                    "category": meta["category"],
                    "aliases": sorted(meta["aliases"]),
                    "origin": meta["origin"],
                    "embedding": vec,
                }
            )
        data = (
            client.table("skills")
            .upsert(rows, on_conflict="canonical_name")
            .execute()
        ).data or []
        inserted += len(data)
        time.sleep(0.1)

    print(f"Selesai. upserted={inserted} rows (total kanonik {len(names)})")
    print("Verifikasi: SELECT category, count(*) FROM skills GROUP BY category;")


if __name__ == "__main__":
    main()
