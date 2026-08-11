# LAPORAN PERBAIKAN — JobIntel (Eksekusi FIX_PLAN.md)

> **Tanggal:** 11 Agustus 2026
> **Referensi:** `AUDIT_REPORT.md` (temuan) → `FIX_PLAN.md` (rencana) → dokumen ini (hasil eksekusi)
> **Status:** SELESAI — semua 6 batch dieksekusi & diverifikasi

---

## 1. RINGKASAN HASIL

| Batch | Fokus | Status | Verifikasi |
|---|---|---|---|
| 1 | Quick Wins (P0) | ✅ Selesai | Search 200 OK, retry_count naik, warm-up OK |
| 2 | Data Correctness | ✅ Selesai | n_postings konsisten role, occurrences increment, dedup bounded, upsert akurat |
| 3 | Data Quality (P0) | ✅ Selesai | Kamus bersih 1.385 skill, kategori tool terisi, loop retry tertutup |
| 4 | Observability & Kontrak | ✅ Selesai | Kontrak §7.2, threshold config, WWR robust, guard scheduler |
| 5 | Testing Gaps | ✅ Selesai | 30/30 test PASS (15 test baru) |
| 6 | Validasi Empiris §13 | ✅ Selesai | Threshold final 0.25/0.80 terdokumentasi |
| — | Full Regression + E2E | ✅ Selesai | pytest 30/30, npm build PASS, search+insight end-to-end |

---

## 2. DETAIL PERUBAHAN KODE

### Backend

| File | Perubahan | Fix |
|---|---|---|
| `app/api/search.py` | Tambah kolom `id` di select skills → hilangkan KeyError 500; ubah respons jadi `{query, count, results}` | **FIX-1.1, FIX-4.1** |
| `app/pipeline/extractor.py` | Gunakan param `client` (hapus re-import); SELECT tambah `retry_count`; increment `retry_count` saat gagal | **FIX-1.4, FIX-1.2** |
| `app/main.py` | Warm-up model embedding di lifespan startup | **FIX-1.3** |
| `app/api/skills.py` | `n_postings` konsisten filter role via `search_jobs`; pakai `role_filter_distance` config | **FIX-2.1, FIX-4.2** |
| `app/pipeline/normalizer.py` | `_record_unmatched`: read-then-update → occurrences increment nyata | **FIX-2.2** |
| `app/pipeline/dedup.py` | `run_dedup` bounded window 90 hari; `upsert_raw_jobs` hitungan akurat via pre-check | **FIX-2.3, FIX-2.4** |
| `app/adapters/wwr.py` | Parser `content` aman (handling list kosong/str) | **FIX-4.3** |
| `app/scheduler.py` | Guard `_running` flag non-reentrant | **FIX-4.4** |
| `app/config.py` | Komentar nilai threshold final §13 | **FIX-6** |
| `scripts/init_db.sql` | `count_postings_in_days` siap role_vec (belum diaplikasikan — tak ada akses SQL; workaround di skills.py) | FIX-2.1 (partial) |
| `scripts/seed_skills.py` | Rewrite: whitelist tech + ESCO-relevan + kategori 3 kelas + delete stale | **FIX-3.1** |
| `scripts/backup_db.py` | **(BARU)** backup darurat tabel inti | Backup |

### Data (diubah via DB)

| Item | Sebelum | Sesudah |
|---|---|---|
| Jumlah skills | 13.905 (noisy, ESCO mentah) | **1.385** (whitelist IT + ESCO-relevan) |
| Kategori | hard 992 / soft 8 / **tool 0** | hard ~968 / soft ~393 / **tool ~24** |
| Noise | "curl hair", "advise on hair style", "accounting" | **hilang total** (verified 0) |
| `unmatched_skills` | 136 | 543 (raw non-IT terekstrak — sehat, review alias) |

### Frontend

| File | Perubahan | Fix |
|---|---|---|
| `app/composables/useApi.ts` | `search` return `SearchResponse {query,count,results}` | FIX-4.1 |
| `app/pages/index.vue` | Baca `data.results` (sinkron kontrak baru; versi user dipertahankan) | FIX-4.1 |

---

## 3. HASIL VERIFIKASI

### 3.1 Unit test — 30/30 PASS (naik dari 15)
Test baru: `test_extractor.py` (5), `test_dedup_integration.py` (5), `test_api.py` (6) — mencakup regresi B12, retry, kontrak API, dedup cross-source.

### 3.2 Pipeline nyata
- Fetch: idempotent (re-run inserted=0) ✅
- Extraction: 77 sukses / 10 gagal — **retry_count kini naik** (failed status: retry_count=2, stop di 3) → **loop B3 tertutup** ✅
- Normalize: 86 (dengan kamus baru) ✅
- Embed: 76 embedded, done=177 ✅

### 3.3 API nyata
- `/api/search?q=backend+python` → `{query,count:3,results:[...]}` dengan top_skills bersih (python, sql, django, docker, kubernetes) ✅
- `/api/search` validasi 422 (q kosong, limit>100) ✅
- `/api/skills/top?role=data+scientist` → n_postings=18 (subset dari 185, **FIX-2.1**) ✅
- `/api/skills/top?category=tool` → **data terisi** (aws, kubernetes, gcp...) — C3 teratasi ✅

### 3.4 E2E (Playwright)
- Search "DevOps" → **Ditemukan 30 loker relevan** (kartu lengkap: relevansi, tanggal, skill chips tech, link "Buka Loker") ✅
- Search "Backend Python" → Ditemukan 7 loker ✅
- Insight → ranking "#4 aws — Tool — 26 loker", filter panel lengkap ✅
- Backend status indikator "Backend Online" ✅

### 3.5 Quality Insight (data nyata 90 hari)
| Tools | Hard skills |
|---|---|
| aws 27x, kubernetes 25x, gcp 20x, azure 15x, react 9x | python 22x, terraform 19x, docker 18x, golang 16x, javascript 15x |

---

## 4. KEPUTUSAN & DEVIASI SELAMA EKSEKUSI

1. **FIX-2.1 (n_postings role):** RPC `count_postings_in_days` tidak bisa di-update (tidak ada akses psql/SQL editor). Workaround: gunakan `search_jobs` (predikat identik) untuk count saat role aktif. `init_db.sql` sudah diperbarui utk dokumentasi — perlu diaplikasikan manual bila akses SQL tersedia.
2. **FIX-3.1 kurasi:** Diimplementasikan sebagai `data/tech_whitelist.csv` (221 entri) + filter ESCO-relevan (1.189 label dari 13.896). Pendekatan whitelist-driven, bukan keyword-verbose.
3. **Frontend `index.vue`:** User telah mengubahnya (versi polish) setelah audit; saya **tidak menimpa** — hanya menyesuaikan 1 baris agar sinkron dengan kontrak baru `{results}`.
4. **10 posting extraction gagal (retry_count=2):** Berhenti diproses (limit 3). Ini perilaku benar pasca-FIX-1.2; bisa diproses ulang bila mau (set retry_count=0).

---

## 5. DEFINITION OF DONE MVP (plan §14) — STATUS AKHIR

| Kriteria | Status |
|---|---|
| Fetch harian RemoteOK+WWR | ✅ Pipeline manual jalan + scheduler siap (guard _running) |
| ≥2 minggu data (187 posting) | ✅ Terakumulasi; pipeline tanpa failure beruntun |
| Extraction spot-check ≥80% valid | ⚠️ Perlu review manual 10 sampel (alat `validate_extraction --evidence` siap) |
| Kedua threshold divalidasi §13 | ✅ 0.25 & 0.80 final + tercatat di config |
| Search semantic relevan + redirect benar | ✅ Terverifikasi E2E (DevOps 30, Backend Python 7) |
| Dashboard ranking + filter + n_postings + disclaimer | ✅ Terverifikasi E2E (aws #4 Tool 26 loker) |
| Duplikat ter-flag & di-exclude | ✅ Mekanisme jalan (flagged=0 wajar saat ini) + bounded |
| Semua unit test hijau | ✅ 30/30 |
| `npm run build` PASS | ✅ |
| README reproduce-able | ⚠️ Perlu update: seed pakai `tech_whitelist.csv` (sudah di-docstring) |

---

## 6. REKOMENDASI LANJUTAN (opsional)

1. **Spot-check extraction 10 sampel** dengan `--evidence` (gate Tahap 3 plan.md) — review manual skill valid ≥80%.
2. **Aplikasikan `init_db.sql`** versi baru (count_postings_in_days + role_vec) via Supabase SQL Editor bila ingin hilangkan workaround.
3. **Kurasi `unmatched_skills` (543)**: tambahkan alias yang sering muncul ke `tech_whitelist.csv` → re-seed.
4. **Update README** backend: dokumentasikan `tech_whitelist.csv` sebagai sumber kamus utama.
5. Commit perubahan (saat ini semua belum di-commit): backend 8 file, frontend 2 file, data baru.

---

*Eksekusi FIX_PLAN.md selesai. Ringkasan log & bukti di atas; backup DB tersimpan di `backend/data/backup_audit/`.*
