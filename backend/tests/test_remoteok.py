from __future__ import annotations

import json
import pathlib
from unittest import mock

from app.adapters.remoteok import RemoteOKAdapter

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "remoteok_sample.json"


def _load_fixture() -> list:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_skips_first_metadata_element() -> None:
    with mock.patch("httpx.Client.get") as fake_get:
        fake_get.return_value = mock.Mock(status_code=200, json=lambda: _load_fixture())
        jobs = RemoteOKAdapter().fetch()
    # 3 element fixture - 1 metadata = 2 jobs
    assert len(jobs) == 2
    assert all(j.title != "metadata_placeholder" for j in jobs)


def test_mapping_fields() -> None:
    with mock.patch("httpx.Client.get") as fake_get:
        fake_get.return_value = mock.Mock(status_code=200, json=lambda: _load_fixture())
        jobs = RemoteOKAdapter().fetch()
    job = jobs[0]
    assert job.source == "remoteok"
    assert job.source_id == "800101"
    assert job.title == "Senior Backend Engineer (Python)"
    assert job.company == "Acme Corp"
    assert job.source_url.startswith("https://remoteok.com/remote-jobs/")
    assert "PostgreSQL" in job.raw_description  # HTML sudah di-strip
    assert job.posted_date is not None


def test_filters_short_description() -> None:
    payload = _load_fixture()
    payload.append(
        {
            "id": 800103,
            "position": "Short Posting",
            "company": "X",
            "date": "2026-08-06T00:00:00.000Z",
            "url": "https://remoteok.com/remote-jobs/800103",
            "description": "<p>short</p>",
        }
    )
    with mock.patch("httpx.Client.get") as fake_get:
        fake_get.return_value = mock.Mock(status_code=200, json=lambda: payload)
        jobs = RemoteOKAdapter().fetch()
    assert all(j.title != "Short Posting" for j in jobs)


def test_handles_empty_payload() -> None:
    with mock.patch("httpx.Client.get") as fake_get:
        fake_get.return_value = mock.Mock(status_code=200, json=lambda: [])
        assert RemoteOKAdapter().fetch() == []
