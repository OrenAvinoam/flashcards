import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deck_svc.config import get_settings
from deck_svc.database import get_db
from deck_svc.models import Card, Deck
from deck_svc.schemas import (
    CardCreate,
    CardResponse,
    CardUpdate,
    DeckCreate,
    DeckResponse,
    DeckUpdate,
)
from flashcards_common.jwt import JWTUser, jwt_dependency

router = APIRouter()
_settings = get_settings()
_get_current_user = jwt_dependency(_settings.jwt_secret)
CurrentUser = Annotated[JWTUser, Depends(_get_current_user)]
DB = Annotated[AsyncSession, Depends(get_db)]


async def _get_deck_or_404(deck_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Deck:
    result = await db.execute(select(Deck).where(Deck.id == deck_id, Deck.user_id == user_id))
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
    return deck


async def _get_card_or_404(card_id: uuid.UUID, db: AsyncSession) -> Card:
    result = await db.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


# --- Deck routes ---

@router.post("/decks", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(body: DeckCreate, user: CurrentUser, db: DB) -> Deck:
    deck = Deck(user_id=user.user_id, name=body.name)
    db.add(deck)
    await db.commit()
    await db.refresh(deck)
    return deck


@router.get("/decks", response_model=list[DeckResponse])
async def list_decks(user: CurrentUser, db: DB) -> list[Deck]:
    result = await db.execute(select(Deck).where(Deck.user_id == user.user_id).order_by(Deck.created_at))
    return list(result.scalars().all())


@router.get("/decks/{deck_id}", response_model=DeckResponse)
async def get_deck(deck_id: uuid.UUID, user: CurrentUser, db: DB) -> Deck:
    return await _get_deck_or_404(deck_id, user.user_id, db)


@router.patch("/decks/{deck_id}", response_model=DeckResponse)
async def update_deck(deck_id: uuid.UUID, body: DeckUpdate, user: CurrentUser, db: DB) -> Deck:
    deck = await _get_deck_or_404(deck_id, user.user_id, db)
    if body.name is not None:
        deck.name = body.name
    await db.commit()
    await db.refresh(deck)
    return deck


@router.delete("/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck(deck_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    deck = await _get_deck_or_404(deck_id, user.user_id, db)
    await db.delete(deck)
    await db.commit()


# --- Card routes ---

@router.post("/decks/{deck_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(deck_id: uuid.UUID, body: CardCreate, user: CurrentUser, db: DB) -> Card:
    await _get_deck_or_404(deck_id, user.user_id, db)
    card = Card(deck_id=deck_id, front=body.front, back=body.back, fsrs_state={})
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return card


@router.get("/decks/{deck_id}/cards", response_model=list[CardResponse])
async def list_cards(deck_id: uuid.UUID, user: CurrentUser, db: DB) -> list[Card]:
    await _get_deck_or_404(deck_id, user.user_id, db)
    result = await db.execute(select(Card).where(Card.deck_id == deck_id).order_by(Card.created_at))
    return list(result.scalars().all())


@router.patch("/cards/{card_id}", response_model=CardResponse)
async def update_card(card_id: uuid.UUID, body: CardUpdate, user: CurrentUser, db: DB) -> Card:
    card = await _get_card_or_404(card_id, db)
    await _get_deck_or_404(card.deck_id, user.user_id, db)
    if body.front is not None:
        card.front = body.front
    if body.back is not None:
        card.back = body.back
    if body.fsrs_state is not None:
        card.fsrs_state = body.fsrs_state
    await db.commit()
    await db.refresh(card)
    return card


@router.get("/cards/{card_id}", response_model=CardResponse)
async def get_card(card_id: uuid.UUID, user: CurrentUser, db: DB) -> Card:
    card = await _get_card_or_404(card_id, db)
    await _get_deck_or_404(card.deck_id, user.user_id, db)
    return card


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(card_id: uuid.UUID, user: CurrentUser, db: DB) -> None:
    card = await _get_card_or_404(card_id, db)
    await _get_deck_or_404(card.deck_id, user.user_id, db)
    await db.delete(card)
    await db.commit()
