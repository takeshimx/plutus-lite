"""Firebase ID トークンの検証と許可リストの判定(A1、ADR-002)。

- トークンが無い、または無効: 401
- トークンは有効だが、メールが許可リストに無い、または未確認: 403
- user_id(uid)は検証済みトークンからだけ取り出す。リクエストの他の部分からは受け取らない
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import firebase_admin
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

TokenVerifier = Callable[[str], dict[str, Any]]

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    uid: str
    email: str


@lru_cache
def _firebase_app(project_id: str) -> firebase_admin.App:
    # FIREBASE_AUTH_EMULATOR_HOST が設定されていれば、firebase_admin は模擬版のトークンを検証する
    return firebase_admin.initialize_app(options={"projectId": project_id}, name="plutus-lite")


def get_token_verifier(settings: Settings = Depends(get_settings)) -> TokenVerifier:
    app = _firebase_app(settings.project_id)

    def verify(token: str) -> dict[str, Any]:
        claims: dict[str, Any] = firebase_auth.verify_id_token(token, app=app)
        return claims

    return verify


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    verify: TokenVerifier = Depends(get_token_verifier),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if credentials is None:
        raise _unauthorized()
    try:
        claims = verify(credentials.credentials)
    except Exception:
        # 理由はログにだけ残し、応答には出さない。トークン自体は記録しない
        logger.info("token verification failed")
        raise _unauthorized() from None

    uid = claims.get("uid") or claims.get("sub")
    email = str(claims.get("email") or "").lower()
    if not uid:
        raise _unauthorized()
    request.state.uid = uid

    if not claims.get("email_verified") or email not in settings.allowed_emails:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not allowed")

    return CurrentUser(uid=str(uid), email=email)
