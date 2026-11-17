"""BigQuery の取引表へのアクセス。user_id の条件を付けるのは、このファイルだけ(A3、AGENTS.md 決まり2)。

- リポジトリは、検証済みトークンの UID を受け取って作る。呼び出し側は UID を渡し直せない
- すべての SQL は _run() を通す。_run() は @user_id を必ずパラメータに入れ、SQL に条件が無ければ止まる
- 値はすべてクエリパラメータで渡す。文字列の連結で SQL に値を埋め込まない(決まり8)
- 一覧とサマリーは、同じ絞り込み _scope() を使う(A4、ADR-003)
- 登録は DML の INSERT で行う。ストリーミング挿入は、直後に UPDATE / DELETE できないため使わない
"""

import builtins
import uuid
from datetime import UTC, date, datetime
from functools import lru_cache
from typing import Any

from fastapi import Depends
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud import bigquery

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.schemas import CategoryTotal, MonthlySummary, Transaction, TransactionInput

_COLUMNS = "transaction_id, date, type, amount_jpy, category, note, created_at"
_USER_CONDITION = "user_id = @user_id"


@lru_cache
def _client(project_id: str, emulator_host: str | None) -> bigquery.Client:
    if emulator_host:
        return bigquery.Client(
            project=project_id,
            client_options=ClientOptions(api_endpoint=emulator_host),
            credentials=AnonymousCredentials(),  # type: ignore[no-untyped-call]
        )
    return bigquery.Client(project=project_id)


def _month_range(month: str) -> tuple[date, date]:
    year, mon = (int(x) for x in month.split("-"))
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end


class TransactionRepository:
    def __init__(self, client: bigquery.Client, table: str, uid: str) -> None:
        if not uid:
            raise ValueError("uid is required")
        self._client = client
        self._table = table
        self._uid = uid

    def _run(self, sql: str, params: list[Any] | None = None) -> bigquery.QueryJob:
        # 読み取り・更新・削除は user_id の条件が必須。登録は user_id に @user_id を入れることが必須
        is_insert = sql.lstrip().upper().startswith("INSERT")
        if (is_insert and "VALUES (@user_id," not in sql) or (not is_insert and _USER_CONDITION not in sql):
            raise RuntimeError("every query must be scoped to the current user_id")
        query_params = [bigquery.ScalarQueryParameter("user_id", "STRING", self._uid), *(params or [])]
        job = self._client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=query_params))
        job.result()
        return job

    def _scope(self, month: str | None) -> tuple[str, list[Any]]:
        """一覧とサマリーで共有する絞り込み。必ず user_id で絞り、月の指定があれば日付の範囲で絞る。"""
        if month is None:
            return _USER_CONDITION, []
        start, end = _month_range(month)
        return (
            f"{_USER_CONDITION} AND date >= @month_start AND date < @month_end",
            [
                bigquery.ScalarQueryParameter("month_start", "DATE", start),
                bigquery.ScalarQueryParameter("month_end", "DATE", end),
            ],
        )

    def list(self, month: str | None) -> list[Transaction]:
        where, params = self._scope(month)
        sql = f"SELECT {_COLUMNS} FROM `{self._table}` WHERE {where} ORDER BY date DESC, created_at DESC"  # noqa: S608
        rows = self._run(sql, params).result()
        return [Transaction(**dict(row.items())) for row in rows]

    def monthly_summary(self) -> builtins.list[MonthlySummary]:
        """月ごとの収入合計、支出合計、支出のカテゴリ別内訳。合計はすべて SQL で計算する(A6、ADR-003)。

        一覧と同じ _scope() で絞るため、同じ月の一覧の合計と必ず一致する(A4)。
        金額は符号のまま足す。支出のマイナスは返金、収入のマイナスは訂正として差し引かれる。
        """
        where, params = self._scope(None)
        totals_sql = (
            "SELECT FORMAT_DATE('%Y-%m', date) AS month, "  # noqa: S608  値はすべてパラメータ
            "SUM(IF(type = 'income', amount_jpy, 0)) AS income_total, "
            "SUM(IF(type = 'expense', amount_jpy, 0)) AS expense_total "
            f"FROM `{self._table}` WHERE {where} GROUP BY month ORDER BY month DESC"
        )
        categories_sql = (
            "SELECT FORMAT_DATE('%Y-%m', date) AS month, category, SUM(amount_jpy) AS total "  # noqa: S608
            f"FROM `{self._table}` WHERE {where} AND type = 'expense' "
            "GROUP BY month, category ORDER BY month DESC, total DESC, category"
        )
        by_month: dict[str, builtins.list[CategoryTotal]] = {}
        for row in self._run(categories_sql, params).result():
            by_month.setdefault(row.month, []).append(CategoryTotal(category=row.category, total=row.total))
        return [
            MonthlySummary(
                month=row.month,
                income_total=row.income_total,
                expense_total=row.expense_total,
                expense_by_category=by_month.get(row.month, []),
            )
            for row in self._run(totals_sql, params).result()
        ]

    def create(self, data: TransactionInput) -> Transaction:
        created = Transaction(
            transaction_id=str(uuid.uuid4()),
            created_at=datetime.now(UTC).replace(microsecond=0),
            **data.model_dump(),
        )
        sql = (
            f"INSERT INTO `{self._table}` (user_id, {_COLUMNS}) "  # noqa: S608
            "VALUES (@user_id, @transaction_id, @date, @type, @amount_jpy, @category, @note, @created_at)"
        )
        self._run(
            sql,
            [
                bigquery.ScalarQueryParameter("transaction_id", "STRING", created.transaction_id),
                bigquery.ScalarQueryParameter("date", "DATE", created.date),
                bigquery.ScalarQueryParameter("type", "STRING", created.type),
                bigquery.ScalarQueryParameter("amount_jpy", "INT64", created.amount_jpy),
                bigquery.ScalarQueryParameter("category", "STRING", created.category),
                bigquery.ScalarQueryParameter("note", "STRING", created.note),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", created.created_at),
            ],
        )
        return created

    def get(self, transaction_id: str) -> Transaction | None:
        """自分の取引を1件取得する。無い(他人の取引を含む)ときは None。"""
        sql = (
            f"SELECT {_COLUMNS} FROM `{self._table}` "  # noqa: S608
            f"WHERE {_USER_CONDITION} AND transaction_id = @transaction_id"
        )
        rows = list(
            self._run(sql, [bigquery.ScalarQueryParameter("transaction_id", "STRING", transaction_id)]).result()
        )
        return Transaction(**dict(rows[0].items())) if rows else None

    def update(self, transaction_id: str, data: TransactionInput) -> Transaction | None:
        """自分の取引だけを更新する。DML の影響件数は模擬版では返らないため、先に存在を確かめる。"""
        current = self.get(transaction_id)
        if current is None:
            return None
        sql = (
            f"UPDATE `{self._table}` "  # noqa: S608
            "SET date = @date, type = @type, amount_jpy = @amount_jpy, category = @category, note = @note "
            f"WHERE {_USER_CONDITION} AND transaction_id = @transaction_id"
        )
        self._run(
            sql,
            [
                bigquery.ScalarQueryParameter("transaction_id", "STRING", transaction_id),
                bigquery.ScalarQueryParameter("date", "DATE", data.date),
                bigquery.ScalarQueryParameter("type", "STRING", data.type),
                bigquery.ScalarQueryParameter("amount_jpy", "INT64", data.amount_jpy),
                bigquery.ScalarQueryParameter("category", "STRING", data.category),
                bigquery.ScalarQueryParameter("note", "STRING", data.note),
            ],
        )
        return current.model_copy(update=data.model_dump())

    def delete(self, transaction_id: str) -> bool:
        """自分の取引だけを削除する。対象が無い(他人の取引を含む)ときは False。"""
        if self.get(transaction_id) is None:
            return False
        sql = f"DELETE FROM `{self._table}` WHERE {_USER_CONDITION} AND transaction_id = @transaction_id"  # noqa: S608
        self._run(sql, [bigquery.ScalarQueryParameter("transaction_id", "STRING", transaction_id)])
        return True


def get_repository(
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> TransactionRepository:
    client = _client(settings.project_id, settings.bigquery_emulator_host)
    table = f"{settings.project_id}.{settings.dataset}.transactions"
    return TransactionRepository(client, table, user.uid)
