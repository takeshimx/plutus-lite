"""A3: one user can never read or change another user's data. Cases E07-E08."""

import httpx
import pytest

from conftest import auth

pytestmark = pytest.mark.isolation

A_KEYS = [f"a{i:02d}" for i in range(1, 11)]
B_KEYS = ["b01", "b02"]


def unchanged(api: httpx.Client, tokens: dict[str, str], tid: str) -> None:
    rows = {t["transaction_id"]: t for t in api.get("/api/transactions", headers=auth(tokens["user_a"])).json()}
    assert rows[tid]["amount_jpy"] == 5000
    assert rows[tid]["category"] == "食費"


def test_e07_delete_other_users_transaction_is_404(
    api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str]
) -> None:
    target = seeded["a04"]
    assert api.delete(f"/api/transactions/{target}", headers=auth(tokens["user_b"])).status_code == 404
    unchanged(api, tokens, target)


@pytest.mark.edit
def test_e07_edit_other_users_transaction_is_404(
    api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str]
) -> None:
    target = seeded["a04"]
    body = {"date": "2026-11-10", "type": "expense", "amount_jpy": 1, "category": "hacked"}
    assert api.put(f"/api/transactions/{target}", json=body, headers=auth(tokens["user_b"])).status_code == 404
    unchanged(api, tokens, target)


def test_e08_list_excludes_other_user(api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str]) -> None:
    listed = {t["transaction_id"] for t in api.get("/api/transactions", headers=auth(tokens["user_a"])).json()}
    assert {seeded[k] for k in A_KEYS} <= listed
    assert not {seeded[k] for k in B_KEYS} & listed


@pytest.mark.summary
def test_e08_summary_excludes_other_user(api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str]) -> None:
    summary = api.get("/api/summary/monthly", headers=auth(tokens["user_a"])).json()
    nov = next(m for m in summary if m["month"] == "2026-11")
    assert nov["income_total"] == 295000  # would be 795000 if user_b leaked in
