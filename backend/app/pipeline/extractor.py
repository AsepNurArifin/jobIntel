from __future__ import annotations

import json
import time
from typing import Any

from groq import Groq

from app.config import Settings
from app.models import ExtractionResult

SYSTEM_PROMPT = """You are a precise information extraction system for IT job postings.
Extract ONLY what is explicitly written in the job description. Never infer
or add skills that are not mentioned. Return a single JSON object with
exactly these keys:

{
  "hard_skills": [string],
  "soft_skills": [string],
  "tools": [string],
  "experience_level": "junior" | "mid" | "senior" | "unknown",
  "min_years_experience": number | null,
  "employment_type": "remote" | "onsite" | "hybrid" | "unknown"
}

Rules:
- All skill strings lowercase, trimmed, no duplicates.
- hard_skills = capabilities; tools = named products. "python" is a hard
  skill; "pandas" is a tool. "sql" is a hard skill; "postgresql" is a tool.
- If nothing found for a key, return [] (or null / "unknown").
- Ignore benefits, salary, company description, and legal boilerplate.
- Output ONLY the JSON object, no markdown, no commentary."""


def build_user_message(title: str, description: str, max_chars: int = 8000) -> str:
    return f"JOB TITLE: {title}\n\nJOB DESCRIPTION:\n{description[:max_chars]}"


def _extract_json(text: str) -> dict:
    """Robust JSON parsing: cari blok JSON walau LLM menambahkan noise."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def extract_one(
    client: Groq,
    model: str,
    title: str,
    description: str,
    max_chars: int = 8000,
    include_evidence: bool = False,
) -> ExtractionResult:
    """Satu call extraction. `include_evidence` dipakai mode spot-check.

    Raises RuntimeError kalau LLM gagal / rate limited (dipakai retry di caller).
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if include_evidence:
        messages[0]["content"] += (
            "\n\nAdditionally, return a key \"evidence\" mapping each skill name "
            "to the exact sentence in the job description that supports it. "
            "This is for QA review only."
        )
    messages.append({"role": "user", "content": build_user_message(title, description, max_chars)})

    response = client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq mengembalikan konten kosong")

    data = _extract_json(content)
    return ExtractionResult(
        hard_skills=data.get("hard_skills") or [],
        soft_skills=data.get("soft_skills") or [],
        tools=data.get("tools") or [],
        experience_level=str(data.get("experience_level", "unknown")).lower(),
        min_years_experience=data.get("min_years_experience"),
        employment_type=str(data.get("employment_type", "unknown")).lower(),
    )


async def run_extraction(client: Any, settings: Settings) -> tuple[int, int]:
    """Extract semua posting yang status pending/failed (retry < 3).

    Returns (n_done, n_failed).
    """
    db = client
    groq = Groq(api_key=settings.groq_api_key)

    # Kandidat: belum done, versi outdated, bukan duplikat, retry < 3
    candidates = (
        db.table("job_postings")
        .select("id, title, raw_description, retry_count")
        .or_(
            f"extraction_status.eq.pending,extraction_status.eq.failed,"
            f"and(extraction_status.eq.done,extraction_version.lt.{settings.extraction_version})"
        )
        .lt("retry_count", 3)
        .is_("is_duplicate_of", "null")
        .limit(100)
        .execute()
    )

    n_done = 0
    n_failed = 0
    for row in candidates.data or []:
        pid = row["id"]
        try:
            result = extract_one(
                groq,
                settings.groq_model,
                row.get("title", ""),
                row.get("raw_description", ""),
                max_chars=settings.max_description_chars,
            )
            db.table("extracted_requirements").upsert(
                {
                    "job_posting_id": pid,
                    "hard_skills_raw": result.hard_skills,
                    "soft_skills_raw": result.soft_skills,
                    "tools_raw": result.tools,
                    "experience_level": result.experience_level,
                    "min_years_experience": result.min_years_experience,
                    "employment_type": result.employment_type,
                },
                on_conflict="job_posting_id",
            ).execute()
            db.table("job_postings").update(
                {"extraction_status": "done", "extraction_version": settings.extraction_version}
            ).eq("id", pid).execute()
            n_done += 1
        except Exception:
            n_failed += 1
            try:
                db.table("job_postings").update(
                    {
                        "extraction_status": "failed",
                        "retry_count": int(row.get("retry_count") or 0) + 1,
                    }
                ).eq("id", pid).execute()
            except Exception:
                pass
        time.sleep(0.2)  # gentle pacing ke Groq

    return n_done, n_failed
