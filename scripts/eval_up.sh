#!/usr/bin/env bash
# 評価ゲート用に、模擬版(Firebase Auth、BigQuery)と API を起動する。CI と手元の両方で使う。
# 終わると .eval.env に EVAL_* を書き出す。止めるときは scripts/eval_down.sh。
set -euo pipefail
cd "$(dirname "$0")/.."

export GCP_PROJECT_ID=demo-plutus-lite
export BQ_DATASET=plutus_lite
export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
export BIGQUERY_EMULATOR_HOST=http://127.0.0.1:9050
export ALLOWED_EMAILS=user-a@example.com,user-b@example.com
API_PORT=8080
LOGS=.eval-logs
mkdir -p "$LOGS"

BQ_IMAGE="ghcr.io/goccy/bigquery-emulator@sha256:f4e428d265a93dc5ce36c294e1c584c7c9b384117d47ab8ddbb63d8d50b7f393" # v0.8.1
FIREBASE_TOOLS="firebase-tools@15.36.0"

wait_for() { # url, name
  for _ in $(seq 1 60); do
    curl -s -o /dev/null "$1" && return 0
    sleep 1
  done
  echo "$2 did not start"; tail -50 "$LOGS"/*.log || true; exit 1
}

echo "== BigQuery emulator"
docker rm -f plutus-bq >/dev/null 2>&1 || true
# Windows の Git Bash でパスが書き換えられないようにする
HOST_DIR="$(pwd -W 2>/dev/null || pwd)/eval/emulator"
MSYS_NO_PATHCONV=1 docker run -d --name plutus-bq -p 9050:9050 \
  -v "$HOST_DIR:/work:ro" \
  "$BQ_IMAGE" --project=demo-plutus-lite --data-from-yaml=/work/bigquery.yaml >/dev/null
wait_for "http://127.0.0.1:9050/bigquery/v2/projects/demo-plutus-lite/datasets" "BigQuery emulator"

echo "== Firebase Auth emulator"
npx --yes "$FIREBASE_TOOLS" emulators:start --only auth --project demo-plutus-lite >"$LOGS/firebase.log" 2>&1 &
echo $! > "$LOGS/firebase.pid"
wait_for "http://127.0.0.1:9099/" "Firebase Auth emulator"

echo "== API"
(cd api && exec uv run uvicorn app.main:app --host 127.0.0.1 --port $API_PORT >"../$LOGS/api.log" 2>&1) &
echo $! > "$LOGS/api.pid"
wait_for "http://127.0.0.1:$API_PORT/healthz" "API"

echo "== Test accounts"
{
  echo "EVAL_BASE_URL=http://127.0.0.1:$API_PORT"
  (cd eval && uv run python ../scripts/eval_accounts.py)
} > .eval.env
echo "ready: .eval.env"
