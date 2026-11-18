"""Rate limiting per user and endpoint (Issue #25)."""

import builtins
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.auth import get_token_verifier
from app.config import Settings, get_settings
from app.main import create_app
from app.ratelimit import RateLimiter, get_rate_limiter
from app.repository import get_repository


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_up_to_limit_then_blocks() -> None:
    clock = Clock()
    limiter = RateLimiter(3, clock=clock)
    assert [limiter.hit("k") for _ in range(3)] == [None, None, None]
    assert limiter.hit("k") == pytest.approx(60.0)


def test_window_slides() -> None:
    clock = Clock()
    limiter = RateLimiter(2, clock=clock)
    limiter.hit("k")
    clock.now += 30
    limiter.hit("k")
    assert limiter.hit("k") is not None
    clock.now += 30.1  # the first hit is now older than 60s
    assert limiter.hit("k") is None


def test_keys_are_independent() -> None:
    limiter = RateLimiter(1, clock=Clock())
    assert limiter.hit("a") is None
    assert limiter.hit("b") is None
    assert limiter.hit("a") is not None


class EmptyRepo:
    def list(self, month: str | None) -> list[Any]:
        return []

    def monthly_summary(self) -> builtins.list[Any]:
        return []


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings("demo-test", "plutus_lite", frozenset({"a@example.com", "b@example.com"}), (), None, 2)
    users = {
        "a": {"uid": "uid-a", "email": "a@example.com", "email_verified": True},
        "b": {"uid": "uid-b", "email": "b@example.com", "email_verified": True},
    }
    limiter = RateLimiter(2)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_token_verifier] = lambda: users.__getitem__
    app.dependency_overrides[get_repository] = lambda: EmptyRepo()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    with TestClient(app) as c:
        yield c


def h(user: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user}"}


def test_429_after_limit_with_retry_after(client: TestClient) -> None:
    assert client.get("/api/transactions", headers=h("a")).status_code == 200
    assert client.get("/api/transactions", headers=h("a")).status_code == 200
    r = client.get("/api/transactions", headers=h("a"))
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


def test_retry_after_is_at_least_one_second(client: TestClient) -> None:
    """Retry-After must never be 0, even when less than a second is left in the window."""
    clock = Clock()
    limiter = RateLimiter(1, clock=clock)
    client.app.dependency_overrides[get_rate_limiter] = lambda: limiter  # type: ignore[attr-defined]
    assert client.get("/api/transactions", headers=h("a")).status_code == 200
    clock.now += 59.6  # 0.4 seconds left
    r = client.get("/api/transactions", headers=h("a"))
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "1"


def test_limit_is_per_user_and_per_endpoint(client: TestClient) -> None:
    for _ in range(2):
        client.get("/api/transactions", headers=h("a"))
    assert client.get("/api/transactions", headers=h("a")).status_code == 429
    assert client.get("/api/transactions", headers=h("b")).status_code == 200
    assert client.get("/api/summary/monthly", headers=h("a")).status_code == 200


def test_query_string_does_not_create_a_new_bucket(client: TestClient) -> None:
    client.get("/api/transactions?month=2026-10", headers=h("a"))
    client.get("/api/transactions?month=2026-11", headers=h("a"))
    assert client.get("/api/transactions?month=2026-12", headers=h("a")).status_code == 429


def test_healthz_is_not_limited(client: TestClient) -> None:
    assert all(client.get("/healthz").status_code == 200 for _ in range(5))
