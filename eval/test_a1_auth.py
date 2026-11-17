"""A1: requests without a valid token get 401; allowed-list violations get 403. Cases E01-E03."""

import httpx
import pytest

from conftest import auth

ENDPOINTS = [
    ("GET", "/api/transactions"),
    ("POST", "/api/transactions"),
    ("PUT", "/api/transactions/00000000-0000-0000-0000-000000000000"),
    ("DELETE", "/api/transactions/00000000-0000-0000-0000-000000000000"),
    ("GET", "/api/summary/monthly"),
]
VALID_BODY = {"date": "2026-11-01", "type": "expense", "amount_jpy": 100, "category": "食費"}

pytestmark = pytest.mark.auth


def call(api: httpx.Client, method: str, path: str, headers: dict[str, str]) -> httpx.Response:
    body = VALID_BODY if method in ("POST", "PUT") else None
    return api.request(method, path, json=body, headers=headers)


@pytest.mark.parametrize(("method", "path"), ENDPOINTS)
def test_e01_no_token_is_401(api: httpx.Client, method: str, path: str) -> None:
    assert call(api, method, path, {}).status_code == 401


@pytest.mark.parametrize(("method", "path"), ENDPOINTS)
def test_e02_invalid_token_is_401(api: httpx.Client, method: str, path: str) -> None:
    assert call(api, method, path, auth("not-a-real-token")).status_code == 401


@pytest.mark.parametrize(("method", "path"), ENDPOINTS)
def test_e03_not_allowed_account_is_403(api: httpx.Client, tokens: dict[str, str], method: str, path: str) -> None:
    assert call(api, method, path, auth(tokens["not_allowed"])).status_code == 403


def test_healthz_needs_no_token(api: httpx.Client) -> None:
    assert api.get("/healthz").status_code == 200
