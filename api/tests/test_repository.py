"""Every query is scoped to the current user (A3) and uses parameters, never string-built values."""

from typing import Any

import pytest

from app.repository import TransactionRepository
from app.schemas import TransactionInput


class FakeRow:
    n = 1


class FakeJob:
    def __init__(self, sql: str) -> None:
        self._sql = sql

    def result(self) -> list[Any]:
        return [FakeRow()] if "COUNT(*)" in self._sql else []


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def query(self, sql: str, job_config: Any) -> FakeJob:
        params = {p.name: p.value for p in job_config.query_parameters}
        self.calls.append((sql, params))
        return FakeJob(sql)


@pytest.fixture
def client() -> FakeClient:
    return FakeClient()


@pytest.fixture
def repo(client: FakeClient) -> TransactionRepository:
    return TransactionRepository(client, "p.d.transactions", "uid-a")  # type: ignore[arg-type]


def test_every_operation_passes_the_current_uid(repo: TransactionRepository, client: FakeClient) -> None:
    repo.list(None)
    repo.list("2026-11")
    repo.create(TransactionInput(date="2026-11-03", type="expense", amount_jpy=100, category="食費"))  # type: ignore[arg-type]
    repo.delete("tx-1")
    assert len(client.calls) == 5  # list x2, insert, ownership check, delete
    for sql, params in client.calls:
        assert params["user_id"] == "uid-a"
        assert "@user_id" in sql


def test_reads_and_deletes_filter_by_user(repo: TransactionRepository, client: FakeClient) -> None:
    repo.list("2026-11")
    repo.delete("tx-1")
    for sql, _ in client.calls:
        assert "WHERE user_id = @user_id" in sql


def test_values_are_parameters_not_sql_text(repo: TransactionRepository, client: FakeClient) -> None:
    hostile = "x'; DELETE FROM t WHERE '1'='1"
    repo.create(TransactionInput(date="2026-11-03", type="expense", amount_jpy=100, category=hostile))  # type: ignore[arg-type]
    repo.delete(hostile)
    for sql, _ in client.calls:
        assert hostile not in sql
    assert hostile in client.calls[0][1].values()


def test_month_filter_is_a_date_range(repo: TransactionRepository, client: FakeClient) -> None:
    repo.list("2026-12")
    _, params = client.calls[0]
    assert str(params["month_start"]) == "2026-12-01"
    assert str(params["month_end"]) == "2027-01-01"


def test_unscoped_sql_is_refused(repo: TransactionRepository) -> None:
    with pytest.raises(RuntimeError):
        repo._run("SELECT * FROM `p.d.transactions`")
    with pytest.raises(RuntimeError):
        repo._run("INSERT INTO `p.d.transactions` (user_id) VALUES ('someone')")


def test_empty_uid_is_refused(client: FakeClient) -> None:
    with pytest.raises(ValueError):
        TransactionRepository(client, "p.d.transactions", "")  # type: ignore[arg-type]


def test_delete_checks_ownership_first(client: FakeClient) -> None:
    class NotOwned(FakeClient):
        def query(self, sql: str, job_config: Any) -> FakeJob:
            super().query(sql, job_config)
            job = FakeJob(sql)
            job.result = lambda: []  # type: ignore[method-assign]
            return job

    other = NotOwned()
    repo = TransactionRepository(other, "p.d.transactions", "uid-b")  # type: ignore[arg-type]
    assert repo.delete("tx-of-user-a") is False
    assert not any(sql.startswith("DELETE") for sql, _ in other.calls)
