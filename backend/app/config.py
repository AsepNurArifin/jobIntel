from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_key: str = ""

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_retries: int = 3

    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    scheduler_enabled: bool = False
    fetch_cron_hour: int = 6

    search_threshold: float = 0.25  # final §13 (11-08-2026, 187 posting): precision top-10 ~70-80% utk query dgn data cukup
    skill_match_threshold: float = 0.80  # final §13 (11-08-2026): false-mapping minimal, coverage wajar
    role_filter_distance: float = 0.75

    extraction_version: int = 1
    http_timeout: int = 30
    max_description_chars: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
