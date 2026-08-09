# PRD / SRS — JobIntel
## Personal IT Job Aggregator & Market Intelligence System

**Versi:** 0.1 (Draft MVP)
**Pemilik:** Asep Nur Arifin
**Tanggal:** 9 Agustus 2026
**Status:** Draft — menunggu validasi scope sebelum masuk fase desain teknis detail

---

## 1. Latar Belakang & Problem Statement

Loker IT tersebar di banyak platform (LinkedIn, Jobstreet, Glints, Kalibrr, dll), masing-masing dengan format requirement yang tidak terstruktur dan berbeda-beda cara penulisannya. Untuk seseorang yang ingin fokus meningkatkan skill secara efektif dan mencari kerja secara strategis, membaca loker satu per satu secara manual:

- Tidak scalable — volume loker terlalu banyak untuk dibaca manual.
- Tidak memberi gambaran pola/tren — sulit menjawab pertanyaan seperti "skill apa yang paling sering diminta untuk role Data Scientist di Indonesia saat ini?"
- Menghambat pengambilan keputusan belajar — tanpa data agregat, prioritas belajar jadi tebak-tebakan, bukan berdasarkan evidence.

**Tujuan utama sistem:** menjadi *personal job hunting tool* yang sekaligus berfungsi sebagai *market research tool* — mengumpulkan loker IT dari berbagai sumber, mengekstrak requirement-nya secara terstruktur, dan menyajikan dua hal: (1) hasil pencarian loker yang bisa langsung diklik menuju sumber asli, dan (2) dashboard prioritas skill (hard skill & soft skill) berdasarkan agregasi data loker yang relevan.

---

## 2. Goals & Non-Goals

### Goals (MVP)
- G1: Mengumpulkan data loker IT dari sumber yang **legal/feasible diakses** secara otomatis atau semi-otomatis.
- G2: Mengekstrak requirement dari deskripsi loker (unstructured text) menjadi data terstruktur (hard skill, soft skill, tools, level, pengalaman).
- G3: Menyediakan fitur pencarian keyword (mis. "data scientist") yang menampilkan daftar loker relevan, masing-masing dengan link langsung ke sumber asli.
- G4: Menyediakan dashboard agregat yang menampilkan prioritas skill (hard & soft) berdasarkan frekuensi kemunculan di loker-loker yang relevan dengan pencarian/role tertentu.
- G5: Sistem berjalan sebagai personal tool — single-user, dijalankan oleh dan untuk Asep sendiri.

### Non-Goals (eksplisit di luar scope MVP)
- NG1: Bukan produk multi-tenant/multi-user dengan sistem login publik.
- NG2: Bukan cakupan semua industri — fokus IT/tech saja (Data, AI/ML, Backend, dst).
- NG3: Bukan real-time crawler yang jalan 24/7 tanpa batas — frequency fetch dibatasi secara sadar untuk menghindari risiko pemblokiran.
- NG4: Tidak melakukan scraping terhadap platform yang secara eksplisit melarang di ToS tanpa jalur resmi (API/partner access) — ini keputusan sadar untuk membatasi risiko legal, bukan keterbatasan teknis.

---

## 3. User & Use Case

**User:** Asep sendiri (single-user).

**Primary use cases:**
1. *"Saya mau tau requirement Data Scientist yang sedang dicari sekarang"* → search keyword → dapat list loker relevan + link sumber.
2. *"Saya mau tau skill apa yang paling sering diminta untuk role Backend Engineer dalam 3 bulan terakhir"* → buka dashboard, filter role → lihat ranking hard skill & soft skill.
3. *"Saya mau langsung apply ke loker yang match"* → klik hasil pencarian → redirect ke halaman asli loker di platform sumber.

---

## 4. Functional Requirements

| ID | Requirement | Prioritas |
|----|-------------|-----------|
| FR-1 | Sistem dapat mengambil (fetch) data loker dari minimal 2-3 sumber yang feasible diakses (lihat §7 Data Source Strategy) | Must |
| FR-2 | Sistem menyimpan raw data loker: judul, perusahaan, deskripsi lengkap, URL sumber, tanggal posting, tanggal fetch | Must |
| FR-3 | Sistem mengekstrak dari deskripsi loker: hard skill, soft skill, tools/teknologi, level pengalaman (junior/mid/senior), tipe kerja (remote/onsite/hybrid) menggunakan LLM-based structured extraction | Must |
| FR-4 | Sistem melakukan normalisasi skill (mis. "Python", "python programming", "Py" → entitas yang sama) | Must |
| FR-5 | User dapat search berdasarkan keyword bebas (mis. "data scientist", "backend python") menggunakan **semantic search (embedding-based via pgvector)** dan mendapat list loker relevan | Must |
| FR-6 | Setiap hasil pencarian menampilkan ringkasan (judul, perusahaan, skill utama) dan dapat diklik untuk redirect ke URL sumber asli | Must |
| FR-7 | Dashboard menampilkan ranking hard skill berdasarkan frekuensi kemunculan, terfilter berdasarkan keyword/role/kategori | Must |
| FR-8 | Dashboard menampilkan ranking soft skill secara terpisah dari hard skill | Must |
| FR-9 | User dapat memfilter hasil/dashboard berdasarkan rentang waktu (mis. loker 30 hari terakhir) | Should |
| FR-10 | Sistem menandai loker yang duplikat/repost dari sumber berbeda | Should |
| FR-11 | User dapat melihat tren skill dari waktu ke waktu (skill apa yang naik/turun permintaannya) | Could (Fase 2) |
| FR-12 | Sistem dapat melakukan gap analysis: bandingkan skill yang dimiliki user vs skill yang paling diminta pasar | Could (Fase 2) |

---

## 5. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | **Legal compliance**: sistem hanya mengambil data dari sumber yang ToS-nya memungkinkan (API resmi/RSS) atau yang risikonya sudah divalidasi dan diterima secara sadar sebagai personal use. Tidak menargetkan platform dengan proteksi anti-bot agresif tanpa jalur resmi. |
| NFR-2 | **Fetch frequency**: terjadwal harian (1x/hari, via cron sederhana), bukan continuous polling. Loker tidak berubah dalam hitungan jam, jadi fetch harian sudah cukup fresh tanpa membebani sumber data secara tidak perlu. |
| NFR-3 | **Data freshness**: loker yang ditampilkan idealnya tidak lebih dari 30 hari sejak posting (loker lama biasanya sudah closed). |
| NFR-4 | **Extraction accuracy**: hasil ekstraksi skill harus divalidasi secara sampling manual di awal (bukan dipercaya 100% dari LLM tanpa spot-check). |
| NFR-5 | **Local-first**: untuk MVP, sistem berjalan lokal di laptop/lingkungan Asep, tidak wajib hosting cloud (mengurangi risiko IP cloud provider ter-flag sebagai bot, dan menghindari cost hosting yang tidak perlu untuk single-user tool). |
| NFR-6 | **Maintainability**: karena struktur HTML/API sumber eksternal bisa berubah sewaktu-waktu, tiap adapter sumber data harus terisolasi (perubahan di satu sumber tidak merusak sumber lain). |

---

## 6. System Architecture (High-Level)

Mengikuti prinsip *smallest safe change* dan *avoid premature abstraction* — arsitektur MVP dibuat linear dulu, bukan langsung multi-agent kompleks.

```
[Source Adapters: RemoteOK API, WWR RSS] → [Raw Storage (Supabase Postgres)] 
→ [LLM Extraction (Groq)] → [Normalization (ESCO + custom alias table)] 
→ [Structured DB + pgvector embeddings (Supabase)] 
→ [Search API (FastAPI, standalone, semantic search via pgvector)] 
→ [Dashboard/UI (Nuxt 3, terpisah, consume API)]
```

**Keputusan:** Search API dan Dashboard/UI dipisah sebagai dua service berbeda (bukan monolith). Search API dibangun reusable — bisa dipakai ulang nanti sebagai demo project di portfolio, terlepas dari Nuxt frontend-nya. Supabase (Postgres + pgvector) dipakai sebagai single database untuk data relasional maupun vector embedding, menghindari kebutuhan vector DB terpisah.

### Alur logika:

1. **Source Adapter Layer** — modul terpisah per sumber data (mis. `adapter_glints.py`, `adapter_jobstreet.py`). Masing-masing adapter bertanggung jawab fetch raw listing dari satu sumber. Terisolasi supaya kalau satu sumber berubah struktur, adapter lain tidak terdampak.

2. **Raw Storage** — simpan hasil fetch mentah (judul, deskripsi, URL, source, timestamp) sebelum diproses. Ini penting sebagai *source of truth* — kalau logic ekstraksi nanti diperbaiki, tidak perlu fetch ulang, cukup reprocess dari raw storage.

3. **LLM Extraction Layer** — satu prompt terstruktur yang mengubah deskripsi loker (free text) menjadi JSON: `{hard_skills: [], soft_skills: [], tools: [], level: str, employment_type: str}`. Menggunakan structured output (format JSON eksplisit di system prompt).

4. **Normalization Layer** — mapping variasi penulisan skill ke entitas kanonik. Untuk MVP: dictionary/lookup table manual yang di-maintain seiring waktu (bukan langsung machine learning clustering — terlalu premature untuk skala data personal).

5. **Structured DB** — menyimpan data ter-extract dan ter-normalisasi, siap untuk query (search by keyword) dan aggregation (hitung frekuensi skill per role).

6. **Search API** — endpoint sederhana: input keyword → query ke DB (title/description/skill match) → return list loker terurut relevansi, masing-masing dengan URL asli.

7. **Dashboard/Query UI** — dua mode:
   - *Search mode*: keyword → list loker (FR-5, FR-6).
   - *Insight mode*: filter role/kategori → ranking hard skill & soft skill (FR-7, FR-8).

### Catatan arsitektur:
Ini **belum** perlu jadi multi-agent system (LangGraph dkk) di MVP — itu over-engineering untuk kebutuhan personal single-user. Pipeline linear/sequential sudah cukup. Pertimbangan agentic architecture baru relevan kalau nanti scope berkembang ke arah otomatisasi lebih kompleks (mis. auto-apply, personalized recommendation dengan reasoning multi-step).

---

## 7. Data Source Strategy

Ini bagian paling kritis dan harus divalidasi sebelum development dimulai. Klasifikasi sumber:

| Kategori | Contoh | Status (divalidasi 9 Agt 2026) | Strategi |
|----------|--------|-------------------------------|----------|
| **Official API/RSS, aman digunakan** | RemoteOK | Official public JSON API (`remoteok.com/api`), tanpa auth/proxy/captcha | ✅ Sumber utama MVP |
| **Official API/RSS, aman digunakan** | WeWorkRemotely | Official public RSS feeds, 11 kategori termasuk programming & devops | ✅ Sumber kedua MVP |
| **Tidak ada API resmi (gray area)** | Glints | Tidak mempublikasikan API developer publik; hanya ada layanan pihak ketiga berbayar yang scraping tanpa izin resmi | ⚠️ Tunda ke Fase 2, validasi ulang sebelum dipakai |
| **Proteksi ketat, tidak ada API resmi** | LinkedIn, Jobstreet | Anti-bot agresif, ToS eksplisit melarang | ❌ Skip dari MVP |
| **Agregator/API resmi (coverage terbatas untuk Indonesia)** | Adzuna, Google for Jobs (SerpAPI) | Legal, tapi coverage loker IT Indonesia perlu divalidasi lebih lanjut | 🔍 Kandidat ekspansi Fase 2 |

**Keputusan MVP:** mulai dari **RemoteOK + WeWorkRemotely** — dua-duanya official API/RSS, zero risk pemblokiran, dan data sudah relatif terstruktur (title, company, tags/skill, apply URL).

**Trade-off yang diterima secara sadar:** kedua sumber ini fokus pada remote job global, bukan loker lokal Indonesia. Untuk role target (AI/ML, Data, Backend) ini cukup relevan karena role tersebut lazim remote — tapi insight skill yang dihasilkan lebih merepresentasikan standar global, bukan spesifik kebiasaan HR Indonesia. Ekspansi ke sumber lokal (Glints, dst) didorong ke Fase 2 setelah pipeline inti tervalidasi.

---

## 8. Data Model (Entitas Utama)

```
JobPosting
├── id
├── title
├── company
├── source (enum: glints, kalibrr, ...)
├── source_url
├── raw_description
├── posted_date
├── fetched_date
├── location
├── employment_type

ExtractedRequirement (1:1 dengan JobPosting)
├── job_posting_id (FK)
├── hard_skills [] 
├── soft_skills []
├── tools []
├── experience_level (junior/mid/senior)
├── min_years_experience

Skill (normalized dictionary, seeded dari skills.csv ESCO)
├── id
├── canonical_name (dari preferredLabel ESCO)
├── category (hard/soft)
├── aliases []  (dari altLabels ESCO + custom alias table untuk tools/tech spesifik)
├── source (enum: esco, custom_alias)
├── embedding (vector, precomputed sekali saat setup — dipakai untuk proses matching normalisasi, bukan untuk search)

JobPosting (tambahan field)
├── embedding (vector, pgvector) — 1 vector per posting, dipakai khusus untuk semantic search (FR-5)

ExtractedRequirement
├── job_posting_id (FK)
├── skill_ids [] (FK ke Skill — hasil matching skill mentah dari LLM extraction ke Skill.id terdekat via cosine similarity terhadap Skill.embedding)
```

---

## 9. Tech Stack Rekomendasi

Menyesuaikan stack yang sudah familiar (konsisten dengan Mind-AI dan portfolio website Nuxt/Supabase). Search API dan Dashboard/Frontend dipisah sebagai dua service berbeda.

| Layer | Pilihan | Alasan | Trade-off |
|---|---|---|---|
| Search API | FastAPI | Konsisten dengan Mind-AI, reusable untuk portfolio | — |
| Frontend/Dashboard | **Nuxt 3** | Konsisten dengan portfolio website, lebih polished dibanding Streamlit kalau nanti dipamerkan sebagai portfolio piece | Effort build UI lebih besar dibanding Streamlit — trade waktu demi hasil lebih presentable |
| Database | **Supabase (Postgres + pgvector)** | Satu database untuk relational data & vector embedding sekaligus (tidak butuh vector DB terpisah seperti Milvus), konsisten dengan stack portfolio | Perlu koneksi internet ke Supabase cloud (bukan fully local seperti SQLite) — acceptable untuk personal tool |
| Extraction | Groq (LLM structured output) | Sudah familiar, cepat, murah | Perlu spot-check akurasi manual di awal |
| Skill normalization | **ESCO taxonomy** sebagai base, + custom alias table untuk tools/tech spesifik | Taxonomy resmi, gratis, sudah battle-tested — jauh lebih robust daripada dictionary manual dari nol | ESCO lemah untuk tools/tech spesifik yang cepat berubah (mis. nama produk baru) — ditambal dengan alias table kecil yang di-maintain manual |
| Semantic search | **Embedding lokal (sentence-transformers, mis. `all-MiniLM-L6-v2`)** disimpan di pgvector | Gratis, tanpa rate limit, cukup akurat untuk skala data personal | Kualitas sedikit di bawah model embedding komersial (Voyage/OpenAI) — bisa upgrade nanti kalau relevansi hasil dirasa kurang |
| Scheduler | Cron sederhana, fetch 1x/hari | Cukup untuk kebutuhan freshness, pola traffic lebih "manusiawi" | Tidak scalable ke multi-user, tapi memang bukan tujuan sistem ini |

---

## 10. MVP Scope vs Fase 2

**MVP (fokus dulu):**
- 1-2 source adapter tervalidasi legal/feasible
- Extraction pipeline (LLM-based)
- Normalization dasar (manual dictionary)
- Search by keyword + link ke sumber
- Dashboard ranking hard/soft skill sederhana

**Fase 2 (setelah MVP tervalidasi):**
- Tambah sumber data lain
- Tren skill dari waktu ke waktu (time-series)
- Gap analysis otomatis (bandingkan CV/skill user vs market)
- Notifikasi loker baru yang match kriteria

---

## 11. Risiko & Open Questions

| Risiko | Mitigasi |
|--------|----------|
| Sumber data berubah struktur/API sewaktu-waktu | Adapter terisolasi per sumber (§6) |
| Akurasi ekstraksi LLM tidak konsisten | Spot-check manual di awal, refine prompt iteratif |
| Volume data loker IT terlalu sedikit dari sumber yang feasible → insight kurang representatif | Terima sebagai trade-off sadar untuk MVP; evaluasi ekspansi sumber di Fase 2 |
| Duplikasi loker (repost sama di beberapa sumber) | Deduplication berdasarkan title+company+similarity deskripsi (FR-10) |

**Keputusan yang sudah divalidasi (9 Agustus 2026):**
1. ✅ Sumber MVP: RemoteOK (official API) + WeWorkRemotely (official RSS). Field description dikonfirmasi berisi teks lengkap, cukup untuk LLM extraction. Glints & platform lain ditunda ke Fase 2.
2. ✅ Search API dan Dashboard dipisah sebagai dua service berbeda (FastAPI + Nuxt 3).
3. ✅ Fetch dijadwalkan harian via cron sederhana.
4. ✅ Skill normalization: ESCO taxonomy (`skills.csv`, format CSV, English) sebagai base, ditambal custom alias table untuk tools/tech spesifik.
5. ✅ Embedding strategy: dua jenis embedding dengan fungsi terpisah — skill-level embedding (precomputed sekali, dipakai untuk proses matching normalisasi ke Skill.id) dan job-level embedding (permanen per JobPosting, dipakai untuk semantic search FR-5).
6. ✅ Database: Supabase (Postgres + pgvector), frontend: Nuxt 3, embedding model: sentence-transformers lokal.

**Pertanyaan terbuka yang masih perlu divalidasi — bersifat empiris, baru bisa dijawab setelah pipeline & data riil tersedia (bukan di tahap dokumen):**
1. Threshold cosine similarity untuk semantic search — perlu eksperimen dengan 5-10 query contoh terhadap data riil pasca-fetch, manual-judge relevansi hasil untuk menentukan cutoff yang tepat.
2. Threshold similarity untuk matching skill mentah (hasil LLM extraction) ke Skill ESCO terdekat — perlu validasi serupa agar tidak salah mapping skill yang mirip tapi sebenarnya berbeda makna.

---

*Dokumen ini adalah draft awal. Struktur dan detail teknis (skema DB lengkap, prompt extraction, pemilihan adapter final) akan didetailkan setelah validasi sumber data di §7 selesai.*
