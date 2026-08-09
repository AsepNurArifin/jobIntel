from __future__ import annotations

import time
from typing import Literal

from app.adapters import REGISTRY
from app.config import get_settings
from app.db import get_client

StepName = Literal["fetch", "dedup", "extract", "normalize", "embed", "all"]


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _log(step: str, message: str) -> None:
    print(f"[{_now()}] [{step}] {message}")


async def run_pipeline(step: StepName = "all", source: str = "all") -> dict:
    settings = get_settings()
    client = get_client()
    stats: dict = {}

    if step in ("fetch", "all"):
        from app.pipeline import dedup as _  # noqa: F401  (pastikan import OK)
        stats.update(await _run_fetch(client, source))

    if step in ("dedup", "all"):
        from app.pipeline.dedup import run_dedup

        n_flagged = run_dedup(client)
        stats["dedup_flagged"] = n_flagged
        _log("dedup", f"flagged={n_flagged}")

    if step in ("extract", "all"):
        from app.pipeline.extractor import run_extraction

        n_done, n_failed = await run_extraction(client, settings)
        stats["extracted"] = n_done
        stats["extract_failed"] = n_failed
        _log("extract", f"done={n_done} failed={n_failed}")

    if step in ("normalize", "all"):
        from app.pipeline.normalizer import run_normalization

        n_normalized = await run_normalization(client, settings)
        stats["normalized"] = n_normalized
        _log("normalize", f"normalized={n_normalized}")

    if step in ("embed", "all"):
        from app.pipeline.embedder import run_job_embedding

        n_embedded = await run_job_embedding(client, settings)
        stats["embedded"] = n_embedded
        _log("embed", f"embedded={n_embedded}")

    return stats


async def _run_fetch(client, source: str) -> dict:
    from app.pipeline.dedup import upsert_raw_jobs

    total_fetched = 0
    total_inserted = 0
    for source_name, adapter_cls in REGISTRY.items():
        if source != "all" and source != source_name:
            continue
        try:
            adapter = adapter_cls()
            jobs = adapter.fetch()
            _log("fetch", f"{source_name}: fetched={len(jobs)}")
            inserted = upsert_raw_jobs(client, jobs)
            total_fetched += len(jobs)
            total_inserted += inserted
        except Exception as exc:  # noqa: BLE001
            _log("fetch", f"{source_name}: ERROR {exc}")

    result = {"fetched": total_fetched, "inserted": total_inserted}
    _log("fetch", f"total fetched={total_fetched} inserted={total_inserted}")
    return result
