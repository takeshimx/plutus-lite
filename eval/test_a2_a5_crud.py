"""A2: create, update, delete. A5: integer yen, negatives allowed, invalid input is 400. Cases E04-E06, E12-E20."""

from collections.abc import Iterator
from typing import Any

import httpx
import pytest

from conftest import auth

pytestmark = pytest.mark.crud

BASE = {"date": "2026-11-03", "type": "expense", "amount_jpy": 1500, "category": "食費", "note": "eval"}
LIMIT = 10_000_000_000


@pytest.fixture
def user_a(tokens: dict[str, str]) -> dict[str, str]:
    return auth(tokens["user_a"])


@pytest.fixture
def created(api: httpx.Client, user_a: dict[str, str]) -> Iterator[list[str]]:
    """Collects ids created by a test and deletes them afterwards."""
    ids: list[str] = []
    yield ids
    for tid in ids:
        api.delete(f"/api/transactions/{tid}", headers=user_a)


def list_all(api: httpx.Client, headers: dict[str, str]) -> list[dict[str, Any]]:
    r = api.get("/api/transactions", headers=headers)
    assert r.status_code == 200
    return r.json()


def create(api: httpx.Client, headers: dict[str, str], ids: list[str], body: dict[str, Any]) -> httpx.Response:
    r = api.post("/api/transactions", json=body, headers=headers)
    if r.status_code == 201:
        ids.append(r.json()["transaction_id"])
    return r


def test_e04_create_appears_in_list(api: httpx.Client, user_a: dict[str, str], created: list[str]) -> None:
    r = create(api, user_a, created, BASE)
    assert r.status_code == 201
    tid = r.json()["transaction_id"]
    rows = {t["transaction_id"]: t for t in list_all(api, user_a)}
    assert tid in rows
    assert {k: rows[tid][k] for k in BASE} == BASE


def test_e05_update_is_reflected(api: httpx.Client, user_a: dict[str, str], created: list[str]) -> None:
    tid = create(api, user_a, created, BASE).json()["transaction_id"]
    r = api.put(f"/api/transactions/{tid}", json={**BASE, "amount_jpy": 2500}, headers=user_a)
    assert r.status_code == 200
    rows = {t["transaction_id"]: t for t in list_all(api, user_a)}
    assert rows[tid]["amount_jpy"] == 2500


def test_e06_delete_removes_from_list(api: httpx.Client, user_a: dict[str, str], created: list[str]) -> None:
    tid = create(api, user_a, created, BASE).json()["transaction_id"]
    assert api.delete(f"/api/transactions/{tid}", headers=user_a).status_code == 204
    assert tid not in {t["transaction_id"] for t in list_all(api, user_a)}


@pytest.mark.parametrize("amount", [-1000, LIMIT, -LIMIT])
def test_e12_e19_accepted_amounts(api: httpx.Client, user_a: dict[str, str], created: list[str], amount: int) -> None:
    assert create(api, user_a, created, {**BASE, "amount_jpy": amount}).status_code == 201


INVALID = {
    "e13_float": {**BASE, "amount_jpy": 1.5},
    "e13_string": {**BASE, "amount_jpy": "100"},
    "e13_missing": {k: v for k, v in BASE.items() if k != "amount_jpy"},
    "e14_type_refund": {**BASE, "type": "refund"},
    "e15_feb_30": {**BASE, "date": "2026-02-30"},
    "e15_month_13": {**BASE, "date": "2026-13-01"},
    "e15_empty": {**BASE, "date": ""},
    "e16_note_201": {**BASE, "note": "x" * 201},
    "e16_no_category": {k: v for k, v in BASE.items() if k != "category"},
    "e18_zero": {**BASE, "amount_jpy": 0},
    "e18_empty_category": {**BASE, "category": ""},
    "e20_over_limit": {**BASE, "amount_jpy": LIMIT + 1},
    "e20_under_limit": {**BASE, "amount_jpy": -LIMIT - 1},
}


@pytest.mark.parametrize("body", INVALID.values(), ids=INVALID.keys())
def test_invalid_input_is_400_and_not_saved(
    api: httpx.Client, user_a: dict[str, str], created: list[str], body: dict[str, Any]
) -> None:
    before = len(list_all(api, user_a))
    assert create(api, user_a, created, body).status_code == 400
    assert len(list_all(api, user_a)) == before


def test_invalid_update_is_400(api: httpx.Client, user_a: dict[str, str], created: list[str]) -> None:
    tid = create(api, user_a, created, BASE).json()["transaction_id"]
    assert api.put(f"/api/transactions/{tid}", json={**BASE, "amount_jpy": 1.5}, headers=user_a).status_code == 400


def test_e17_user_id_in_body_is_ignored(
    api: httpx.Client, tokens: dict[str, str], user_a: dict[str, str], created: list[str]
) -> None:
    r = create(api, user_a, created, {**BASE, "user_id": "someone-else"})
    assert r.status_code in (201, 400)
    if r.status_code == 201:
        tid = r.json()["transaction_id"]
        assert tid in {t["transaction_id"] for t in list_all(api, user_a)}
        assert tid not in {t["transaction_id"] for t in list_all(api, auth(tokens["user_b"]))}
