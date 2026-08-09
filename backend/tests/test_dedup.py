from __future__ import annotations

from app.pipeline.dedup import _normalize_key


def test_normalize_key_lowercase_and_punctuation() -> None:
    assert _normalize_key("Senior Backend Engineer!", "Acme-Corp") == "senior backend engineer acme corp"


def test_normalize_key_whitespace() -> None:
    assert _normalize_key("  Python  Developer ", "  X  ") == "python developer x"


def test_normalize_key_same_meaning() -> None:
    a = _normalize_key("Data Scientist", "ABC Ltd")
    b = _normalize_key("data-scientist", "abc ltd")
    assert a == b


def test_normalize_key_none_handling() -> None:
    assert _normalize_key("DevOps", None) == "devops"
