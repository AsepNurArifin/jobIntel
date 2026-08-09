# JobIntel Backend — Search API & Pipeline

Personal IT job aggregator & market intelligence. Backend ini berisi: source
adapters (RemoteOK + WeWorkRemotely), pipeline ekstraksi/normalisasi/embedding,
semantic search (pgvector), dan ranking skill.

Dokumen acuan: `../plan.md` (plan eksekusi) dan `../PRD_SRS_JobIntel.md` (produk).

## Prasyarat

- Python 3.12+ (disarankan via `uv`)
- Akun Supabase (free tier) — untuk Postgres + pgvector
- Groq API key — untuk LLM extraction

## Setup (dari nol)

```powershell
cd backend

# 1. Install dependencies
uv sync

# 2. Konfigurasi
Copy-Item .env.example .env
# isi SUPABASE_URL, SUPABASE_SERVICE_KEY, GROQ_API_KEY di .env

# 3. Inisialisasi database
#    Buka Supabase → SQL Editor → jalankan isi scripts/init_db.sql

# 4. Seed kamus skill (ESCO labels + alias table) + precompute embedding
#    Data ESCO: taruh data/esco/skills_en_label.txt
#    (download: Skill-Extraction-benchmark repo / data/skills_en_label.txt)
uv run python -m scripts.seed_skills
```

## Menjalankan API

```powershell
uv run uvicorn app.main:app --reload --port 8000
```

- Health: `GET http://localhost:8000/health`
- Docs: `http://localhost:8000/docs`

## Menjalankan pipeline (manual)

Pipeline bisa di-trigger manual tanpa menunggu jadwal harian:

```powershell
# Semua step, semua sumber
uv run python -m scripts.run_pipeline

# Hanya fetch dari RemoteOK
uv run python -m scripts.run_pipeline --step fetch --source remoteok

# Hanya extraction
uv run python -m scripts.run_pipeline --step extract
```

Step pipeline: `fetch` → `dedup` → `extract` → `normalize` → `embed`.

## Scheduler otomatis (haris harian)

Set `SCHEDULER_ENABLED=true` dan `FETCH_CRON_HOUR=6` di `.env`, lalu jalan biasa:

```powershell
uv run uvicorn app.main:app --port 8000
```

Scheduler (APScheduler, in-process) akan men-trigger `run_pipeline()` setiap
hari pada jam yang dikonfigurasi. Default `SCHEDULER_ENABLED=false` agar dev
tidak terpicu otomatis.

## Spot-check kualitas extraction (NFR-4)

```powershell
# Sample 10 posting, minta bukti (kutipan) per skill
uv run python -m scripts.validate_extraction --sample 10 --evidence
```

Review manual: pastikan skill yang diekstrak ≥ 80% valid (muncul eksplisit di
deskripsi). Jika prompt kurang akurat, refine di `app/pipeline/extractor.py`
dan naikkan `EXTRACTION_VERSION` di `.env` → re-run extract (hanya versi
outdated yang diproses ulang).

## Validasi threshold (plan §13)

```powershell
uv run python -m scripts.validate_thresholds --queries "data scientist,backend python,ml engineer"
uv run python -m scripts.validate_thresholds --skill-sample 50
```

Hasilnya menentukan nilai final `SEARCH_THRESHOLD` & `SKILL_MATCH_THRESHOLD`
di `.env`. Nilai di `.env.example` hanyalah titik mula eksperimen.

## Test

```powershell
uv run pytest
```

## Struktur penting

```
app/adapters/          # source adapters (terisolasi per sumber)
app/pipeline/          # orchestrator + extractor/normalizer/embedder/dedup
app/api/               # FastAPI routes (/api/search, /api/skills/top)
scripts/               # init_db.sql, seed, run_pipeline, validations
data/                  # ESCO labels + alias_table.csv
```

## Frontend

Frontend (Nuxt 3) ada di `../frontend`. Konsumsi API ini via
`runtimeConfig.public.apiBaseUrl` (default `http://localhost:8000`).
