from __future__ import annotations

from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup

from app.adapters.base import AbstractJobAdapter
from app.config import get_settings
from app.models import RawJob

ADZUNA_API = "https://api.adzuna.com/v1/api/jobs"

# Negara yang direkrut — fokus pasar berbahasa Inggris (deskripsi layak extract)
ADZUNA_COUNTRIES = ["gb", "us"]
ADZUNA_CATEGORY = "it-jobs"

MIN_DESCRIPTION_LENGTH = 200

# Tanda deskripsi non-Inggris yang sering membuat extraction gagal / mojibake
_NON_EN_MARKERS = ["m/w/d", "fachinformatiker", "für", "und", "mit", "die ", "der ",
                   "des", "nous", "vous", "pour", "une ", "das ", "berlin", "münchen",
                   "frankfurt", "hamburg", "köln", "amsterdam", "rotterdam"]


def _is_english(text: str) -> bool:
    """Heuristik: deskripsi layak di-extract bila mayoritas berbahasa Inggris."""
    low = text.lower()
    # Tolak bila banyak mojibake/encoding rusak (karakter pengganti)
    if low.count("\ufffd") > 5:
        return False
    # Tolak bila ada marker bahasa asing khas
    marker_hits = sum(1 for m in _NON_EN_MARKERS if m in low)
    if marker_hits >= 2:
        return False
    return True


def _strip_html(html: str | None) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return None


class AdzunaAdapter(AbstractJobAdapter):
    """Adapter untuk Adzuna Jobs API — agregator loker global.

    Endpoint: https://api.adzuna.com/v1/api/jobs/{country}/search/1
    Filter IT via param `category=it-jobs` (bukan path category).
    Memerlukan ADZUNA_APP_ID & ADZUNA_APP_KEY di .env.
    Deskripsi yang dikembalikan API hanya snippet — cukup untuk ekstraksi.
    """

    source = "adzuna"

    def fetch(self) -> list[RawJob]:
        settings = get_settings()
        app_id = settings.adzuna_app_id
        app_key = settings.adzuna_app_key

        if not app_id or not app_key:
            print("[adzuna] SKIP: ADZUNA_APP_ID / ADZUNA_APP_KEY belum di-set di .env")
            return []

        headers = {"User-Agent": "JobIntel-Personal/0.1 (personal research tool)"}
        jobs: list[RawJob] = []
        seen: set[str] = set()

        for country in ADZUNA_COUNTRIES:
            try:
                params = {
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": 50,
                    "content-type": "application/json",
                    "category": ADZUNA_CATEGORY,
                }
                url = f"{ADZUNA_API}/{country}/search/1"
                with httpx.Client(timeout=settings.http_timeout, headers=headers) as client:
                    resp = client.get(url, params=params)
                    resp.raise_for_status()
                    payload = resp.json()
            except Exception as exc:  # noqa: BLE001
                print(f"[adzuna] {country} gagal: {exc}")
                continue

            for item in payload.get("results") or []:
                adz_id = str(item.get("id") or "").strip()
                if not adz_id:
                    continue
                # source_id harus unik global — prepend negara agar tak bentrok antar negara
                source_id = f"{country}-{adz_id}"
                if source_id in seen:
                    continue
                seen.add(source_id)

                raw_description = _strip_html(item.get("description", ""))
                if len(raw_description) < MIN_DESCRIPTION_LENGTH:
                    continue
                if not _is_english(raw_description):
                    continue

                company_obj = item.get("company") or {}
                location_obj = item.get("location") or {}

                jobs.append(
                    RawJob(
                        source=self.source,
                        source_id=source_id,
                        title=(item.get("title") or "").strip(),
                        company=company_obj.get("display_name"),
                        source_url=item.get("redirect_url") or "",
                        raw_description=raw_description,
                        location=location_obj.get("display_name"),
                        posted_date=_parse_date(item.get("created")),
                    )
                )
        print(f"[adzuna] total jobs: {len(jobs)}")
        return jobs
