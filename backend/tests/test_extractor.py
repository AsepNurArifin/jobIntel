from __future__ import annotations

import pytest

from app.models import ExtractionResult
from app.pipeline.extractor import _extract_json, build_user_message, extract_one


class _FakeChoice:
    def __init__(self, content: str | None):
        self.message = _FakeMessage(content)


class _FakeMessage:
    def __init__(self, content: str | None):
        self.content = content


class _FakeResponse:
    def __init__(self, content: str | None):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, response):
        self._response = response

    def create(self, **kwargs):
        return self._response


class _FakeChat:
    def __init__(self, response):
        self.completions = _FakeCompletions(response)


class _FakeGroq:
    def __init__(self, response):
        self.chat = _FakeChat(response)


def test_extract_one_parses_valid_json() -> None:
    client = _FakeGroq(_FakeResponse('{"hard_skills": ["python"], "tools": [], "soft_skills": [], '
                                     '"experience_level": "senior", "min_years_experience": 3, '
                                     '"employment_type": "remote"}'))
    result = extract_one(client, "llama-3.3-70b-versatile", "Backend Engineer", "desc")
    assert isinstance(result, ExtractionResult)
    assert result.hard_skills == ["python"]
    assert result.experience_level == "senior"
    assert result.min_years_experience == 3


def test_extract_one_handles_missing_keys() -> None:
    client = _FakeGroq(_FakeResponse('{"hard_skills": ["go"]}'))
    result = extract_one(client, "m", "T", "d")
    assert result.hard_skills == ["go"]
    assert result.soft_skills == []
    assert result.tools == []
    assert result.experience_level == "unknown"


def test_extract_one_raises_on_empty_content() -> None:
    client = _FakeGroq(_FakeResponse(None))
    with pytest.raises(RuntimeError):
        extract_one(client, "m", "T", "d")


def test_build_user_message_truncates() -> None:
    msg = build_user_message("Title", "x" * 100, max_chars=20)
    assert len(msg) < 80  # title + prefix + 20 chars desc


def test_extract_json_handles_embedded_json() -> None:
    data = _extract_json('prefix {"a": [1, 2]} suffix')
    assert data == {"a": [1, 2]}
