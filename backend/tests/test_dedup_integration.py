from __future__ import annotations

from app.pipeline.dedup import _normalize_key, run_dedup, upsert_raw_jobs
from app.models import RawJob


class FakeQuery:
    """Minimal chained query builder untuk mensimulasikan PostgREST."""

    def __init__(self, data):
        self._data = data

    def execute(self):
        return _Result(self._data)

    def select(self, *args, **kwargs):
        return self

    def is_(self, *a, **k):
        return self

    def gte(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def in_(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def range(self, *a, **k):
        return self

    def maybe_single(self):
        return self


class _Result:
    def __init__(self, data):
        self.data = data
        self.count = len(data)


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.updated = []

    def table(self, name):
        return _Table(self, name)


class _Table:
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def select(self, *args, **kwargs):
        return FakeQuery(self.client.rows)

    def update(self, payload):
        self.client.updated.append(("update", payload))
        return FakeQuery([])

    def insert(self, payload, **kwargs):
        self.client.updated.append(("insert", payload))
        return FakeQuery([payload])

    def upsert(self, payload, **kwargs):
        self.client.updated.append(("upsert", payload))
        return FakeQuery([payload])

    def delete(self):
        return FakeQuery([])


def test_normalize_key_handles_special_chars() -> None:
    assert _normalize_key("C++", "Foo") == "c foo"


def test_dedup_flags_cross_source_duplicate() -> None:
    rows = [
        {"id": 1, "source": "remoteok", "title": "Backend Engineer", "company": "Acme", "is_duplicate_of": None},
        {"id": 2, "source": "wwr", "title": "Backend Engineer", "company": "Acme", "is_duplicate_of": None},
    ]
    client = FakeClient(rows)
    flagged = run_dedup(client, window_days=90)
    assert flagged == 1
    updates = [u for u in client.updated if u[0] == "update"]
    assert any(payload.get("is_duplicate_of") == 1 for _, payload in updates)


def test_dedup_ignores_same_source() -> None:
    rows = [
        {"id": 1, "source": "remoteok", "title": "Dev", "company": "X", "is_duplicate_of": None},
        {"id": 2, "source": "remoteok", "title": "Dev", "company": "X", "is_duplicate_of": None},
    ]
    client = FakeClient(rows)
    assert run_dedup(client, window_days=90) == 0


def test_upsert_raw_jobs_empty() -> None:
    assert upsert_raw_jobs(FakeClient([]), []) == 0


def test_upsert_raw_jobs_inserts_new() -> None:
    job = RawJob(
        source="remoteok",
        source_id="abc",
        title="Engineer",
        source_url="https://x",
        raw_description="d" * 300,
    )
    client = FakeClient([{"source": "remoteok", "source_id": "other"}])
    n = upsert_raw_jobs(client, [job])
    assert n == 1
