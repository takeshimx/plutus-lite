"""Create test accounts in the Firebase Auth emulator and print EVAL_* tokens.

Only talks to the emulator (FIREBASE_AUTH_EMULATOR_HOST). Never use against real Firebase.
Output: lines of KEY=VALUE for the evaluation suite.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

HOST = os.environ.get("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
PROJECT = os.environ.get("GCP_PROJECT_ID", "demo-plutus-lite")
BASE = f"http://{HOST}/identitytoolkit.googleapis.com/v1"
PASSWORD = "emulator-only-password"  # noqa: S105  模擬版専用

ACCOUNTS = {
    "EVAL_TOKEN_USER_A": "user-a@example.com",
    "EVAL_TOKEN_USER_B": "user-b@example.com",
    "EVAL_TOKEN_NOT_ALLOWED": "not-allowed@example.com",
}


def post(url: str, body: dict[str, Any], owner: bool = False) -> dict[str, Any]:
    if not url.startswith("http://127.0.0.1:") and not url.startswith("http://localhost:"):
        sys.exit("refusing to call a non-emulator host")
    headers = {"Content-Type": "application/json"}
    if owner:
        headers["Authorization"] = "Bearer owner"  # 模擬版の管理者用
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")  # noqa: S310
    with urllib.request.urlopen(req) as res:  # noqa: S310
        result: dict[str, Any] = json.load(res)
        return result


def token_for(email: str) -> str:
    try:
        user = post(f"{BASE}/accounts:signUp?key=fake", {"email": email, "password": PASSWORD})
        local_id = user["localId"]
    except urllib.error.HTTPError:
        user = post(f"{BASE}/accounts:signInWithPassword?key=fake", {"email": email, "password": PASSWORD})
        local_id = user["localId"]
    post(f"{BASE}/projects/{PROJECT}/accounts:update", {"localId": local_id, "emailVerified": True}, owner=True)
    signed_in = post(
        f"{BASE}/accounts:signInWithPassword?key=fake",
        {"email": email, "password": PASSWORD, "returnSecureToken": True},
    )
    return str(signed_in["idToken"])


def main() -> None:
    for key, email in ACCOUNTS.items():
        print(f"{key}={token_for(email)}")


if __name__ == "__main__":
    main()
