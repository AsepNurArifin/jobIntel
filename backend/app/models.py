from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class RawJob(BaseModel):
    """Kontrak output semua adapter — field wajib/nullable disepakati di plan §6.2."""

    source: str
    source_id: str
    title: str
    company: str | None = None
    source_url: str
    raw_description: str
    location: str | None = None
    posted_date: date | None = None


class ExtractionResult(BaseModel):
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    experience_level: str = "unknown"
    min_years_experience: float | None = None
    employment_type: str = "unknown"


class SearchResult(BaseModel):
    id: int
    title: str
    company: str | None
    source: str
    source_url: str
    posted_date: date | None
    location: str | None
    similarity: float
    top_skills: list[str] = Field(default_factory=list)
    description: str = ""
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    experience_level: str = "unknown"
    min_years_experience: float | None = None
    employment_type: str = "unknown"


class SkillRank(BaseModel):
    name: str
    category: str
    freq: int
