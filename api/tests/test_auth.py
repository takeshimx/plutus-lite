"""Unit tests for token handling and the allow list (A1). The token verifier is replaced with a fake."""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.auth import get_token_verifier
from app.config import Settings, get_settings
from app.main import create_app
from app.repository import get_repository

TOKENS: dict[str, dict[str, Any]] = {
    "allowed": {"uid": "uid-a", "email": "A@Example.com", "email_verified": True},
    "not-allowed": {"uid": "uid-c", "email": "c@example.com", "email_verified": True},
    "unverified": {"uid": "uid-u", "email": "a@example.com", "email_verified": False},
    "no-uid": {"email": "a@example.com", "email_verified": True},
}


def fake_verify(token: str) -> dict[str, Any]:
    if token not in TOKENS:
        raise ValueError("invalid token")
    return TOKENS[token]


class EmptyRepo:
    def list(self, month: str | None) -> list[Any]:
        return []


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        project_id="demo-test",
        dataset="plutus_lite",
        allowed_emails=frozenset({"a@example.com"}),
        cors_origins=(),
        bigquery_emulator_host=None,
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_token_verifier] = lambda: fake_verify
    app.dependency_overrides[get_repository] = lambda: EmptyRepo()
    with TestClient(app) as c:
        yield c


def h(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("path", ["/healthz", "/health"])
def test_health_needs_no_token(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", ["/api/transactions", "/api/summary/monthly"])
def test_missing_token_is_401(client: TestClient, path: str) -> None:
    r = client.get(path)
    assert r.status_code == 401
    assert r.headers["WWW-Authenticate"] == "Bearer"


def test_invalid_token_is_401(client: TestClient) -> None:
    assert client.get("/api/transactions", headers=h("bogus")).status_code == 401


def test_token_without_uid_is_401(client: TestClient) -> None:
    assert client.get("/api/transactions", headers=h("no-uid")).status_code == 401


def test_not_allowed_email_is_403(client: TestClient) -> None:
    assert client.get("/api/transactions", headers=h("not-allowed")).status_code == 403


def test_unverified_email_is_403(client: TestClient) -> None:
    """An unverified email must not pass the allow list even if the address matches."""
    assert client.get("/api/transactions", headers=h("unverified")).status_code == 403


def test_allowed_email_passes_auth_case_insensitive(client: TestClient) -> None:
    assert client.get("/api/transactions", headers=h("allowed")).status_code == 200


def test_non_bearer_scheme_is_401(client: TestClient) -> None:
    assert client.get("/api/transactions", headers={"Authorization": "Basic allowed"}).status_code == 401
