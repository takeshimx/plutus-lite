"""Input validation rules (A5 and G5 decisions in eval/README.md)."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas import MAX_ABS_AMOUNT, TransactionInput

BASE: dict[str, Any] = {"date": "2026-11-03", "type": "expense", "amount_jpy": 1500, "category": "食費"}


@pytest.mark.parametrize("amount", [1, -1, -1000, MAX_ABS_AMOUNT, -MAX_ABS_AMOUNT])
def test_accepted_amounts(amount: int) -> None:
    assert TransactionInput(**{**BASE, "amount_jpy": amount}).amount_jpy == amount


@pytest.mark.parametrize(
    "changes",
    [
        {"amount_jpy": 0},
        {"amount_jpy": 1.5},
        {"amount_jpy": 1.0},
        {"amount_jpy": "100"},
        {"amount_jpy": True},
        {"amount_jpy": MAX_ABS_AMOUNT + 1},
        {"amount_jpy": -MAX_ABS_AMOUNT - 1},
        {"type": "refund"},
        {"date": "2026-02-30"},
        {"date": "2026-13-01"},
        {"date": ""},
        {"date": 1700000000},
        {"date": "2026-11-03T00:00:00"},
        {"category": ""},
        {"category": "   "},
        {"category": 123},
        {"note": "x" * 201},
        {"user_id": "someone-else"},
    ],
)
def test_rejected_inputs(changes: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        TransactionInput(**{**BASE, **changes})


@pytest.mark.parametrize("missing", ["date", "type", "amount_jpy", "category"])
def test_required_fields(missing: str) -> None:
    with pytest.raises(ValidationError):
        TransactionInput(**{k: v for k, v in BASE.items() if k != missing})


def test_note_is_optional_and_up_to_200() -> None:
    assert TransactionInput(**BASE).note is None
    assert TransactionInput(**{**BASE, "note": "x" * 200}).note == "x" * 200


def test_category_is_trimmed() -> None:
    assert TransactionInput(**{**BASE, "category": " 食費 "}).category == "食費"
