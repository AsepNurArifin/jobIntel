# FIX-PLAN — JobIntel Remediation Plan

> **Dokumen rencana perbaikan** berdasarkan temuan `AUDIT_REPORT.md` (11 Agustus 2026).
> **Tidak ada eksekusi kode dalam dokumen ini** — ini panduan implementation-ready.
> **Referensi bug:** B1–B12, C3, KQ-1 (lihat AUDIT_REPORT.md §3).

---

## 0. Aturan Main

- **Satu batch → verifikasi → lanjut.** Tiap batch punya tes yang membuktikan fix bekerja dan tidak merusak yang lain.
- **Full regression setelah tiap batch:** `uv run pytest` + `npm run build` harus tetap hijau.
- **Backup DB sebelum Batch 3/4** (re-seed & re-normalize mengubah data): Supabase → Database → Backups, atau `pg_dump` snapshot.
- **Urutan wajib:** Batch 1 → 2 → 3 → 4. Batch 5 paralel kapan pun.

---

## Batch 1 — QUICK WINS (P0) — ~15 menit, risiko rendah

> Tujuan: mengembalikan fungsi inti yang rusak total + menutup loop berbahaya. Tidak menyentuh data.

### FIX-1.1 — Search endpoint 500 (B12) — KRITIS
- **File:** `backend/app/api/search.py:26`
- **Perubahan:** tambahkan kolom `id` ke select:
  ```python
  .select("id, canonical_name")
  ```
- **Verifikasi:**
  - `curl "http://localhost:8000/api/search?q=python&days=30&limit=3"` → HTTP 200, `top_skills` terisi nama skill.
  - E2E: frontend `/` ketik "backend python" → hasil tampil dengan chips skill.
- **Regression risk:** tidak ada (menambah kolom seleksi).

### FIX-1.2 — retry_count tidak pernah naik (B3) — KRITIS
- **File:** `backend/app/pipeline/extractor.py:146-151` (cabang `except`)
- **Perubahan:** increment `retry_count` (baca nilai lama → update; atau RPC SQL `retry_count = retry_count + 1`):
  ```python
  db.table("job_postings").update({
      "extraction_status": "failed",
      "retry_count": (row_retry_count + 1),  # nilai dari SELECT kandidat
  }).eq("id", pid).execute()
  ```
  Sertakan `retry_count` di SELECT kandidat (baris 107) agar tersedia.
- **Verifikasi:**
  - Simulasi posting gagal (mock Groq raise) → `retry_count` 0→1; setelah 3 gagal, posting tidak lagi masuk kandidat.
  - `SELECT id, retry_count FROM job_postings WHERE extraction_status='failed'`.
- **Regression risk:** rendah; pastikan format tetap konsisten dengan `.lt("retry_count", 3)`.

### FIX-1.3 — Warm-up model embedding (B11)
- **File:** `backend/app/main.py` (lifespan startup)
- **Perubahan:** setelah settings load, panggil `encode(["warmup"], settings)` (atau `_get_model(settings)`) agar model ~90MB dimuat saat startup, bukan saat request pertama user.
- **Verifikasi:** request `/api/search` pertama setelah restart < 5 detik (bandingkan baseline >120s/timeout).
- **Regression risk:** startup lebih lambat ~3-8s — diterima; log "model warmed".

### FIX-1.4 — Konsistensi param client di extractor (B2)
- **File:** `backend/app/pipeline/extractor.py:94-116`
- **Perubahan:** gunakan parameter `client` yang sudah di-pass (hapus re-import `get_client()` di dalam fungsi) agar tidak ada dua sumber client.
- **Verifikasi:** pytest + satu run `--step extract` kecil tetap jalan.

---

## Batch 2 — DATA CORRECTNESS (P1) — ~1 jam

> Tujuan: statistik & counter benar; dedup tetap berfungsi saat data tumbuh.

### FIX-2.1 — n_postings konsisten dengan filter role (B5)
- **File:** `backend/scripts/init_db.sql` (fungsi `count_postings_in_days`) + `backend/app/api/skills.py:39-42`
- **Perubahan:** tambahkan parameter `role_vec vector` ke RPC; saat tidak NULL, hitung hanya posting yang cocok filter role (kondisi identik dengan `top_skills`). Teruskan `role_vec` dari endpoint.
- **Verifikasi:** `GET /api/skills/top?days=90&role=data+scientist` → `n_postings` ≤ total tanpa role (subset nyata).

### FIX-2.2 — occurrences unmatched_skills increment (B7b)
- **File:** `backend/app/pipeline/normalizer.py:41-49`
- **Perubahan:** ganti "insert-ignore" menjadi pola increment nyata (upsert dengan `occurrences = unmatched_skills.occurrences + 1` via RPC, atau read-then-update).
- **Verifikasi:** raw skill yang sama di-normalize 2x → `occurrences` bertambah.

### FIX-2.3 — Dedup bounded (B4)
- **File:** `backend/app/pipeline/dedup.py` (`run_dedup`)
- **Perubahan:** batasi scope fetch (mis. hanya posting `fetched_at >= now() - interval '90 days'` atau proses per-batch dengan pagination), sehingga tidak memuat seluruh tabel setiap run.
- **Verifikasi:** dengan dataset >1000 (uji sintetis/padding), duplikat lintas-sumber masih ter-flag; `run_dedup` tidak timeout.

### FIX-2.4 — Statistik upsert & seed (B1, B9)
- **Files:** `backend/app/pipeline/dedup.py` (`upsert_raw_jobs`), `backend/scripts/seed_skills.py:106`
- **Perubahan:** hitungan `inserted`/`updated` berdasarkan hasil nyata (bukan asumsi `len(data)`); log terpisah `inserted vs skipped-duplicates`.
- **Verifikasi:** fetch re-run → log `inserted=0 skipped=N` akurat.

---

## Batch 3 — DATA QUALITY (KQ-1, C3) — P0 — ~0.5–1 hari ⚠️ MENGUBAH DATA

> Tujuan: kamus skill bersih & domain-IT, kategori `tool` terisi, mapping tidak lagi menyesatkan.
> **Wajib backup DB dulu.** Batch ini menjalankan re-seed + re-normalize.

### FIX-3.1 — Filter kamus skill ke domain IT + kategorisasi 3 kelas
- **Files:** `backend/scripts/seed_skills.py`, `backend/data/alias_table.csv`, `backend/app/pipeline/normalizer.py` (`categorize_label`)
- **Perubahan:**
  - Buat **whitelist/filter IT** (mis. gunakan `backend/data/esco/esco_priors.json` yang sudah ada + kurasi 13.896 label — buang entri non-tech seperti "curl hair", "advise on hair style", "accounting", "electricity", dst.).
  - Perbaiki kategorisasi ke **hard / soft / tool** (bukan hanya hard/soft): mapping tools dari alias table & daftar produk-tech ("kubernetes", "aws", "postgresql", "tableau", "jira"...) → `category='tool'`; behavioral → `soft`; sisanya → `hard`.
  - Tambahkan alias baru yang terbukti dibutuhkan dari `unmatched_skills` (136 entries — sumber kurasi utama).
- **Verifikasi:** `SELECT category, count(*) FROM skills GROUP BY category` → tool > 0; tidak ada label "%hair%"/"accounting" sebagai skill tech.

### FIX-3.2 — Re-seed + re-normalize
- **Langkah:**
  1. Jalankan ulang `python -m scripts.seed_skills` (timpa kamus lama, embedding baru).
  2. Reset `extracted_requirements.skill_ids = NULL` (semua atau yang affected) agar dipetakan ulang.
  3. Jalankan `run_pipeline --step normalize`.
- **Verifikasi:**
  - Top skills 90 hari menampilkan skill tech nyata (python, sql, javascript, aws...), bukan "curl hair"/"use microsoft office".
  - `curl` → `tool` yang benar (bukan "curl hair").
  - `/api/skills/top?category=tool` → **menghasilkan data** (C3 teratasi).

---

## Batch 4 — OBSERVABILITY & KONTRAK (P2) — ~0.5 hari

### FIX-4.1 — Sinkronisasi kontrak API (B6)
- **Keputusan (pilih satu):** (a) ubah `/api/search` mengikuti plan.md §7.2 `{query, count, results:[...]}` dan update `frontend/app/composables/useApi.ts` + `types/index.ts`; **ATAU** (b) update `plan.md` §7.2 mendokumentasikan bentuk list saat ini. Direkomendasikan **(a)** untuk konsistensi dok induk.
- **Verifikasi:** respons sesuai satu kontrak tunggal; frontend tetap jalan.

### FIX-4.2 — Threshold config terhubung (B7a)
- **Files:** `init_db.sql` (`top_skills`), `backend/app/api/skills.py`
- **Perubahan:** kirim `role_filter_distance` dari config ke RPC; hapus hardcode `0.25`.
- **Verifikasi:** mengubah `ROLE_FILTER_DISTANCE` di `.env` mengubah hasil filter role.

### FIX-4.3 — Parser WWR robust (B8)
- **File:** `backend/app/adapters/wwr.py:71-75`
- **Perubahan:** akses aman daftar `content` (cek truthy sebelum `[0]`), fallback ke `summary` bila kosong.
- **Verifikasi:** `pytest tests/test_wwr.py` + feed nyata fetch tanpa exception.

### FIX-4.4 — Guard scheduler `_running` (B10)
- **File:** `backend/app/scheduler.py`
- **Perubahan:** bungkus `_scheduled_pipeline` dengan flag non-reentrant sesuai plan §6.10 (skip + log bila run sebelumnya belum selesai).
- **Verifikasi:** paksa dua trigger overlap → run kedua di-skip dengan log jelas.

---

## Batch 5 — TESTING GAPS (P2) — paralel, ~0.5–1 hari

- **T-API:** TestClient + mock RPC untuk `/health`, `/api/search` (200/422/500 paths), `/api/skills/top` (filter days/role/category, n_postings konsisten).
- **T-Extractor:** retry logic (retry_count naik, status failed→tidak diproses setelah 3x), batching limit, `_extract_json` edge cases.
- **T-Dedup integration:** `run_dedup` menandai duplikat lintas-sumber (judul+company sama, beda source) & tidak menandai yang beda.
- **T-Frontend:** (opsional) Vitest komponen `JobCard`/`SkillBarChart` + satu happy-path Playwright.
- **Kriteria:** coverage komponen pipeline inti > 60%; semua test hijau.

---

## Batch 6 — VALIDASI EMPIRIS (plan §13) — ~0.5 hari — SEBELUM klaim DoD

- **SEARCH_THRESHOLD:** jalankan `validate_thresholds.py --queries "data scientist,backend python,ml engineer,devops,data analyst,full stack javascript,AI engineer,backend golang"` → pilih cutoff dengan precision top-10 ≥70% → set di `.env` + komentar di `config.py`.
- **SKILL_MATCH_THRESHOLD:** `--skill-sample 50` → pilih false-mapping minimal → set di `.env`.
- **SPOT-CHECK EXTRACTION (Tahap 3 gate):** `validate_extraction.py --sample 10 --evidence` → review manual ≥80% valid; bila < 80% → refine prompt → bump `EXTRACTION_VERSION=2` → re-extract.

---

## Dependensi & Risiko

| Item | Keterangan |
|---|---|
| FIX-3 tergantung backup DB | Jangan jalankan re-seed tanpa snapshot |
| FIX-3 mengubah mapping skill yang sudah dipakai UI | Jalankan saat downtime; verifikasi ulang dashboard setelahnya |
| FIX-1.1 harus mendahului E2E frontend | Search E2E tidak dapat diverifikasi sebelum B12 diperbaiki |
| Batch 6 butuh data riil memadai | Jalankan setelah Batch 3 agar kualitas skill bersih |

## Kriteria Selesai (DoD setelah perbaikan)

- [ ] `/api/search` 200 dengan `top_skills` benar untuk semua query uji §13
- [ ] `retry_count` ter-increment; tidak ada retry tak berujung
- [ ] `n_postings` konsisten saat filter role
- [ ] Kamus skill domain-IT bersih; kategori `tool` > 0; dashboard Insight menampilkan skill tech nyata
- [ ] Dedup tetap berfungsi >1000 rows
- [ ] Cold-start search < 5s (warm-up aktif)
- [ ] Kedua threshold final terdokumentasi di `.env` + `config.py`
- [ ] Extraction spot-check ≥80% valid terdokumentasi
- [ ] Full regression hijau: `uv run pytest` + `npm run build`
- [ ] Kontrak API tunggal (kode & plan.md sinkron)

---

*Rencana ini siap dieksekusi bertahap. Estimasi total: ~2–3 hari kerja.*
