"""Scheduler service tests — unit-level, no real Redis/deck-svc needed."""
import pytest

from scheduler_svc.fsrs_helper import apply_review, is_due


def test_apply_review_good() -> None:
    state: dict = {}
    new_state = apply_review(state, "good")
    assert "due_at" in new_state
    assert new_state["reps"] == 1
    assert new_state["state"] in ("review", "relearning", "new")


def test_apply_review_again() -> None:
    state: dict = {}
    new_state = apply_review(state, "again")
    assert new_state["lapses"] == 1 or new_state["reps"] == 1


def test_apply_review_invalid_grade() -> None:
    with pytest.raises(ValueError, match="Unknown grade"):
        apply_review({}, "perfect")


def test_is_due_new_card() -> None:
    assert is_due({}) is True


def test_is_due_past() -> None:
    assert is_due({"due_at": "2000-01-01T00:00:00+00:00"}) is True


def test_is_due_future() -> None:
    assert is_due({"due_at": "2099-01-01T00:00:00+00:00"}) is False
