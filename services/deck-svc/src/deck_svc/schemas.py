import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DeckCreate(BaseModel):
    name: str


class DeckUpdate(BaseModel):
    name: str | None = None


class DeckResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CardCreate(BaseModel):
    front: str
    back: str


class CardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None
    fsrs_state: dict[str, Any] | None = None


class CardResponse(BaseModel):
    id: uuid.UUID
    deck_id: uuid.UUID
    front: str
    back: str
    fsrs_state: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
