"""Shared fixtures for the evaluation gate.

The suite is black-box: it only talks to the API over HTTP. The target and the
test accounts come from environment variables:

    EVAL_BASE_URL            e.g. http://localhost:8080
    EVAL_TOKEN_USER_A        valid token, allowed account
    EVAL_TOKEN_USER_B        valid token, allowed account, different UID
    EVAL_TOKEN_NOT_ALLOWED   valid token, account not on the allow list

Each test is tagged with a feature (pytest marker). Tests for features that are
not listed in gate.json are skipped. If any feature is enabled but the API is
not configured, the run fails instead of passing silently.
"""

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest

HERE = Path(__file__).parent
FEATURES = {
    "auth": "A1: 401/403 handling",
    "crud": "A2/A5: create, update, delete, input validation",
    "isolation": "A3: users cannot see or change each other's data",
    "list": "A2: list filtered by month, ordered by date",
    "summary": "A4: monthly summary matches the golden set and the list",
}


def load_json(name: str) -> Any:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


ENABLED: set[str] = set(load_json("gate.json")["enabled_features"])
unknown = ENABLED - FEATURES.keys()
if unknown:
    raise RuntimeError(f"gate.json has unknown features: {sorted(unknown)}")


def pytest_configure(config: pytest.Config) -> None:
    for name, desc in FEATURES.items():
        config.addinivalue_line("markers", f"{name}: {desc}")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        features = {m.name for m in item.iter_markers() if m.name in FEATURES}
        if features and not features <= ENABLED:
            item.add_marker(pytest.mark.skip(reason=f"feature not enabled in gate.json: {sorted(features - ENABLED)}"))


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} is not set, but gate.json enables features that need the API")
    return value


@pytest.fixture(scope="session")
def api() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=require_env("EVAL_BASE_URL"), timeout=30) as client:
        yield client


@pytest.fixture(scope="session")
def tokens() -> dict[str, str]:
    return {
        "user_a": require_env("EVAL_TOKEN_USER_A"),
        "user_b": require_env("EVAL_TOKEN_USER_B"),
        "not_allowed": require_env("EVAL_TOKEN_NOT_ALLOWED"),
    }


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def dataset() -> dict[str, Any]:
    return load_json("golden/dataset.json")


@pytest.fixture(scope="session")
def expected() -> dict[str, Any]:
    return load_json("golden/expected.json")


@pytest.fixture(scope="module")
def seeded(api: httpx.Client, tokens: dict[str, str], dataset: dict[str, Any]) -> Iterator[dict[str, str]]:
    """Load the golden set through the API. Yields {key: transaction_id}. Deletes it afterwards."""
    ids: dict[str, tuple[str, str]] = {}
    try:
        for user, rows in dataset["users"].items():
            for row in rows:
                body = {k: v for k, v in row.items() if k != "key"}
                r = api.post("/api/transactions", json=body, headers=auth(tokens[user]))
                assert r.status_code == 201, f"seeding {row['key']} failed: {r.status_code} {r.text}"
                ids[row["key"]] = (user, r.json()["transaction_id"])
        yield {key: tid for key, (_, tid) in ids.items()}
    finally:
        for user, tid in ids.values():
            api.delete(f"/api/transactions/{tid}", headers=auth(tokens[user]))
