from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import bookmarks, search, skills
from app.config import get_settings
from app.db import healthcheck


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    from app.pipeline.embedder import _get_model

    _get_model(settings)  # warm-up model embedding (hindari timeout request pertama)
    scheduler = None
    if settings.scheduler_enabled:
        from app.scheduler import start_scheduler

        scheduler = start_scheduler()
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="JobIntel Search API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(search.router)
    app.include_router(skills.router)
    app.include_router(bookmarks.router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "db": "connected" if healthcheck() else "disconnected"}

    return app


app = create_app()
