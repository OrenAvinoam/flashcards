"""LLM provider abstraction."""
import json
from typing import Protocol, runtime_checkable

import httpx
from pydantic import BaseModel


class CardDraft(BaseModel):
    front: str
    back: str


@runtime_checkable
class LLMProvider(Protocol):
    async def generate_cards(self, text: str, count: int = 10) -> list[CardDraft]: ...


_SYSTEM_PROMPT = (
    "You are an expert flashcard creator. Given a passage of text, generate concise, "
    "high-quality flashcards. Each flashcard has a 'front' (a question or prompt) and a "
    "'back' (the answer or explanation). Be specific and factual. Avoid vague questions. "
    "Return ONLY a JSON array of objects with 'front' and 'back' string fields."
)


class GeminiProvider:
    def __init__(self, api_key: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)

    async def generate_cards(self, text: str, count: int = 10) -> list[CardDraft]:
        from google import genai

        prompt = (
            f"{_SYSTEM_PROMPT}\n\nGenerate exactly {count} flashcards from this text:\n\n{text}\n\n"
            "Return ONLY the JSON array, no markdown, no explanation."
        )
        response = self._client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data: list[dict[str, str]] = json.loads(raw)
        return [CardDraft(front=d["front"], back=d["back"]) for d in data]


class OllamaProvider:
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def generate_cards(self, text: str, count: int = 10) -> list[CardDraft]:
        prompt = (
            f"{_SYSTEM_PROMPT}\n\nGenerate exactly {count} flashcards from this text:\n\n{text}\n\n"
            "Return ONLY the JSON array, no markdown, no explanation."
        )
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            raw = resp.json()["response"].strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data: list[dict[str, str]] = json.loads(raw)
        return [CardDraft(front=d["front"], back=d["back"]) for d in data]


def make_provider(provider: str, gemini_api_key: str, ollama_url: str, ollama_model: str) -> LLMProvider:
    if provider == "gemini":
        return GeminiProvider(api_key=gemini_api_key)
    if provider == "ollama":
        return OllamaProvider(base_url=ollama_url, model=ollama_model)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Must be 'gemini' or 'ollama'.")
