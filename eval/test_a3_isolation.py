"""A3: one user can never read or change another user's data. Cases E07-E08."""

import httpx
import pytest

from conftest import auth

pytestmark = pytest.mark.isolation

A_KEYS = [f"a{i:02d}" for i in range(1, 11)]
B_KEYS = ["b01", "b02"]


def test_e07_other_users_transaction_is_404(api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str]) -> None:
    user_b = auth(tokens["user_b"])
    target = seeded["a04"]
    body = {"date": "2026-11-10", "type": "expense", "amount_jpy": 1, "category": "hacked"}
    assert api.put(f"/api/transactions/{target}", json=body, headers=user_b).status_code == 404
    assert api.delete(f"/api/transactions/{target}", headers=user_b).status_code == 404

    rows = {t["transaction_id"]: t for t in api.get("/api/transactions", headers=auth(tokens["user_a"])).json()}
    assert rows[target]["amount_jpy"] == 5000
    assert rows[target]["category"] == "食費"


def test_e08_list_and_summary_exclude_other_user(
    api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str]
) -> None:
    listed = {t["transaction_id"] for t in api.get("/api/transactions", headers=auth(tokens["user_a"])).json()}
    assert {seeded[k] for k in A_KEYS} <= listed
    assert not {seeded[k] for k in B_KEYS} & listed

    summary = api.get("/api/summary/monthly", headers=auth(tokens["user_a"])).json()
    nov = next(m for m in summary if m["month"] == "2026-11")
    assert nov["income_total"] == 295000  # would be 795000 if user_b leaked in
