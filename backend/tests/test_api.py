from __future__ import annotations

from unittest import mock

from fastapi.testclient import TestClient

from app.main import create_app


class _RPCResult:
    def __init__(self, data):
        self.data = data


class _FakeRPC:
    def __init__(self, fn):
        self.fn = fn
        self.args = None

    def rpc(self, name, args):
        self.args = args
        return _FakeRPCCall(self.fn(name, args))

    def table(self, name):
        return _FakeTable(self.fn, name)


class _FakeRPCCall:
    def __init__(self, data):
        self._data = data

    def execute(self):
        return _RPCResult(self._data)


class _FakeTable:
    def __init__(self, fn, name):
        self.fn = fn
        self.name = name

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def in_(self, *a, **k):
        return self

    def is_(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        return _RPCResult(self.fn("table", self.name))


def _make_client(search_rows=None):
    """Fake supabase client: RPC search_jobs/top_skills/count + table skills."""
    if search_rows is None:
        search_rows = []

    def fn(name, args=None):
        if name == "search_jobs":
            return search_rows
        if name == "top_skills":
            return [
                {"name": "python", "category": "hard", "freq": 22},
                {"name": "aws", "category": "tool", "freq": 27},
            ]
        if name == "count_postings_in_days":
            return 185
        if name == "table" and args == "skills":
            return [{"id": 1, "canonical_name": "python"}]
        return []

    return _FakeRPC(fn)


def test_search_returns_contract_object():
    """Regresi B12 & FIX-4.1: /api/search return {query, count, results}, bukan 500."""
    rows = [
        {
            "id": 1,
            "title": "Backend Engineer",
            "company": "Acme",
            "source": "remoteok",
            "source_url": "https://remoteok.com/x",
            "posted_date": "2026-08-01",
            "location": "Worldwide",
            "similarity": 0.61,
        }
    ]
    client = _make_client(search_rows=rows)
    app = create_app()
    with mock.patch("app.api.search.get_client", return_value=client):
        with mock.patch("app.api.search.encode", return_value=[[0.1] * 384]):
            resp = TestClient(app).get("/api/search", params={"q": "python", "days": 30, "limit": 5})

    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"query", "count", "results"}
    assert body["query"] == "python"
    assert body["count"] == 1
    assert body["results"][0]["title"] == "Backend Engineer"


def test_search_empty_result_returns_contract():
    client = _make_client(search_rows=[])
    app = create_app()
    with mock.patch("app.api.search.get_client", return_value=client):
        with mock.patch("app.api.search.encode", return_value=[[0.1] * 384]):
            resp = TestClient(app).get("/api/search", params={"q": "nonsense", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["results"] == []


def test_search_validation_422():
    app = create_app()
    with mock.patch("app.api.search.get_client", return_value=_make_client()):
        resp = TestClient(app).get("/api/search", params={"q": "   "})
    assert resp.status_code == 422
    resp2 = TestClient(app).get("/api/search", params={"q": "x", "limit": 101})
    assert resp2.status_code == 422


def test_health_ok():
    app = create_app()
    with mock.patch("app.api.search.get_client", return_value=_make_client()):
        with mock.patch("app.db.healthcheck", return_value=True):
            resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db": "connected"}


def test_skills_top_returns_contract():
    app = create_app()
    with mock.patch("app.api.skills.get_client", return_value=_make_client()):
        with mock.patch("app.api.skills.encode", return_value=[[0.1] * 384]):
            resp = TestClient(app).get("/api/skills/top", params={"days": 30})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"filters", "n_postings", "skills"}
    assert body["n_postings"] == 185
    assert body["skills"][0]["name"] == "python"
