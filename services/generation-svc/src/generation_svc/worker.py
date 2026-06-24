"""arq worker for card generation jobs."""
import io
from typing import Any

import pypdf
from arq import create_pool
from arq.connections import RedisSettings

from generation_svc.config import get_settings
from generation_svc.providers import CardDraft, make_provider

_settings = get_settings()


def _redis_settings() -> RedisSettings:
    url = _settings.redis_url
    # arq RedisSettings from URL
    return RedisSettings.from_dsn(url)


async def generate_cards_job(
    ctx: dict[str, Any],
    text: str,
    count: int = 10,
) -> list[dict[str, str]]:
    provider = make_provider(
        _settings.llm_provider,
        _settings.gemini_api_key,
        _settings.ollama_url,
        _settings.ollama_model,
    )
    drafts: list[CardDraft] = await provider.generate_cards(text, count)
    return [{"front": d.front, "back": d.back} for d in drafts]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts)


class WorkerSettings:
    functions = [generate_cards_job]
    redis_settings = _redis_settings()
    max_jobs = 10
    job_timeout = 300
