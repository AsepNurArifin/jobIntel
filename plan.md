# Plan — JobIntel MVP Implementation Plan

> **Dokumen induk eksekusi.** Semua keputusan teknis yang sudah dikunci, spesifikasi detail per komponen, kontrak API, roadmap bertahap, dan kriteria kelulusan terdokumentasi di sini. Dokumen ini menjadi satu-satunya referensi selama implementasi — kalau ada deviasi saat coding, update dokumen ini dulu, baru kode mengikuti.
>
> **Berdasarkan:** `PRD_SRS_JobIntel.md` v0.1 (9 Agustus 2026) + hasil analisis/investigasi arsitektur & flow bisnis + kesepakatan implementasi.
> **Status:** Siap eksekusi. **Tanggal:** 9 Agustus 2026.
> **Mode kerja:** Single-developer (Asep) dibantu AI agent. Local-first, Windows environment.

---

## Daftar Isi

- [0. Keputusan yang Sudah Dikunci (Final)](#0-keputusan-yang-sudah-dikunci-final)
- [1. Prinsip Implementasi](#1-prinsip-implementasi)
- [2. Arsitektur Final](#2-arsitektur-final)
- [3. Prasyarat & Setup Awal (Tahap 0 Detil)](#3-prasyarat--setup-awal-tahap-0-detil)
- [4. Struktur Folder Lengkap](#4-struktur-folder-lengkap)
- [5. Skema Database Lengkap](#5-skema-database-lengkap)
- [6. Spesifikasi Komponen Backend](#6-spesifikasi-komponen-backend)
- [7. Kontrak API (Request/Response)](#7-kontrak-api-requestresponse)
- [8. Spesifikasi Frontend](#8-spesifikasi-frontend)
- [9. Konfigurasi & Environment](#9-konfigurasi--environment)
- [10. Dependencies (Pinned)](#10-dependencies-pinned)
- [11. Roadmap Eksekusi 9 Tahap (Task-by-Task)](#11-roadmap-eksekusi-9-tahap-task-by-task)
- [12. Risiko & Mitigasi Operasional](#12-risiko--mitigasi-operasional)
- [13. Protokol Validasi Empiris (Threshold)](#13-protokol-validasi-empiris-threshold)
- [14. Definition of Done — MVP](#14-definition-of-done--mvp)
- [15. Di Luar Scope](#15-di-luar-scope)
- [Lampiran A: Inventaris File yang Akan Dibuat](#lampiran-a-inventaris-file-yang-akan-dibuat)
- [Lampiran B: Glosarium](#lampiran-b-glosarium)

---

## 0. Keputusan yang Sudah Dikunci (Final)

Tabel berikut adalah **keputusan yang sudah disepakati dan tidak perlu dipertanyakan ulang** selama implementasi MVP. Perubahan hanya boleh terjadi lewat revisi eksplisit dokumen ini.

| # | Area | Keputusan Final | Alasan Ringkas |
|---|---|---|---|
| 1 | Scheduler | **APScheduler (AsyncIOScheduler) in-process** di FastAPI lifespan, cron harian | Windows-friendly, satu command `uvicorn` jalan semua; tidak perlu Task Scheduler |
| 2 | LLM extraction | **Groq — `llama-3.3-70b-versatile`**, JSON mode (`response_format={"type":"json_object"}`) | Free tier, mendukung structured output, familiar; fallback `llama-3.1-8b-instant` jika kena rate limit |
| 3 | Struktur backend | Monorepo `backend/` (FastAPI) + `frontend/` (Nuxt 3) — lihat §4 | Sesuai PRD: API & UI dipisah sebagai dua service |
| 4 | Taxonomy skill | **ESCO v1.2.x latest stable, English** (`skills_en.csv` + alt labels) + `alias_table.csv` custom | Battle-tested, gratis; alias table menambal kelemahan ESCO untuk tools/tech baru |
| 5 | Database | **Supabase Postgres + pgvector** (satu DB untuk relational + vector) | Tidak butuh vector DB terpisah; konsisten dengan stack portfolio |
| 6 | Sumber MVP | **RemoteOK** (official JSON API `https://remoteok.com/api`) + **WeWorkRemotely** (official RSS) | Zero risk legal/blokir; LinkedIn/Jobstreet **skip**; Glints **tunda Fase 2** |
| 7 | Embedding | **sentence-transformers lokal `all-MiniLM-L6-v2`** (384 dim), dua tipe embedding terpisah fungsi | Gratis, tanpa rate limit, cukup akurat untuk skala personal |
| 8 | Frontend | **Nuxt 3 + Nuxt UI** (sudah ter-scaffold di `frontend/`), consume Search API via HTTP | Presentable untuk portfolio |
| 9 | Dedup | **Flag, bukan delete** — kolom `is_duplicate_of` via normalized `title+company` match saat ingest | Aman, reversible; query insight selalu exclude duplikat |
| 10 | Extraction tracking | Kolom `extraction_status` (`pending/done/failed`) + `extraction_version` per posting | Reprocess selektif saat prompt berubah; hemat token Groq |
| 11 | Local-first | Semua berjalan di laptop Asep; satu-satunya service eksternal = Supabase cloud + Groq API | Sesuai NFR-5 |

---

## 1. Prinsip Implementasi

1. **MVP dulu.** Pipeline linear, tidak ada multi-agent/LangGraph, tidak ada auto-apply, tidak ada notifikasi.
2. **Raw storage = source of truth.** Deskripsi mentah selalu disimpan *sebelum* diproses → prompt extraction bisa diubah dan data di-reprocess tanpa fetch ulang.
3. **Idempotency di mana-mana.** Re-run pipeline tidak menghasilkan duplikat (`UNIQUE(source, source_id)`, skip yang `extraction_status='done'`).
4. **Adapter terisolasi.** Kegagalan/perubahan satu sumber tidak merambat ke sumber lain (NFR-6).
5. **Threshold tidak di-hardcode asal.** `SEARCH_THRESHOLD` dan `SKILL_MATCH_THRESHOLD` divalidasi empiris dengan data riil (§13) — nilai awal hanyalah titik mula eksperimen.
6. **Smallest safe change per tahap.** Tiap tahap roadmap menghasilkan artefak yang bisa dites independently; tidak lanjut ke tahap berikutnya sebelum kriteria done terpenuhi.
7. **Observability sederhana tapi nyata.** Log per-step (fetched/inserted/extracted/normalized/embedded/failed counts) cukup untuk personal tool — tidak perlu stack monitoring berat.

---

## 2. Arsitektur Final

### 2.1 Diagram sistem

```
                         ┌─────────────────────────────────────────────────────────┐
                         │  PROSES TUNGGAL: uvicorn (FastAPI)                      │
                         │                                                         │
   cron harian           │  ┌─────────────────────────────────────────────────┐    │
   (APScheduler,   ─────►│  │ PIPELINE ORCHESTRATOR (app/pipeline/orchestrator)│   │
   default 06:00)        │  │                                                   │   │
                         │  │  STEP 1 FETCH        STEP 2 DEDUP                 │   │
   manual trigger  ─────►│  │  ┌───────────────┐   ┌────────────────────────┐  │   │
   (run_pipeline.py)     │  │  │ adapter_       │   │ normalize title+company │  │   │
                         │  │  │  remoteok.py   │──►│ exact match vs existing │  │   │
                         │  │  │ adapter_wwr.py │   │ → set is_duplicate_of   │  │   │
                         │  │  └───────────────┘   └────────────────────────┘  │   │
                         │  │         │                        │               │   │
                         │  │         ▼                        ▼               │   │
                         │  │  STEP 3 EXTRACT         (duplikat dilewati       │   │
                         │  │  ┌───────────────────┐   dari step berikutnya)   │   │
                         │  │  │ Groq Llama 3.3 70B │                          │   │
                         │  │  │ JSON mode →        │                          │   │
                         │  │  │ {hard_skills,      │                          │   │
                         │  │  │  soft_skills,      │                          │   │
                         │  │  │  tools, level,     │                          │   │
                         │  │  │  min_years,        │                          │   │
                         │  │  │  employment_type}  │                          │   │
                         │  │  └───────────────────┘                          │   │
                         │  │         │                                        │   │
                         │  │         ▼                                        │   │
                         │  │  STEP 4 NORMALIZE                                │   │
                         │  │  raw skill → alias exact → embed → cosine        │   │
                         │  │  vs skills.embedding → skill_ids[]               │   │
                         │  │  gagal → tabel unmatched_skills                  │   │
                         │  │         │                                        │   │
                         │  │         ▼                                        │   │
                         │  │  STEP 5 EMBED JOBS                               │   │
                         │  │  embed(title + desc[:2000]) → jp.embedding       │   │
                         │  └─────────────────────────────────────────────────┘  │
                         └───────────────────────┬─────────────────────────────┘
                                                 ▼
                                 ┌────────────────────────────┐
                                 │  Supabase Postgres          │
                                 │  + pgvector                 │
                                 │  job_postings               │
                                 │  extracted_requirements     │
                                 │  skills (ESCO seeded)       │
                                 │  unmatched_skills           │
                                 └────────────┬───────────────┘
                                              │ SQL + vector ops
                        ┌─────────────────────┴─────────────────────┐
                        ▼                                           ▼
         ┌──────────────────────────┐                ┌──────────────────────────┐
         │  Search API (FastAPI)     │  HTTP          │  Frontend Nuxt 3          │
         │  GET /api/search          │ ◄────────────  │  /        (Search mode)   │
         │  GET /api/skills/top      │  JSON          │  /insight (Insight mode)  │
         │  GET /health              │                └──────────────────────────┘
         └──────────────────────────┘
```

### 2.2 Dua jenis embedding — fungsi dipisah tegas

| Embedding | Kapan dibuat | Disimpan di | Dipakai untuk |
|---|---|---|---|
| **Skill embedding** | Sekali saat `seed_skills.py` (dan saat ada skill custom baru) | `skills.embedding` | Normalisasi: raw skill dari LLM → `Skill.id` terdekat via cosine |
| **Job embedding** | Per posting, STEP 5 pipeline | `job_postings.embedding` | (a) Semantic search FR-5, (b) filter `role` semantik di endpoint insight |

### 2.3 Keputusan arsitektur turunan analisis

- **Scheduler toggle**: `SCHEDULER_ENABLED=true/false` di `.env`. Dev & testing API tidak memicu fetch tak disengaja.
- **Pipeline manual trigger**: `scripts/run_pipeline.py` dengan argumen `--step fetch|extract|normalize|embed|all` dan `--source remoteok|wwr|all` — tiap step bisa ditest terisolasi.
- **Dedup placement**: dijalankan **tepat setelah insert raw, sebelum extraction** — duplikat tidak membuang token LLM.
- **Retry Groq**: exponential backoff (1s → 2s → 4s), max 3x per posting; kegagalan final → `extraction_status='failed'`, otomatis di-retry run berikutnya.
- **Adapter failure isolation**: tiap adapter dibungkus try/except sendiri; error di-log dengan nama adapter; sumber lain tetap jalan.
- **NFR-3 enforcement di query level**: semua endpoint insight default `days=30` — loker expired tidak mengotori statistik tanpa perlu job cleanup di MVP.

---

## 3. Prasyarat & Setup Awal (Tahap 0 Detil)

Checklist ini harus selesai **sebelum** baris kode pertama ditulis.

### 3.1 Akun & kredensial

| Item | Cara dapat | Disimpan di |
|---|---|---|
| Supabase project | supabase.com → New Project (free tier) → catat `Project URL` + `service_role` key (bukan anon key — backend butuh full access tanpa RLS) | `backend/.env` |
| Groq API key | console.groq.com → API Keys → Create | `backend/.env` |
| ESCO dataset | Download ESCO v1.2.x classification, bahasa EN, format CSV → ambil `skills_en.csv` | `backend/data/esco/skills_en.csv` (gitignored) |

### 3.2 Environment lokal

- Python ≥ 3.11 (cek: `python --version`)
- Node.js ≥ 20 (sudah ada — frontend sudah ter-scaffold)
- Buat virtualenv: `python -m venv backend/.venv` → aktivasi → `pip install -r backend/requirements.txt`
- Copy `backend/.env.example` → `backend/.env`, isi nilai nyata

### 3.3 Inisialisasi database

1. Buka Supabase → SQL Editor → jalankan isi `scripts/init_db.sql` (DDL lengkap di §5).
2. Verifikasi: `SELECT * FROM pg_extension WHERE extname='vector';` harus return 1 row.
3. Jalankan `python scripts/seed_skills.py` → tabel `skills` terisi (~13.000+ skill ESCO dengan `preferredLabel`, `altLabels`, kategori) + embedding ter-precompute.
   - Kategorisasi hard/soft dari field `skillType` ESCO: `skill/competence` → hard, `knowledge` → hard, `transversal` → soft. Mapping persisnya ditentukan saat implementasi berdasar inspeksi kolom CSV aktual.
   - Seed `alias_table.csv` ikut di-load ke kolom `aliases` skill terkait.

**Kriteria done Tahap 0:** `uvicorn app.main:app` jalan, `GET /health` → `{"status":"ok","db":"connected"}`, tabel `skills` berisi data.

---

## 4. Struktur Folder Lengkap

```
jobHunter/
├── PRD_SRS_JobIntel.md          # (existing) dokumen produk
├── plan.md                      # (existing) dokumen ini
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory + lifespan (scheduler start/stop)
│   │   ├── config.py            # pydantic-settings: semua env var bertipe
│   │   ├── db.py                # Supabase client singleton + helper query reusable
│   │   ├── models.py            # Pydantic models: RawJob, ExtractionResult,
│   │   │                        #   SearchRequest/Response, SkillRankingResponse
│   │   ├── adapters/
│   │   │   ├── __init__.py      # registry: {"remoteok": RemoteOKAdapter, ...}
│   │   │   ├── base.py          # AbstractJobAdapter (ABC) + RawJob contract
│   │   │   ├── remoteok.py      # RemoteOK official JSON API
│   │   │   └── wwr.py           # WeWorkRemotely RSS via feedparser
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py  # run(step=..., source=...): koordinasi 5 step + logging
│   │   │   ├── extractor.py     # Groq call + prompt + backoff + status tracking
│   │   │   ├── normalizer.py    # raw skill → skill_ids (3-level resolution)
│   │   │   ├── embedder.py      # SentenceTransformer singleton + batch encode
│   │   │   └── dedup.py         # normalized title+company matching
│   │   ├── api/
│   │   │   ├── __init__.py      # include_router aggregasi
│   │   │   ├── search.py        # GET /api/search
│   │   │   └── skills.py        # GET /api/skills/top
│   │   └── scheduler.py         # APScheduler setup + job entrypoint
│   ├── scripts/
│   │   ├── init_db.sql          # DDL lengkap (§5)
│   │   ├── seed_skills.py       # load ESCO CSV + alias → insert + precompute embedding
│   │   ├── run_pipeline.py      # CLI manual trigger (arg --step, --source)
│   │   ├── validate_extraction.py   # sampling N posting → tampil side-by-side utk spot-check
│   │   └── validate_thresholds.py   # helper eksperimen threshold (§13)
│   ├── data/
│   │   ├── esco/                # skills_en.csv (gitignored)
│   │   └── alias_table.csv      # alias tech custom (tracked di git)
│   ├── tests/
│   │   ├── fixtures/
│   │   │   ├── remoteok_sample.json   # response asli disimpan utk offline test
│   │   │   └── wwr_sample.xml
│   │   ├── test_remoteok.py
│   │   ├── test_wwr.py
│   │   ├── test_dedup.py
│   │   └── test_normalizer.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md                # setup instructions reproduce-able
└── frontend/                    # (existing scaffold Nuxt 3)
    ├── app/
    │   ├── app.vue              # (existing) root: nav + <NuxtPage/>
    │   ├── pages/
    │   │   ├── index.vue        # Search mode
    │   │   └── insight.vue      # Insight mode
    │   └── components/
    │       ├── SearchBar.vue
    │       ├── JobCard.vue
    │       ├── SkillBarChart.vue
    │       └── FilterPanel.vue
    └── nuxt.config.ts           # + runtimeConfig.apiBaseUrl
```

---

## 5. Skema Database Lengkap

Isi penuh `scripts/init_db.sql`:

```sql
-- ============================================================
-- JobIntel MVP — init_db.sql
-- Jalankan sekali di Supabase SQL Editor.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------- ENUMs ----------
CREATE TYPE source_enum AS ENUM ('remoteok', 'wwr');
CREATE TYPE exp_level_enum AS ENUM ('junior', 'mid', 'senior', 'unknown');
CREATE TYPE emp_type_enum AS ENUM ('remote', 'onsite', 'hybrid', 'unknown');
CREATE TYPE skill_category_enum AS ENUM ('hard', 'soft', 'tool');
CREATE TYPE extraction_status_enum AS ENUM ('pending', 'done', 'failed');

-- ---------- job_postings: raw source of truth ----------
CREATE TABLE job_postings (
    id                 BIGSERIAL PRIMARY KEY,
    source             source_enum NOT NULL,
    source_id          TEXT        NOT NULL,     -- id unik dari platform asal
    title              TEXT        NOT NULL,
    company            TEXT,
    source_url         TEXT        NOT NULL,
    raw_description    TEXT,
    location           TEXT,
    posted_date        DATE,                       -- boleh NULL (WWR kadang tak ada)
    fetched_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    embedding          vector(384),                -- diisi STEP 5
    is_duplicate_of    BIGINT REFERENCES job_postings(id),
    extraction_status  extraction_status_enum NOT NULL DEFAULT 'pending',
    extraction_version INT NOT NULL DEFAULT 1,
    retry_count        INT NOT NULL DEFAULT 0,
    UNIQUE (source, source_id)                     -- idempotency fetch harian
);

-- ---------- extracted_requirements: hasil LLM, 1:1 ----------
CREATE TABLE extracted_requirements (
    job_posting_id       BIGINT PRIMARY KEY REFERENCES job_postings(id) ON DELETE CASCADE,
    hard_skills_raw      TEXT[],
    soft_skills_raw      TEXT[],
    tools_raw            TEXT[],
    experience_level     exp_level_enum,
    min_years_experience NUMERIC,
    employment_type      emp_type_enum,
    skill_ids            BIGINT[],                   -- hasil normalisasi (STEP 4)
    extracted_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- skills: kamus normalisasi (ESCO + custom) ----------
CREATE TABLE skills (
    id             BIGSERIAL PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    category       skill_category_enum NOT NULL,
    aliases        TEXT[] NOT NULL DEFAULT '{}',
    origin         TEXT  NOT NULL DEFAULT 'esco',   -- 'esco' | 'custom_alias'
    esco_uri       TEXT,                              -- traceability ke ESCO
    embedding      vector(384)                        -- precomputed saat seed
);

-- ---------- unmatched_skills: antrian review normalisasi ----------
CREATE TABLE unmatched_skills (
    id          BIGSERIAL PRIMARY KEY,
    raw_name    TEXT NOT NULL,
    first_seen  TIMESTAMPTZ NOT NULL DEFAULT now(),
    occurrences INT NOT NULL DEFAULT 1,
    resolved    BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (raw_name)
);

-- ---------- Indexes ----------
CREATE INDEX idx_postings_posted_date ON job_postings (posted_date DESC NULLS LAST);
CREATE INDEX idx_postings_status      ON job_postings (extraction_status)
    WHERE extraction_status <> 'done';
CREATE INDEX idx_postings_dedup       ON job_postings (is_duplicate_of)
    WHERE is_duplicate_of IS NULL;

-- pgvector HNSW index (cosine) — dibuat SETELAH ada data awal
-- (HNSW pada tabel kosong tetap valid, tapi build lebih efisien setelah data masuk)
CREATE INDEX idx_postings_embedding ON job_postings
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_skills_embedding ON skills
    USING hnsw (embedding vector_cosine_ops);
```

### Keputusan desain & alasannya

| Keputusan | Alasan |
|---|---|
| `UNIQUE(source, source_id)` | Idempotency: fetch harian overlap data tidak menimbulkan duplikat row |
| `ON DELETE CASCADE` pada `extracted_requirements` | Jika posting perlu dihapus manual, requirement ikut bersih |
| `skill_ids BIGINT[]` (array FK, bukan junction table) | MVP: query agregasi cukup `unnest()`; junction table dipertimbangkan ulang hanya jika query terbukti lambat |
| `skill_category_enum` termasuk `'tool'` | FR-3 meminta tools diekstrak → dashboard memisahkan hard skill vs tools vs soft skill |
| `posted_date` nullable + index `NULLS LAST` | WWR tidak selalu menyediakan tanggal posting — fallback ditampilkan pakai `fetched_at` |
| `retry_count` | Batas retry gagal extraction (max 3) tanpa loop tak berujung |
| `unmatched_skills.occurrences` | Skill yang sering gagal match di-review duluan (prioritas alias table) |
| HNSW index, bukan IVFFlat | HNSW tidak butuh training/list size tuning — lebih aman untuk skala data yang tumbuh bertahap |

---

## 6. Spesifikasi Komponen Backend

### 6.1 `config.py` — semua konfigurasi terpusat bertipe

```python
class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "all-MiniLM-L6-v2"
    scheduler_enabled: bool = False
    fetch_cron_hour: int = 6
    search_threshold: float = 0.25        # titik awal — divalidasi §13
    skill_match_threshold: float = 0.80   # titik awal — divalidasi §13
    extraction_version: int = 1           # naikkan saat prompt berubah
    http_timeout: int = 30
    groq_max_retries: int = 3
    model_config = SettingsConfigDict(env_file=".env")
```

### 6.2 `adapters/base.py` — kontrak adapter

```python
class RawJob(BaseModel):
    source: str            # 'remoteok' | 'wwr'
    source_id: str         # id dari platform asal (untuk UNIQUE constraint)
    title: str
    company: str | None
    source_url: str
    raw_description: str   # plain text (HTML sudah di-strip)
    location: str | None
    posted_date: date | None

class AbstractJobAdapter(ABC):
    source: str
    @abstractmethod
    def fetch(self) -> list[RawJob]: ...
```

### 6.3 `adapters/remoteok.py`

- **Endpoint:** `GET https://remoteok.com/api`
- **Header:** `User-Agent: JobIntel-Personal/0.1 (personal research tool)` — RemoteOK meminta UA yang jelas; request tanpa UA kadang ditolak.
- **Parsing penting:** elemen **pertama** response JSON adalah objek metadata/legal — **harus di-skip**.
- **Mapping field:**
  - `id` → `source_id`, `position` → `title`, `company` → `company`
  - `url` → `source_url`, `description` (HTML) → strip via BeautifulSoup → `raw_description`
  - `date` → parse ISO → `posted_date`
  - `location` → `location` (opsional)
- **Filter MVP:** hanya posting yang `raw_description` tidak kosong dan panjang ≥ 200 char (posting tanpa deskripsi tidak bisa diekstrak LLM).
- **Perilaku:** 1 request per run; timeout 30s; retry 3x backoff; return list `RawJob`.

### 6.4 `adapters/wwr.py`

- **Feed (dipakai dua-duanya):**
  - `https://weworkremotely.com/categories/remote-programming-jobs.rss`
  - `https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss`
- **Library:** `feedparser`.
- **Mapping field:**
  - `id`/`guid` → `source_id`, `title` (format `"Company: Position"` → split di `:` pertama) → `company` + `title`
  - `link` → `source_url`, `content:encoded` → strip HTML → `raw_description`
  - `published` → `posted_date` (fallback `None` → downstream pakai `fetched_at`)
  - `region` (jika ada) → `location`
- **Dedup di dalam adapter:** item yang sama bisa muncul di dua kategori feed → dedup by `guid` dalam satu run.

### 6.5 `pipeline/dedup.py`

- **Kapan:** setelah insert raw, sebelum extraction.
- **Algoritme (MVP, deterministik murah):**
  1. Normalisasi: `lower(title)`, `lower(company)`, hapus punctuation & whitespace berlebih → kunci kanonik.
  2. Untuk setiap posting baru dengan kunci `(source berbeda, title_norm, company_norm)` yang cocok dengan posting existing → set `is_duplicate_of = <id yang lebih lama>`.
  3. Posting ter-flag **dilewati** di STEP 3–5 dan **di-exclude** di semua query API.
- Similarity deskripsi (mahal) **tidak** diimplementasi di MVP — cukup dicatat sebagai peningkatan Fase 2.

### 6.6 `pipeline/extractor.py`

**Seleksi kandidat:** `extraction_status IN ('pending','failed') AND retry_count < 3 AND is_duplicate_of IS NULL AND extraction_version < :current_version`, batch 50 per run langkah.

**System prompt (versi 1 — baseline sebelum refinement Tahap 3):**

```
You are a precise information extraction system for IT job postings.
Extract ONLY what is explicitly written in the job description. Never infer
or add skills that are not mentioned. Return a single JSON object with
exactly these keys:

{
  "hard_skills": [string],   // technical competencies (e.g. "python", "sql",
                             // "machine learning", "statistical analysis")
  "soft_skills": [string],   // interpersonal/behavioral (e.g. "communication",
                             // "teamwork", "problem solving")
  "tools":        [string],  // specific named products/technologies
                             // (e.g. "kubernetes", "aws", "tableau", "jira")
  "experience_level": "junior" | "mid" | "senior" | "unknown",
  "min_years_experience": number | null,   // lowest explicit number mentioned
  "employment_type": "remote" | "onsite" | "hybrid" | "unknown"
}

Rules:
- All skill strings lowercase, trimmed, no duplicates.
- hard_skills = capabilities; tools = named products. "python" is a hard
  skill; "pandas" is a tool. "sql" is a hard skill; "postgresql" is a tool.
- If nothing found for a key, return [] (or null / "unknown").
- Ignore benefits, salary, company description, and legal boilerplate.
- Output ONLY the JSON object, no markdown, no commentary.
```

**User message:** `JOB TITLE: {title}\n\nJOB DESCRIPTION:\n{raw_description[:8000]}`

**Mode debug (dipakai `validate_extraction.py`):** prompt tambahan meminta `evidence` (kutipan kalimat asli) per skill — mempercepat spot-check NFR-4. Output evidence tidak disimpan ke DB di MVP.

**Error handling:** backoff 1s→2s→4s, max 3 retry per run; gagal → `status='failed'`, `retry_count += 1`. Sukses → upsert `extracted_requirements`, `status='done'`, `extraction_version=current`.

### 6.7 `pipeline/normalizer.py`

Resolusi tiap raw skill (dari ketiga array: hard, soft, tools):

```
1. ALIAS EXACT MATCH
   lower(raw) vs skills.aliases (unnested) & canonical_name
   → match? gunakan skill.id, selesai.

2. EMBEDDING MATCH
   vec = embedder.encode(raw)
   SELECT id, 1 - (embedding <=> vec) AS sim FROM skills
   ORDER BY embedding <=> vec LIMIT 1
   → sim >= SKILL_MATCH_THRESHOLD ? gunakan skill.id, selesai.

3. UNMATCHED
   upsert unmatched_skills(raw_name, occurrences += 1)
   → skill tersebut TIDAK masuk skill_ids (diharapkan di-review mingguan)
```

Kategori skill hasil mapping (`hard/soft/tool`) diambil dari record `skills` — bukan dari array asal (LLM kadang salah klasifikasi tipis; kamus ESCO lebih konsisten).

### 6.8 `pipeline/embedder.py`

- Singleton lazy: `_model = SentenceTransformer(settings.embedding_model)` saat pemakaian pertama (hindari load ~90MB model saat import).
- API internal: `encode(texts: list[str]) -> list[list[float]]` dengan batch size 32.
- Job embedding text: `f"{title}\n{raw_description[:2000]}"`.

### 6.9 `pipeline/orchestrator.py`

```
run(step="all", source="all") -> dict statistik
  fetch:      per adapter → insert on conflict do nothing → {fetched, inserted}
  dedup:      deretan posting baru → flag → {flagged}
  extract:    loop batch extractor → {extracted, extract_failed}
  normalize:  posting done & skill_ids NULL → {normalized, unmatched_new}
  embed:      posting done & embedding NULL → {embedded}
  log ringkasan per step (nama step, counts, durasi)
```

Partial step (`--step extract`) memungkinkan debug satu tahap tanpa ulang semua.

### 6.10 `scheduler.py`

- `AsyncIOScheduler` dibuat di FastAPI lifespan startup **hanya jika** `SCHEDULER_ENABLED`.
- Job: `CronTrigger(hour=settings.fetch_cron_hour)` → `orchestrator.run()` dibungkus guard `_running` flag (skip jika run sebelumnya belum selesai).
- Shutdown: `scheduler.shutdown(wait=False)` di lifespan teardown.

---

## 7. Kontrak API (Request/Response)

Base URL lokal: `http://localhost:8000`. CORS dibuka untuk `http://localhost:3000`.

### 7.1 `GET /health`

→ `{"status": "ok", "db": "connected"}`

### 7.2 `GET /api/search` — FR-5, FR-6

| Query param | Tipe | Default | Keterangan |
|---|---|---|---|
| `q` | string, required | — | keyword bebas ("backend python") |
| `days` | int | 30 | filter `posted_date >= now()-days` (kalau NULL pakai `fetched_at`) |
| `source` | `remoteok\|wwr` | semua | |
| `limit` | int | 20 | max 100 |

**Alur:** embed `q` → cosine vs `job_postings.embedding`, `similarity >= SEARCH_THRESHOLD`, exclude duplikat, order by similarity desc.

**Response 200:**
```json
{
  "query": "backend python",
  "count": 12,
  "results": [
    {
      "id": 1042,
      "title": "Senior Backend Engineer",
      "company": "Acme Inc",
      "source": "remoteok",
      "source_url": "https://remoteok.com/remote-jobs/...",
      "posted_date": "2026-08-04",
      "location": "Worldwide",
      "similarity": 0.61,
      "top_skills": ["python", "postgresql", "fastapi", "docker"]
    }
  ]
}
```
`top_skills` = max 5 `canonical_name` dari `skill_ids` join `skills`.

### 7.3 `GET /api/skills/top` — FR-7, FR-8, FR-9

| Query param | Tipe | Default | Keterangan |
|---|---|---|---|
| `days` | int | 30 | 7 / 30 / 90 (frontend menyediakan preset ini) |
| `role` | string | — | filter semantik via job embedding (embedding `:role`, distance `< 0.75` titik awal) |
| `category` | `hard\|soft\|tool` | semua | |
| `limit` | int | 20 | |

**SQL inti:**
```sql
WITH filtered AS (
  SELECT jp.id
  FROM job_postings jp
  WHERE COALESCE(jp.posted_date, jp.fetched_at::date)
          >= current_date - (:days || ' days')::interval
    AND jp.is_duplicate_of IS NULL
    AND (:role IS NULL OR jp.embedding <=> :role_vec < 0.75)
)
SELECT s.canonical_name, s.category, COUNT(*) AS freq
FROM filtered f
JOIN extracted_requirements er ON er.job_posting_id = f.id
CROSS JOIN LATERAL unnest(er.skill_ids) AS sid
JOIN skills s ON s.id = sid
WHERE (:category IS NULL OR s.category = :category)
GROUP BY s.id, s.canonical_name, s.category
ORDER BY freq DESC
LIMIT :limit;
```

**Response 200:**
```json
{
  "filters": {"days": 30, "role": "data scientist", "category": "hard"},
  "n_postings": 187,
  "skills": [
    {"name": "python", "category": "hard", "freq": 121},
    {"name": "machine learning", "category": "hard", "freq": 98}
  ]
}
```
`n_postings` **selalu disertakan** — konteks statistik wajib tampil di UI (mitigasi insight noisy).

### 7.4 Error format (semua endpoint)

```json
{"detail": "human-readable message"}
```
- `422` param invalid (FastAPI default), `500` error tak terduga (di-log).

---

## 8. Spesifikasi Frontend

### 8.1 Halaman `/` — Search mode (FR-5, FR-6)

- **SearchBar**: input keyword + tombol; filter samping: rentang waktu (7/30/90 hari), sumber (All/RemoteOK/WWR).
- **JobCard** per hasil: judul, perusahaan, lokasi, tanggal posting (relative: "3 hari lalu"), max 5 skill chips, similarity badge, tombol **"View on {source}"** → `source_url` `target="_blank" rel="noopener"`.
- State: loading skeleton, empty state ("Tidak ada hasil — coba perlebar rentang waktu"), error toast.

### 8.2 Halaman `/insight` — Insight mode (FR-7, FR-8, FR-9)

- **FilterPanel**: preset waktu (7/30/90), input role opsional, toggle kategori (Hard / Soft / Tools).
- **SkillBarChart**: horizontal bar chart (nama skill, frekuensi). Library: pilih yang paling ringan saat implementasi (mis. chart sederhana via div+CSS atau `chart.js` melalui Nuxt module — keputusan dibuat di Tahap 7 berdasar integritas Nuxt UI).
- Selalu tampilkan: `"Berdasarkan {n_postings} loker, {days} hari terakhir"`.
- Disclaimer permanen (mitigasi bias sumber): *"Insight merepresentasikan demand remote-global (RemoteOK, WeWorkRemotely), bukan pasar lokal Indonesia."*

### 8.3 Konfigurasi

```ts
// nuxt.config.ts
runtimeConfig: { public: { apiBaseUrl: 'http://localhost:8000' } }
```
Composables `useApi()` membungkus `$fetch` dengan base URL di atas.

---

## 9. Konfigurasi & Environment

**`backend/.env.example`:**
```ini
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
GROQ_API_KEY=<groq_key>
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=all-MiniLM-L6-v2
SCHEDULER_ENABLED=false
FETCH_CRON_HOUR=6
SEARCH_THRESHOLD=0.25
SKILL_MATCH_THRESHOLD=0.80
EXTRACTION_VERSION=1
```

> Nilai default threshold di atas adalah **titik mula eksperimen, bukan keputusan final** — finalnya ditentukan lewat protokol §13 dan dicatat di `.env` + komentar `config.py`.

---

## 10. Dependencies (Pinned)

**`backend/requirements.txt` (inti; pin versi persis saat install Tahap 0):**
```
fastapi
uvicorn[standard]
supabase
groq
sentence-transformers
feedparser
httpx
beautifulsoup4
lxml
apscheduler
pydantic
pydantic-settings
pandas          # hanya untuk seed_skills.py
pytest
```
> Versi dipin (`==`) setelah install berhasil di mesin Asep — menjaga reproduce-ability. Frontend dependencies mengikuti `frontend/package.json` existing (Nuxt 3 + Nuxt UI), tanpa tambahan berat.

---

## 11. Roadmap Eksekusi 9 Tahap (Task-by-Task)

> Aturan main: **satu tahap selesai + kriteria done terpenuhi → baru lanjut**. Setiap tahap ditutup dengan verifikasi nyata (command/test/screenshot), bukan asumsi.

### Tahap 0 — Setup & fondasi (0.5 hari)
- [ ] Selesaikan checklist §3.1–3.2 (akun, kredensial, venv, `.env`)
- [ ] Buat skeleton `backend/app/*` kosong + `config.py` + `db.py`
- [ ] Jalankan `init_db.sql` di Supabase; verifikasi extension `vector`
- [ ] Endpoint `GET /health` memverifikasi koneksi DB
- **Done:** `/health` → `{"status":"ok","db":"connected"}`

### Tahap 1 — Adapter RemoteOK + raw storage (1 hari)
- [ ] `adapters/base.py` + `adapters/remoteok.py`
- [ ] Simpan response JSON asli → `tests/fixtures/remoteok_sample.json`
- [ ] `tests/test_remoteok.py`: parsing fixture → RawJob valid (field mapping + skip metadata element)
- [ ] `run_pipeline.py --step fetch --source remoteok` → insert ke DB
- [ ] Re-run → **0 row baru** (idempotency `UNIQUE(source,source_id)` terbukti)
- **Done:** `SELECT count(*) FROM job_postings WHERE source='remoteok';` > 0; re-run tidak menambah.

### Tahap 2 — Adapter WWR + dedup (0.5 hari)
- [ ] `adapters/wwr.py` (2 feed) + fixture XML + `tests/test_wwr.py`
- [ ] `pipeline/dedup.py` + `tests/test_dedup.py` (kasus: judul sama company sama beda sumber ter-flag; beda company tidak)
- [ ] Fetch dua sumber via `--source all`
- **Done:** kedua sumber terisi; `SELECT count(*) FROM job_postings WHERE is_duplicate_of IS NOT NULL;` menunjukkan mekanisme berjalan (boleh 0, tapi unit test wajib hijau).

### Tahap 3 — Extraction Groq (1 hari)
- [ ] `pipeline/extractor.py` + prompt v1 (§6.6)
- [ ] Extract batch pertama (maks 50 posting)
- [ ] `scripts/validate_extraction.py --sample 10 --evidence` → tabel side-by-side (skill terekstrak vs kutipan bukti)
- [ ] Spot-check manual: target **≥ 80% skill valid**. Jika < 80% → refine prompt (clarify rules, tambah few-shot) → bump `EXTRACTION_VERSION=2` → re-extract
- **Done:** 10 sampel lulus spot-check; `extraction_status='done'` untuk batch; hasil review tercatat di catatan repo.

### Tahap 4 — Seed ESCO + normalization (1 hari)
- [ ] Taruh `data/esco/skills_en.csv`; tulis `data/alias_table.csv` (seed awal: `k8s→kubernetes`, `py→python`, `js→javascript`, `ts→typescript`, `postgres→postgresql`, `mongo→mongodb`, `gcp→google cloud platform`, dll.)
- [ ] `scripts/seed_skills.py`: load CSV → kategorisasi → insert `skills` → precompute embedding (batch)
- [ ] `pipeline/normalizer.py` (3-level resolution §6.7) + `tests/test_normalizer.py`
- [ ] Jalankan normalisasi atas hasil Tahap 3 → `skill_ids` terisi
- **Done:** `SELECT count(*) FROM extracted_requirements WHERE skill_ids IS NOT NULL;` > 0; `unmatched_skills` tercatat (tidak error, hanya antri review).

### Tahap 5 — Job embedding + Search API (1 hari)
- [ ] `pipeline/embedder.py` → isi `job_postings.embedding` untuk semua posting done
- **Checkpoint demo internal #1:** pipeline backend ujung-ke-ujung fungsional via CLI
- [ ] `api/search.py` sesuai kontrak §7.2
- [ ] Jalankan protokol validasi `SEARCH_THRESHOLD` (§13.1) → set nilai di `.env`
- **Done:** 3 query uji ("data scientist", "backend python", "machine learning engineer") menghasilkan list relevan (manual judge); `curl /api/search?q=...` return 200 dengan struktur kontrak.

### Tahap 6 — Skills aggregation API (0.5 hari)
- [ ] `api/skills.py` sesuai kontrak §7.3 (termasuk filter `role` semantik + `n_postings`)
- **Done:** `curl "/api/skills/top?days=30&category=hard"` return ranking; angka `n_postings` konsisten dengan isi DB.

### Tahap 7 — Frontend Nuxt (2 hari)
- [ ] `nuxt.config.ts`: runtime config `apiBaseUrl`
- [ ] Komponen: `SearchBar`, `JobCard`, `FilterPanel`, `SkillBarChart`
- [ ] Halaman `/` (search) + `/insight` (ranking + disclaimer + `n`)
- [ ] Handle loading/empty/error states
- [ ] `npm run build` PASS; uji manual kedua halaman di browser (screenshot arsip)
- **Done:** search end-to-end (ketik → list → klik keluar ke sumber asli) dan insight end-to-end (filter → chart berubah) bekerja terhadap API lokal.

### Tahap 8 — Scheduler + operasional (0.5 hari)
- [ ] `scheduler.py` + wiring di `main.py` lifespan
- [ ] Verifikasi: set `SCHEDULER_ENABLED=true`, `FETCH_CRON_HOUR` ke menit terdekat → log menunjukkan run terpicu; `false` → tidak ada job
- [ ] Finalisasi `backend/README.md` (setup reproduce-able: venv, env, init DB, seed, run, trigger manual)
- **Checkpoint demo internal #2 = MVP lengkap**
- **Done:** fetch otomatis terjadwal jalan; manual trigger jalan; log ringkasan per-step rapi.

**Total estimasi: ~8 hari kerja.**

---

## 12. Risiko & Mitigasi Operasional

| Risiko | Dampak | Mitigasi (tertanam di plan) |
|---|---|---|
| Volume loker kecil dari 2 sumber → insight noisy | Ranking skill tidak stabil | Tampilkan `n_postings` di semua statistik; akumulasi 2–4 minggu sebelum klaim; Adzuna/SerpAPI dicatat untuk Fase 2 |
| Bias remote-global | Salah arah prioritas belajar | Disclaimer permanen di `/insight`; tidak pernah diklaim mewakili pasar Indonesia |
| LLM hallucination | Skill ranking salah | Spot-check ≥80% di Tahap 3 (gate keras — tidak lanjut Tahap 4 sebelum lulus); mode evidence mempercepat review; prompt refinement iteratif |
| ESCO tak cover tech baru (Cursor, Claude Code, dll.) | Skill gagal dinormalisasi, hilang dari statistik | `unmatched_skills` + review mingguan + alias table / custom skill (`origin='custom_alias'`) |
| Groq rate limit (batch besar) | Pipeline gagal sebagian | Backoff 3x + `extraction_status/retry_count` resume; fallback model `llama-3.1-8b-instant` via env |
| Endpoint sumber berubah | Fetch gagal | Adapter terisolasi; unit test fixture offline; error adapter tidak merambat; log jelas per adapter |
| Biaya/token re-extraction saat prompt berubah | Pemrosesan ulang boros | `extraction_version` → hanya versi outdated yang diproses |
| Loker expired mengotori statistik | Insight basi | Filter `days` wajib (default 30) di semua query (NFR-3) — tanpa perlu cleanup job di MVP |
| Model embedding lokal berat di cold start | Delay request pertama | Lazy singleton di `embedder.py`; warm-up opsional saat lifespan startup |
| Duplikat lintas sumber tak tertangkap exact match | Double-count ringan | Diterima di MVP (dedup fuzzy = Fase 2); query sudah exclude yang ter-flag |

---

## 13. Protokol Validasi Empiris (Threshold)

> Dua angka ini **tidak boleh** difinalkan tanpa data riil — sesuai §11 PRD. Jalankan di Tahap 5, dokumentasikan hasilnya.

### 13.1 `SEARCH_THRESHOLD` (semantic search)

1. Siapkan 8 query uji representatif: `data scientist`, `backend python`, `machine learning engineer`, `devops`, `data analyst`, `full stack javascript`, `AI engineer`, `backend golang`.
2. Untuk tiap query: jalankan `/api/search?limit=10` tanpa threshold (ambil similarity mentah) → judge manual relevan/tidak untuk top-10.
3. Plot kasar precision vs cutoff (0.20 / 0.25 / 0.30 / 0.35).
4. Pilih cutoff dengan **precision top-10 ≥ 70%** sambil recall masih masuk akal.
5. Catat: tanggal, jumlah data saat uji, angka final → `.env` + komentar `config.py`.

### 13.2 `SKILL_MATCH_THRESHOLD` (normalisasi)

1. Ambil 50 raw skill terekstrak (campur hard/soft/tools).
2. Jalankan matching dengan kandidat threshold 0.75 / 0.80 / 0.85 / 0.90.
3. Untuk tiap nilai, hitung: % matched, % salah-mapping obvious (mis. "rust" bahasa vs lainnya), % unmatched.
4. Pilih nilai dengan false-mapping minimal sambil coverage wajar; sisanya masuk `unmatched_skills` untuk alias review.
5. Catat hasil di `.env` + komentar `config.py`.

---

## 14. Definition of Done — MVP

- [ ] Fetch harian RemoteOK + WWR berjalan otomatis via APScheduler (terbukti dari log)
- [ ] ≥ 2 minggu data terakumulasi tanpa pipeline failure beruntun (target ideal: ≥ 500 posting)
- [ ] Extraction lolos spot-check (≥ 80% valid pada 10 sampel, terdokumentasi)
- [ ] Kedua threshold divalidasi via §13 dan nilai final tercatat
- [ ] Search semantic relevan (judgement 3 query) + setiap hasil redirect benar ke sumber asli
- [ ] Dashboard menampilkan ranking hard/soft/tool + filter waktu + `n_postings` + disclaimer bias
- [ ] Duplikat ter-flag; query insight/search exclude duplikat
- [ ] Semua unit test hijau (`pytest` di `backend/tests/`)
- [ ] `npm run build` frontend PASS
- [ ] `backend/README.md` setup reproduce-able diverifikasi dari nol (fresh venv)

---

## 15. Di Luar Scope

Tegas **tidak** dikerjakan di MVP (dari PRD + keputusan arsitektur): multi-user/auth lintas orang, industri non-IT, real-time crawling 24/7, scraping platform ber-ToS ketat (LinkedIn/Jobstreet), multi-agent/LangGraph, auto-apply, notifikasi loker baru, gap analysis CV, tren time-series, fuzzy dedup berbasis similarity deskripsi, hosting cloud untuk app (hanya Supabase managed DB). Semua kandidat **Fase 2** — dibuka hanya setelah DoD §14 terpenuhi dan tool dipakai riil ≥ 2 minggu.

---

## Lampiran A: Inventaris File yang Akan Dibuat

**Backend (baru):** `app/main.py`, `app/config.py`, `app/db.py`, `app/models.py`, `app/adapters/{__init__,base,remoteok,wwr}.py`, `app/pipeline/{__init__,orchestrator,extractor,normalizer,embedder,dedup}.py`, `app/api/{__init__,search,skills}.py`, `app/scheduler.py`, `scripts/{init_db.sql,seed_skills.py,run_pipeline.py,validate_extraction.py,validate_thresholds.py}`, `data/alias_table.csv`, `data/esco/skills_en.csv` (unduhan, gitignored), `tests/{fixtures/*,test_remoteok.py,test_wwr.py,test_dedup.py,test_normalizer.py}`, `requirements.txt`, `.env`, `.env.example`, `README.md`.

**Frontend (tambahan di atas scaffold existing):** `app/pages/{index.vue,insight.vue}`, `app/components/{SearchBar,JobCard,SkillBarChart,FilterPanel}.vue`, update `app/app.vue` (nav) & `nuxt.config.ts` (runtime config).

## Lampiran B: Glosarium

| Istilah | Definisi dalam konteks JobIntel |
|---|---|
| Raw storage | Tabel `job_postings` — data mentah hasil fetch, tidak diubah setelah insert (kecuali embedding & status) |
| Extraction | LLM mengubah deskripsi free-text → JSON skill/level terstruktur |
| Normalisasi | Mapping skill mentah → entri kanonik di tabel `skills` (ESCO/custom) |
| Skill embedding | Vector per entri `skills`, untuk matching normalisasi |
| Job embedding | Vector per posting, untuk semantic search & filter role |
| Dedup flag | `is_duplicate_of` — penanda duplikat tanpa menghapus data |
| `n_postings` | Jumlah loker dalam filter aktif — konteks statistik wajib di UI |
| Threshold | Cutoff cosine similarity; divalidasi empiris, bukan ditebak |
| Spot-check | Review manual sampel hasil extraction (gate kualitas Tahap 3) |
