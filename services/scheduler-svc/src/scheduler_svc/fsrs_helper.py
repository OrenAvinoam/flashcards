"""Thin wrapper around the fsrs package to convert between our dict state and FSRS objects."""
from datetime import UTC, datetime
from typing import Any

from fsrs import Card, FSRS, Rating, State

_scheduler = FSRS()

_GRADE_MAP: dict[str, Rating] = {
    "again": Rating.Again,
    "hard": Rating.Hard,
    "good": Rating.Good,
    "easy": Rating.Easy,
}


def _state_from_dict(state: dict[str, Any]) -> Card:
    card = Card()
    if not state:
        return card

    card.stability = float(state.get("stability", 0.0))
    card.difficulty = float(state.get("difficulty", 0.0))
    card.reps = int(state.get("reps", 0))
    card.lapses = int(state.get("lapses", 0))

    raw_state = state.get("state", "new")
    card.state = State.New if raw_state == "new" else State.Review if raw_state == "review" else State.Relearning

    due_raw = state.get("due_at")
    if due_raw:
        card.due = datetime.fromisoformat(due_raw)
    last_raw = state.get("last_review")
    if last_raw:
        card.last_review = datetime.fromisoformat(last_raw)

    return card


def _state_to_dict(card: Card) -> dict[str, Any]:
    state_name = "new"
    if card.state == State.Review:
        state_name = "review"
    elif card.state == State.Relearning:
        state_name = "relearning"

    return {
        "stability": card.stability,
        "difficulty": card.difficulty,
        "due_at": card.due.isoformat() if card.due else None,
        "last_review": card.last_review.isoformat() if card.last_review else None,
        "reps": card.reps,
        "lapses": card.lapses,
        "state": state_name,
    }


def apply_review(current_state: dict[str, Any], grade: str) -> dict[str, Any]:
    rating = _GRADE_MAP.get(grade)
    if rating is None:
        raise ValueError(f"Unknown grade: {grade}. Must be one of: again, hard, good, easy")

    card = _state_from_dict(current_state)
    now = datetime.now(UTC)
    card, _ = _scheduler.review_card(card, rating, now)
    return _state_to_dict(card)


def is_due(state: dict[str, Any]) -> bool:
    due_raw = state.get("due_at")
    if not due_raw:
        return True  # new card
    due = datetime.fromisoformat(due_raw)
    if due.tzinfo is None:
        due = due.replace(tzinfo=UTC)
    return due <= datetime.now(UTC)
