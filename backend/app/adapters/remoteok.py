from __future__ import annotations

import json
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup

from app.adapters.base import AbstractJobAdapter
from app.config import get_settings
from app.models import RawJob

REMOTEOK_API = "https://remoteok.com/api"

MIN_DESCRIPTION_LENGTH = 200


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
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


class RemoteOKAdapter(AbstractJobAdapter):
    source = "remoteok"

    def fetch(self) -> list[RawJob]:
        settings = get_settings()
        headers = {"User-Agent": "JobIntel-Personal/0.1 (personal research tool)"}

        with httpx.Client(timeout=settings.http_timeout) as client:
            resp = client.get(REMOTEOK_API, headers=headers)
            resp.raise_for_status()
            payload = resp.json()

        # Elemen pertama adalah metadata/legal — harus di-skip.
        if not isinstance(payload, list) or len(payload) < 2:
            return []

        jobs: list[RawJob] = []
        for item in payload[1:]:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            raw_description = _strip_html(item.get("description", ""))
            if len(raw_description) < MIN_DESCRIPTION_LENGTH:
                continue
            jobs.append(
                RawJob(
                    source=self.source,
                    source_id=str(item.get("id")),
                    title=item.get("position", "").strip(),
                    company=item.get("company"),
                    source_url=item.get("url", ""),
                    raw_description=raw_description,
                    location=item.get("location"),
                    posted_date=_parse_date(item.get("date")),
                )
            )
        return jobs
