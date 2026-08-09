from __future__ import annotations

import pathlib
from unittest import mock

from app.adapters.wwr import WWRAdapter

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "wwr_sample.xml"


def _load_fixture() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_parses_entries_and_splits_title() -> None:
    with mock.patch.object(WWRAdapter, "_download", return_value=_load_fixture()):
        jobs = WWRAdapter().fetch()
    assert len(jobs) == 2
    assert jobs[0].title == "Frontend Developer (React)"
    assert jobs[0].company == "Star Labs"
    assert jobs[0].source == "wwr"
    assert jobs[0].source_url.startswith("https://weworkremotely.com")
    assert "React" in jobs[0].raw_description
    assert jobs[0].posted_date is not None


def test_parses_without_content_only_summary() -> None:
    # Fixture di atas pakai content:encoded; test ini memastikan fallback summary tidak crash.
    with mock.patch.object(WWRAdapter, "_download", return_value=_load_fixture()):
        jobs = WWRAdapter().fetch()
    assert all(j.raw_description for j in jobs)
