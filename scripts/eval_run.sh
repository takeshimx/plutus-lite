#!/usr/bin/env bash
# 評価ゲートを実行する。gate.json で機能が有効なら、模擬版と API を起動してから実行する。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if python -c "import json,sys; sys.exit(0 if json.load(open('eval/gate.json'))['enabled_features'] else 1)"; then
  trap '"$ROOT/scripts/eval_down.sh"' EXIT
  scripts/eval_up.sh
  set -a; . ./.eval.env; set +a
fi

cd eval && uv run pytest "$@"
