import json
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from flashcards_common.http import make_http_client
from flashcards_common.jwt import JWTUser, jwt_dependency
from scheduler_svc.config import get_settings
from scheduler_svc.fsrs_helper import apply_review, is_due

router = APIRouter()
_settings = get_settings()
_get_current_user = jwt_dependency(_settings.jwt_secret)
CurrentUser = Annotated[JWTUser, Depends(_get_current_user)]

CACHE_TTL = 60  # seconds


def _redis_key(user_id: uuid.UUID) -> str:
    return f"due:{user_id}"


class ReviewRequest(BaseModel):
    card_id: uuid.UUID
    grade: str


class DueCard(BaseModel):
    id: uuid.UUID
    deck_id: uuid.UUID
    front: str
    back: str
    fsrs_state: dict[str, Any]


class ReviewResponse(BaseModel):
    card_id: uuid.UUID
    due_at: str | None


async def _get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    return aioredis.from_url(_settings.redis_url, decode_responses=True)


async def _fetch_due_cards(user_id: uuid.UUID, limit: int, token: str) -> list[dict[str, Any]]:
    async with make_http_client(_settings.deck_svc_url) as client:
        decks_resp = await client.get(
            "/decks", headers={"Authorization": f"Bearer {token}"}
        )
        decks_resp.raise_for_status()
        decks = decks_resp.json()

    due: list[dict[str, Any]] = []
    async with make_http_client(_settings.deck_svc_url) as client:
        for deck in decks:
            cards_resp = await client.get(
                f"/decks/{deck['id']}/cards",
                headers={"Authorization": f"Bearer {token}"},
            )
            cards_resp.raise_for_status()
            for card in cards_resp.json():
                if is_due(card.get("fsrs_state", {})):
                    due.append(card)

    due.sort(key=lambda c: c.get("fsrs_state", {}).get("due_at") or "")
    return due[:limit]


@router.get("/due", response_model=list[DueCard])
async def get_due(
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict[str, Any]]:
    redis = await _get_redis()
    cache_key = _redis_key(user.user_id)

    cached = await redis.get(cache_key)
    if cached:
        cards: list[dict[str, Any]] = json.loads(cached)
        return cards[:limit]

    # Need to fetch — but we don't have the raw token here, only the decoded user.
    # We store the raw token in the request state via middleware (see main.py).
    # For simplicity in the scheduler, we rely on the user header forwarded from web.
    # Actually, the simplest design: the scheduler receives the Bearer token and
    # forwards it directly to deck-svc. We extract it from the dependency.
    # We use a workaround: store token in a context var set by the auth dependency.
    from scheduler_svc.token_context import current_token
    token = current_token.get("")
    cards = await _fetch_due_cards(user.user_id, limit, token)
    await redis.setex(cache_key, CACHE_TTL, json.dumps(cards))
    return cards


@router.post("/review", response_model=ReviewResponse)
async def review_card(
    body: ReviewRequest,
    user: CurrentUser,
) -> ReviewResponse:
    from scheduler_svc.token_context import current_token
    token = current_token.get("")

    # Fetch card from deck-svc
    async with make_http_client(_settings.deck_svc_url) as client:
        resp = await client.get(
            f"/cards/{body.card_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        resp.raise_for_status()
        card = resp.json()

    # Apply FSRS
    try:
        new_state = apply_review(card.get("fsrs_state", {}), body.grade)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # Persist updated state back to deck-svc
    async with make_http_client(_settings.deck_svc_url) as client:
        patch_resp = await client.patch(
            f"/cards/{body.card_id}",
            json={"fsrs_state": new_state},
            headers={"Authorization": f"Bearer {token}"},
        )
        patch_resp.raise_for_status()

    # Invalidate cache
    redis = await _get_redis()
    await redis.delete(_redis_key(user.user_id))

    return ReviewResponse(card_id=body.card_id, due_at=new_state.get("due_at"))
