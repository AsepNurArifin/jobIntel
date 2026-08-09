from __future__ import annotations

import time
from typing import Any

from app.config import Settings

_model = None
_model_name: str | None = None


def _get_model(settings: Settings):
    global _model, _model_name
    if _model is None or _model_name != settings.embedding_model:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)
        _model_name = settings.embedding_model
    return _model


def encode(texts: list[str], settings: Settings) -> list[list[float]]:
    """Encode list teks → list vector. Lazy-load model sekali."""
    if not texts:
        return []
    model = _get_model(settings)
    vecs = model.encode(texts, batch_size=32, show_progress_bar=False)
    return [v.tolist() for v in vecs]


def job_embedding_text(title: str, description: str, max_chars: int = 2000) -> str:
    return f"{title}\n{description[:max_chars]}"


async def run_job_embedding(client: Any, settings: Settings) -> int:
    """Isi job_postings.embedding untuk semua posting done yang belum di-embed."""
    rows = (
        client.table("job_postings")
        .select("id, title, raw_description")
        .eq("extraction_status", "done")
        .is_("embedding", "null")
        .is_("is_duplicate_of", "null")
        .limit(200)
        .execute()
    ).data or []

    if not rows:
        return 0

    texts = [job_embedding_text(r.get("title", ""), r.get("raw_description", "")) for r in rows]
    vectors = encode(texts, settings)

    n = 0
    for row, vec in zip(rows, vectors):
        try:
            client.table("job_postings").update({"embedding": vec}).eq("id", row["id"]).execute()
            n += 1
        except Exception:
            continue
        time.sleep(0.05)
    return n
