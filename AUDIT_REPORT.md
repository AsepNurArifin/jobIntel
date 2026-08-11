# LAPORAN AUDIT & TESTING — JobIntel MVP

> **Tanggal:** 11 Agustus 2026
> **Scope:** Full audit (kode + DB nyata + API nyata + pipeline nyata + frontend E2E)
> **Mode:** Laporan saja — **tidak ada kode yang diubah**
> **Environment:** Windows 11, Python 3.12, Node 24, uv 0.11.28, Supabase cloud, Groq

---

## 1. RINGKASAN EKSEKUTIF

| Area | Status | Catatan |
|---|---|---|
| Keamanan secrets | ✅ AMAN | `.env` & data ESCO ter-gitignore dengan benar, tidak ada secrets ter-commit |
| Unit tests | ✅ 15/15 PASS | pytest hijau, 15 modul smoke-import OK |
| Frontend build | ✅ PASS | `npm run build` sukses (3.3 MB, 815 kB gzip) |
| Pipeline fetch | ✅ JALAN | RemoteOK + WWR fetch OK, **idempotency terbukti** (re-run = 0 insert) |
| **Endpoint `/api/search`** | 🔴 **RUSAK TOTAL** | HTTP 500 untuk semua query yang menghasilkan data (bug B12) |
| Endpoint `/api/skills/top` | ⚠️ JALAN, ADA BUG | `n_postings` salah saat filter role (B5); kategori Tools selalu kosong (C3) |
| **Kualitas data skill** | 🔴 **BURUK** | Skill tech dipetakan salah (mis. `curl` → "curl hair"); ESCO label mentah sangat noisy |
| Kesesuaian plan.md | ⚠️ DEVIASI | Kontrak API §7.2 tidak diikuti; retry_count; dedup unbounded |

**Verdict:** Sistem **BELUM memenuhi Definition of Done MVP (plan §14)**. Fitur Search (FR-5/6 — fitur inti) tidak dapat digunakan end-to-end. Backend perlu perbaikan bug kritis + overhaul kualitas data skill sebelum layak dipakai.

---

## 2. HASIL TEST OTOMATIS

```
pytest: 15 passed in 2.97s
  test_dedup.py        4 PASS  (normalize_key: punctuation, whitespace, same-meaning, none)
  test_normalizer.py   5 PASS  (categorize hard/soft, JSON extraction robust)
  test_remoteok.py     4 PASS  (skip metadata, field mapping, filter desc pendek, empty payload)
  test_wwr.py          2 PASS  (parse+split title, fallback summary)
smoke import: 15/15 modul OK
npm run build: PASS
GET /health: {"status":"ok","db":"connected"} ✓
```

**Gap coverage (belum ada test):**
- `extractor.py` (komponen termahal — token Groq — justru zero test)
- `embedder.py`, `orchestrator.py`, `run_dedup`, `upsert_raw_jobs`
- Semua endpoint API (tidak ada test `/api/search`, `/api/skills/top`, `/health`)
- Frontend: tidak ada test sama sekali

---

## 3. BUG REGISTRY — TERKONFIRMASI

### 🔴 KRITIS (blokir fungsi inti)

#### B12 — `/api/search` HTTP 500 untuk SEMUA query dengan hasil
- **Lokasi:** `app/api/search.py:31` — fungsi `_top_skills()`
- **Akar masalah:** `names = client.table("skills").select("canonical_name")...` lalu `by_id = {s["id"]: s["canonical_name"] for s in names}` → **`KeyError: 'id'`** karena kolom `id` tidak di-select.
- **Reproduksi:** `curl "http://localhost:8000/api/search?q=python&days=30&limit=3"` → 500 (kosong, tanpa body error). Terverifikasi berulang: query tanpa hasil → 200 `[]`; query dengan hasil → 500.
- **Bukti langsung DB:** posting id=76 punya `skill_ids=[5198,13904,8724,7360]`; query skills tanpa `id` → KeyError.
- **Dampak E2E:** Halaman Search frontend tidak pernah menampilkan hasil apa pun. Uji Playwright: ketik "backend python" + klik Cari → UI stagnan di empty-state awal, error tertelan.
- **Fix:** `.select("id, canonical_name")`.

#### B3 — `retry_count` tidak pernah naik → extraction gagal di-retry SELAMANYA
- **Lokasi:** `app/pipeline/extractor.py:146-151`
- **Masalah:** saat exception, hanya `update({"extraction_status": "failed"})` — `retry_count += 1` tidak ada. Kandidat extraction difilter `.lt("retry_count", 3)` yang tak akan pernah berubah → posting beracun diproses ulang setiap run, **boros token Groq tanpa batas**. Melanggar plan §6.6.
- **Status DB saat audit:** 0 failed (bug laten — akan aktif begitu ada kegagalan).

#### B4 — `run_dedup` fetch TANPA limit (silent failure setelah >1000 rows)
- **Lokasi:** `app/pipeline/dedup.py:80-85` — `select` semua `job_postings` tanpa `.limit()`. PostgREST default cap ~1000 rows → setelah data tumbuh (target plan: ≥500 posting / akumulasi mingguan), duplikat baru **tidak akan terdeteksi tanpa error apa pun**.
- **Status saat audit:** 187 rows < 1000 → belum aktif, `dedup flagged=0` (wajar: tidak ada judul+company identik lintas sumber saat ini). Tetap laten.
- **Catatan:** juga memuat seluruh tabel tiap run = tidak skalabel.

#### KQ-1 — Kualitas skill mapping BURUK secara sistemik
- **Bukti nyata dari API/DB (90 hari):**
  - `curl` (CLI tool) → mapped ke ESCO **"curl hair"** (menata rambut!). Juga ada "chair a meeting", "advise on hair style", "design hair style" di kamus.
  - Top "hard skills": `solve problems` (7x), `make decisions`, `manage time`, `use microsoft office` — ini soft skill/generik, salah kategori.
  - Insight menampilkan skills non-IT: "international regulations for cargo handling", "accounting", "use painting techniques", "electricity", "create autocad drawings", "prevent health and safety problems".
- **Akar:** (1) Kamus = ESCO label mentah tanpa filter domain IT → 13.905 entries penuh noise non-tech; (2) `categorize_label` hanya keyword heuristik hard/soft; (3) embedding match pada korpus noisy menghasilkan salah-mapping seperti curl→"curl hair".
- **Dampak:** Dashboard Insight (FR-7/8/9) menyesatkan pengguna — ranking skill tidak merefleksikan demand tech riil.

### 🟡 MENENGAH

#### B5 — `n_postings` salah saat filter `role` aktif
- **Lokasi:** `app/api/skills.py:39-42` — `count_postings_in_days` tidak menerima filter role.
- **Bukti live:** `/api/skills/top?days=90&role=data+scientist` → `n_postings=174` (= total seluruh posting di rentang, bukan subset role). Kontrak plan §7.3: "angka `n_postings` konsisten dengan isi DB **dalam filter aktif**".

#### B6 — Kontrak API menyimpang dari plan §7.2
- `/api/search` mengembalikan **`list[SearchResult]`** langsung, bukan `{"query", "count", "results": [...]}`.
- Frontend (`useApi.ts`, menunggu `JobItem[]`) konsisten dengan implementasi, jadi self-consistent — tapi **dokumen induk plan.md tidak sinkron**. Salah satu harus di-update (plan atau kode).

#### B7 — Hardcoded threshold di RPC + unmatched_skills.occurrences mati
- `init_db.sql:175` — `top_skills` memakai `>= 0.25` hardcoded; config `role_filter_distance: 0.75` (config.py:24) tidak terpakai. Dua sumber kebenaran.
- `normalizer.py:41-49` — upsert `unmatched_skills` pakai `ignore_duplicates=True` → `occurrences` **tidak pernah increment** (kolom prioritas review jadi tidak berguna).

#### C3 — Kategori `tool` = 0 dari 13.905 skills
- DB: `{hard: 990, soft: 10}` (sample) — tidak ada jalur yang menghasilkan kategori `tool`.
- **Bukti live:** `/api/skills/top?category=tool` → `skills: []` selalu. UI punya toggle "Tools" yang **permanent kosong**.

#### B11 — Cold-start search timeout >120s
- Model `all-MiniLM-L6-v2` (~90MB) lazy-load pada query pertama → request pertama user timeout. Plan §12 menyebut "warm-up opsional saat lifespan startup" — **tidak diimplementasi**.
- Setelah warm: search latency ~1.4s (saat berfungsi), insight cepat.

### 🟢 RENDAH

#### B1 — Statistik `inserted` berpotensi tidak akurat + fallback lambat
- `dedup.py:41-69`: `upsert(ignore_duplicates=True)` mengembalikan `[]` untuk row di-skip; fallback per-row insert bisa double-hit network. Terobservasi: fetch 176 → inserted 11 + DB 176→187 konsisten, tapi pada run dengan banyak duplikat statistik bisa salah & lambat.

#### B2 — extractor mengabaikan param `client` & query `.or_()` mentah rawan
- `extractor.py:99-116`: `from app.db import get_client as get_db_client; db = get_db_client()` — parameter `client` fungsi tidak dipakai. String or-filter PostgREST mentah rawan salah-syntax pada perubahan versi. Saat ini terbukti berfungsi (100 posting done), jadi rendah-aktual, tapi rapuh.

#### B8 — WWR parser: risiko `IndexError`
- `wwr.py:71-75`: `entry.get("content", [{}])[0]` crash jika `content` ada tapi list kosong. Fallback summary ada, tapi urutan akses list tidak aman.

#### B9 — Statistik `updated` di seed_skills salah kaprah
- `seed_skills.py:106`: `updated += len(chunk) - len(data)` — padahal upsert mengembalikan semua rows; log menyesatkan (aksen pada observability).

#### B10 — Scheduler tanpa guard `_running` eksplisit
- Plan §6.10: job dibungkus guard flag. Implementasi mengandalkan `max_instances=1` APScheduler + try/except print. Deviasi minor, fungsional OK.

---

## 4. HASIL TEST PIPELINE NYATA

| Step | Hasil | Bukti |
|---|---|---|
| Fetch (all) | ✅ OK | remoteok fetched=100, wwr fetched=76, inserted=11 (DB 176→187, konsisten) |
| **Idempotency** | ✅ **TERBUKTI** | re-run fetch → `inserted=0` (UNIQUE(source, source_id) bekerja) |
| Dedup | ✅ Jalan | flagged=0 — benar (tidak ada duplikat title+company lintas sumber saat ini); B4 laten |
| Extract | ✅ 100 done | extraction pipeline sudah pernah jalan penuh; **B3 laten untuk kasus gagal** |
| Normalize | ⚠️ Jalan, buruk | `skill_ids` terisi, tapi mapping noisy (KQ-1); 5 row skill_ids NULL = extraction kosong (bukan bug) |
| Embed | ✅ OK | 100/100 posting done punya embedding; `.env` model konsisten `all-MiniLM-L6-v2` |

**State DB setelah audit:** 187 job_postings (100 done + 87 pending baru dari fetch audit), 187 → extracted_requirements 100, skills 13.905, unmatched_skills 136.

---

## 5. HASIL TEST API NYATA

| Test | Hasil |
|---|---|
| `GET /health` | ✅ 200 `{"status":"ok","db":"connected"}` |
| `GET /api/search?q=python` | 🔴 **500** (berapapun hasilnya) |
| `GET /api/search?q=` (kosong) | ✅ 422 (validasi jalan) |
| `GET /api/search?limit=101` | ✅ 422 (limit max 100 ter-enforce) |
| `GET /api/search` query tanpa hasil | ✅ 200 `[]` |
| `GET /api/skills/top?days=30` | ✅ 200, keys `{filters, n_postings, skills}`, n_postings=181 |
| `GET /api/skills/top?category=tool` | ⚠️ 200 tapi `skills: []` selalu (C3) |
| `GET /api/skills/top?role=data+scientist` | ⚠️ 200 tapi n_postings=174 (salah, B5) |

---

## 6. HASIL E2E FRONTEND (Playwright)

| Skenario | Hasil |
|---|---|
| Build production | ✅ PASS |
| Halaman `/` render (heading, search bar, filter, empty state awal) | ✅ OK |
| Search "backend python" → klik Cari | 🔴 **Tidak menampilkan hasil/error** (backend 500 → fetch gagal; pesan error frontend tertelan/UX misleading) |
| Navigasi `/insight` | ✅ Render lengkap: filter panel (rentang waktu, kategori, role), tombol Terapkan |
| Insight data load | ✅ Chart tampil dengan "Berdasarkan **181** loker, 30 hari terakhir" |
| Disclaimer bias sumber | ✅ Tampil permanen di bawah (sesuai plan §8.2) |
| Kualitas data Insight | 🔴 Ranking menampilkan skill non-IT/noise (KQ-1) |
| Toggle kategori "Tools" | ⚠️ Akan selalu kosong (C3) |

---

## 7. DEFINITION OF DONE MVP (plan §14) — VERDICT

| Kriteria DoD | Status |
|---|---|
| Fetch harian RemoteOK+WWR via scheduler | ⚠️ Pipeline manual OK; scheduler belum diverifikasi live (SCHEDULER_ENABLED=false) |
| ≥2 minggu data terakumulasi tanpa failure | ❓ Belum terbukti (data ada, B3 laten mengancam) |
| Extraction lolos spot-check ≥80% valid | ❓ Belum diverifikasi sistematis (10 sampel + evidence review sesuai Tahap 3) |
| Kedua threshold divalidasi §13 | ❌ **Belum** — nilai masih titik-mula (0.25/0.80) |
| Search semantic relevan + redirect benar | 🔴 **GAGAL** — endpoint 500 (B12) |
| Dashboard ranking + filter + n_postings + disclaimer | ⚠️ Parsial — jalan tapi B5, C3, KQ-1 |
| Duplikat ter-flag & di-exclude | ✅ Mekanisme jalan (flagged=0 saat ini benar), B4 laten |
| Semua unit test hijau | ✅ 15/15 |
| `npm run build` PASS | ✅ |
| README reproduce-able | ⚠️ Perlu verifikasi fresh-venv penuh |

---

## 8. REKOMENDASI PRIORITAS

### P0 — Perbaiki SEKARANG (blokir fungsi inti)
1. **B12** — `search.py:31`: tambahkan `"id"` ke select → `.select("id, canonical_name")`. Tanpa ini Search tidak berguna sama sekali.
2. **B3** — `extractor.py`: tambahkan `retry_count += 1` (RPC atau read-then-update) pada cabang exception.
3. **KQ-1** — Filter kamus skill ke domain IT (mis. pre-filter ESCO labels, atau whitelist+alias_table-driven), perbaiki kategorisasi (hard/soft/tool), lalu re-seed + re-normalize. Termasuk menghapus mapping salah seperti "curl hair".

### P1 — Sprint berikutnya
4. **B5** — `count_postings_in_days` menerima `role_vec` agar konsisten dengan list skill.
5. **B4** — dedup berjalan dengan batas window (mis. hanya posting 90 hari terakhir / paginated), bukan full-table.
6. **B11** — warm-up model di lifespan startup (`encode(["warmup"])` di startup) agar first-request tidak timeout.
7. **C3** — sediakan jalur kategori `tool` (dari `tools_raw` + alias table) atau sembunyikan toggle Tools di UI.
8. **B7** — hapus hardcode 0.25, pakai `role_filter_distance`; perbaiki increment `occurrences` di unmatched_skills.

### P2 — Higienitas
9. **B6** — satukan kontrak: update plan.md §7.2 ATAU ubah response jadi `{query,count,results}`.
10. **B8, B9, B10, B1, B2** — hardening parser WWR, statistik log, guard scheduler, statistik upsert, konsistensi param client.
11. Jalankan **protokol §13** (validasi SEARCH_THRESHOLD & SKILL_MATCH_THRESHOLD) dengan data riil, catat hasilnya ke `.env` + komentar config.
12. Lakukan **spot-check extraction 10 sampel** (Tahap 3) dengan `--evidence` sebelum klaim kualitas.
13. Tambahkan test: endpoint API (TestClient + mock RPC), extractor retry, dedup integration.
14. Frontend: jangan telan error — tampilkan status error yang jelas saat backend 500.

---

## 9. LAMPIRAN — Bukti Kunci

- **B12 reproduksi:** `search_jobs` RPC OK (row id=76, skill_ids ada) → endpoint 500; `_top_skills` select tanpa `id` → KeyError.
- **KQ-1 reproduksi:** DB skills ilike '%hair%' → `['advise on hair style','apply hair cutting techniques','chair a meeting','curl hair','design hair style']`; posting 76 "typescript/curl" mapping → `['use scripting programming','typescript','curl hair','github']`.
- **B5 reproduksi:** role filter ON → n_postings tetap 174 (= tanpa role).
- **C3 reproduksi:** kategori tool → 0 hasil; DB kategori hanya `{hard, soft}`.
- **Idempotency:** fetch run#1 inserted=11, run#2 inserted=0; DB count 176→187→187.
- **Artifacts pembersihan:** server uvicorn/node dimatikan, port 3000/8000 bersih, file log sementara dihapus. Batch 87 posting baru hasil fetch audit dibiarkan `pending` (siap untuk run extract berikutnya).

---
*Laporan dihasilkan oleh audit otomatis — tidak ada baris kode aplikasi yang diubah selama proses.*
