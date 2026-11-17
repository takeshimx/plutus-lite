"""A2 list and A4 summary against the golden set. Cases E09-E11.

These tests assume the test account starts with no transactions; the golden
set is the only data for user_a and user_b during the run.
"""

from typing import Any

import httpx
import pytest

from conftest import auth


@pytest.mark.list
def test_e09_list_by_month_is_filtered_and_ordered(
    api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str], expected: dict[str, Any]
) -> None:
    for month, want in expected["user_a"]["list_by_month"].items():
        r = api.get("/api/transactions", params={"month": month}, headers=auth(tokens["user_a"]))
        assert r.status_code == 200
        got = [t["transaction_id"] for t in r.json()]
        assert got == [seeded[k] for k in want["keys_in_order"]], month


@pytest.mark.list
def test_list_without_month_returns_all(
    api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str], expected: dict[str, Any]
) -> None:
    r = api.get("/api/transactions", headers=auth(tokens["user_a"]))
    assert len(r.json()) == expected["user_a"]["list_all_count"]


@pytest.mark.summary
@pytest.mark.parametrize("user", ["user_a", "user_b"])
def test_e10_summary_matches_golden_set(
    api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str], expected: dict[str, Any], user: str
) -> None:
    r = api.get("/api/summary/monthly", headers=auth(tokens[user]))
    assert r.status_code == 200
    assert r.json() == expected[user]["monthly_summary"]


@pytest.mark.summary
def test_e11_summary_equals_sum_of_list(api: httpx.Client, tokens: dict[str, str], seeded: dict[str, str]) -> None:
    headers = auth(tokens["user_a"])
    for month in api.get("/api/summary/monthly", headers=headers).json():
        rows = api.get("/api/transactions", params={"month": month["month"]}, headers=headers).json()
        income = sum(t["amount_jpy"] for t in rows if t["type"] == "income")
        expense = sum(t["amount_jpy"] for t in rows if t["type"] == "expense")
        assert (month["income_total"], month["expense_total"]) == (income, expense), month["month"]
        assert sum(c["total"] for c in month["expense_by_category"]) == expense, month["month"]
