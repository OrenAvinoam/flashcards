"""Thin typed wrappers around the internal service APIs."""
from typing import Any

import httpx

from web.config import get_settings

_settings = get_settings()


def _client(base_url: str, token: str | None = None) -> httpx.AsyncClient:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=10)


async def login(email: str, password: str) -> str:
    async with _client(_settings.auth_svc_url) as c:
        resp = await c.post("/login", json={"email": email, "password": password})
        resp.raise_for_status()
        return str(resp.json()["access_token"])


async def register(email: str, password: str) -> dict[str, Any]:
    async with _client(_settings.auth_svc_url) as c:
        resp = await c.post("/register", json={"email": email, "password": password})
        resp.raise_for_status()
        return dict(resp.json())


async def get_me(token: str) -> dict[str, Any]:
    async with _client(_settings.auth_svc_url, token) as c:
        resp = await c.get("/me")
        resp.raise_for_status()
        return dict(resp.json())


async def list_decks(token: str) -> list[dict[str, Any]]:
    async with _client(_settings.web_deck_svc_url, token) as c:
        resp = await c.get("/decks")
        resp.raise_for_status()
        return list(resp.json())


async def get_deck(token: str, deck_id: str) -> dict[str, Any]:
    async with _client(_settings.web_deck_svc_url, token) as c:
        resp = await c.get(f"/decks/{deck_id}")
        resp.raise_for_status()
        return dict(resp.json())


async def list_cards(token: str, deck_id: str) -> list[dict[str, Any]]:
    async with _client(_settings.web_deck_svc_url, token) as c:
        resp = await c.get(f"/decks/{deck_id}/cards")
        resp.raise_for_status()
        return list(resp.json())


async def create_deck(token: str, name: str) -> dict[str, Any]:
    async with _client(_settings.web_deck_svc_url, token) as c:
        resp = await c.post("/decks", json={"name": name})
        resp.raise_for_status()
        return dict(resp.json())


async def create_card(token: str, deck_id: str, front: str, back: str) -> dict[str, Any]:
    async with _client(_settings.web_deck_svc_url, token) as c:
        resp = await c.post(f"/decks/{deck_id}/cards", json={"front": front, "back": back})
        resp.raise_for_status()
        return dict(resp.json())


async def delete_card(token: str, card_id: str) -> None:
    async with _client(_settings.web_deck_svc_url, token) as c:
        resp = await c.delete(f"/cards/{card_id}")
        resp.raise_for_status()


async def get_due_cards(token: str, limit: int = 20) -> list[dict[str, Any]]:
    async with _client(_settings.web_scheduler_svc_url, token) as c:
        resp = await c.get("/due", params={"limit": limit})
        resp.raise_for_status()
        return list(resp.json())


async def review_card(token: str, card_id: str, grade: str) -> dict[str, Any]:
    async with _client(_settings.web_scheduler_svc_url, token) as c:
        resp = await c.post("/review", json={"card_id": card_id, "grade": grade})
        resp.raise_for_status()
        return dict(resp.json())


async def enqueue_generation(token: str, text: str, count: int = 10) -> str:
    async with _client(_settings.web_generation_svc_url, token) as c:
        resp = await c.post("/jobs/generate", data={"text": text, "count": str(count)})
        resp.raise_for_status()
        return str(resp.json()["job_id"])


async def enqueue_generation_pdf(token: str, pdf_bytes: bytes, filename: str, count: int = 10) -> str:
    async with _client(_settings.web_generation_svc_url, token) as c:
        resp = await c.post(
            "/jobs/generate",
            files={"file": (filename, pdf_bytes, "application/pdf")},
            data={"count": str(count)},
        )
        resp.raise_for_status()
        return str(resp.json()["job_id"])


async def get_job_status(token: str, job_id: str) -> dict[str, Any]:
    async with _client(_settings.web_generation_svc_url, token) as c:
        resp = await c.get(f"/jobs/{job_id}")
        resp.raise_for_status()
        return dict(resp.json())
