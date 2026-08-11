from __future__ import annotations

from app.adapters.base import AbstractJobAdapter

REGISTRY: dict[str, type[AbstractJobAdapter]] = {}


def _register() -> None:
    from app.adapters.adzuna import AdzunaAdapter
    from app.adapters.remoteok import RemoteOKAdapter
    from app.adapters.wwr import WWRAdapter

    for cls in (RemoteOKAdapter, WWRAdapter, AdzunaAdapter):
        REGISTRY[cls.source] = cls


_register()
