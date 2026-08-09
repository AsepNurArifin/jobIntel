from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "Supabase belum dikonfigurasi. Set SUPABASE_URL dan "
            "SUPABASE_SERVICE_KEY di backend/.env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)


def healthcheck() -> bool:
    try:
        client = get_client()
        client.table("job_postings").select("id").limit(1).execute()
        return True
    except Exception:
        return False
