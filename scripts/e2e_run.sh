#!/usr/bin/env bash
# E2E テスト(P8、Issue #31)を実行する。CI と手元の両方で使う。
# 評価ゲートと同じ scripts/eval_up.sh で模擬版と API を起動し、Playwright が画面を本番用ビルドで起動して操作する。
# 引数は Playwright にそのまま渡す(例: scripts/e2e_run.sh -g A2)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

trap '"$ROOT/scripts/eval_down.sh"' EXIT
# 画面(127.0.0.1:3000)から API を呼べるようにする
export CORS_ORIGINS="http://127.0.0.1:3000"
scripts/eval_up.sh
set -a; . ./.eval.env; set +a

cd frontend && npx playwright test "$@"
