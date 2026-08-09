from __future__ import annotations

from app.pipeline.extractor import _extract_json
from app.pipeline.normalizer import categorize_label


def test_categorize_hard() -> None:
    assert categorize_label("python") == "hard"
    assert categorize_label("use object-oriented programming") == "hard"


def test_categorize_soft() -> None:
    assert categorize_label("communication") == "soft"
    assert categorize_label("show initiative") == "soft"


def test_extract_json_clean() -> None:
    data = _extract_json('{"hard_skills": ["python"]}')
    assert data == {"hard_skills": ["python"]}


def test_extract_json_with_noise() -> None:
    data = _extract_json('Here you go:\n```json\n{"a": 1}\n```')
    assert data == {"a": 1}


def test_extract_json_raises_on_invalid() -> None:
    import pytest

    with pytest.raises(Exception):
        _extract_json("no json here")
