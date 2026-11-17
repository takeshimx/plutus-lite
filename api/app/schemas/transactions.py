"""取引の入出力の型と検証(A5、eval/README.md の G5 決定)。

- 金額は整数円。小数、文字列、真偽値は受け付けない。0 は拒否。絶対値が 100億円を超えたら拒否
- 日付は YYYY-MM-DD の文字列だけ。存在しない日付は拒否
- user_id は入力に含めない。未知の項目があれば拒否する
"""

import re
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, StrictInt, StringConstraints

MAX_ABS_AMOUNT = 10_000_000_000
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _date_from_string(value: object) -> date:
    # 数値(UNIX 時刻)や日時の文字列を日付として受け付けないよう、形式を固定する
    if not isinstance(value, str) or not _DATE_RE.match(value):
        raise ValueError("date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def _check_amount(value: int) -> int:
    if value == 0:
        raise ValueError("amount_jpy must not be 0")
    if abs(value) > MAX_ABS_AMOUNT:
        raise ValueError(f"amount_jpy must be within ±{MAX_ABS_AMOUNT}")
    return value


IsoDate = Annotated[date, BeforeValidator(_date_from_string)]
AmountJpy = Annotated[StrictInt, AfterValidator(_check_amount)]
Category = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=50)]
Note = Annotated[str, StringConstraints(strict=True, max_length=200)]
Month = Annotated[str, StringConstraints(pattern=_MONTH_RE.pattern)]


class TransactionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: IsoDate
    type: Literal["income", "expense"]
    amount_jpy: AmountJpy
    category: Category
    note: Note | None = None


class Transaction(BaseModel):
    transaction_id: str
    date: date
    type: Literal["income", "expense"]
    amount_jpy: int
    category: str
    note: str | None
    created_at: datetime


class TransactionCreated(Transaction):
    pass
