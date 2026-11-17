"""エンドポイントごとのレート制限(要件定義書 2節の6、Issue #25)。

- ユーザー(UID)とエンドポイント(メソッドとパスの型)の組ごとに、直近60秒の呼び出し回数を数える
- 上限を超えたら 429 と Retry-After を返す
- 回数は各インスタンスのメモリで数える。Cloud Run は最大2インスタンスのため、実際の上限は最大でその2倍になる
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from functools import lru_cache

from fastapi import Depends, HTTPException, Request, status

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings

WINDOW_SECONDS = 60.0


class RateLimiter:
    def __init__(self, limit: int, window: float = WINDOW_SECONDS, clock: Callable[[], float] = time.monotonic) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        self._limit = limit
        self._window = window
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str) -> float | None:
        """呼び出しを1回数える。許可なら None、上限超えなら再試行までの秒数を返す。"""
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                return hits[0] + self._window - now
            hits.append(now)
            return None


@lru_cache
def _limiter(limit: int) -> RateLimiter:
    return RateLimiter(limit)


def get_rate_limiter(settings: Settings = Depends(get_settings)) -> RateLimiter:
    return _limiter(settings.rate_limit_per_minute)


def rate_limit(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)  # /api/transactions/{transaction_id} を1つとして数える
    retry_after = limiter.hit(f"{user.uid}:{request.method}:{path}")
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests",
            headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
        )
