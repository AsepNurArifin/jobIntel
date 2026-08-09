from __future__ import annotations

from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx
from bs4 import BeautifulSoup

from app.adapters.base import AbstractJobAdapter
from app.config import get_settings
from app.models import RawJob

WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]

MIN_DESCRIPTION_LENGTH = 200


def _strip_html(html: str | None) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def _parse_published(value: str | None) -> date | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        return dt.date()
    except (ValueError, TypeError):
        return None


def _split_title(title: str) -> tuple[str, str | None]:
    """Format WWR: 'Company: Position'."""
    if ":" in title:
        company, _, position = title.partition(":")
        return position.strip(), company.strip()
    return title.strip(), None


class WWRAdapter(AbstractJobAdapter):
    source = "wwr"

    def fetch(self) -> list[RawJob]:
        settings = get_settings()
        seen: set[str] = set()
        jobs: list[RawJob] = []

        for feed_url in WWR_FEEDS:
            try:
                raw_xml = self._download(feed_url, settings.http_timeout)
                feed = feedparser.parse(raw_xml)
            except Exception as exc:  # noqa: BLE001
                print(f"[wwr] feed {feed_url} gagal: {exc}")
                continue

            for entry in feed.entries:
                guid = entry.get("id") or entry.get("link") or ""
                if not guid or guid in seen:
                    continue
                seen.add(guid)

                raw_description = _strip_html(
                    entry.get("content", [{}])[0].get("value", "")
                    if entry.get("content")
                    else entry.get("summary", "")
                )
                if len(raw_description) < MIN_DESCRIPTION_LENGTH:
                    continue

                title, company = _split_title(entry.get("title", ""))
                jobs.append(
                    RawJob(
                        source=self.source,
                        source_id=guid,
                        title=title,
                        company=company,
                        source_url=entry.get("link", ""),
                        raw_description=raw_description,
                        location=entry.get("region") or None,
                        posted_date=_parse_published(entry.get("published")),
                    )
                )
        return jobs

    @staticmethod
    def _download(url: str, timeout: int) -> str:
        headers = {"User-Agent": "JobIntel-Personal/0.1 (personal research tool)"}
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
