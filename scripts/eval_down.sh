#!/usr/bin/env bash
# scripts/eval_up.sh で起動したものを止める
cd "$(dirname "$0")/.."
for f in .eval-logs/*.pid; do
  [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null
done
pkill -f "firebase-tools.*emulators:start" 2>/dev/null
pkill -f "uvicorn app.main:app" 2>/dev/null
# Windows(Git Bash)では上の kill が効かないことがあるため、ポートで探して止める
if command -v powershell.exe >/dev/null 2>&1; then
  powershell.exe -NoProfile -Command "foreach (\$p in 8080,9099,4400,4500) { Get-NetTCPConnection -LocalPort \$p -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id \$_.OwningProcess -Force -ErrorAction SilentlyContinue } }" >/dev/null 2>&1
fi
docker rm -f plutus-bq >/dev/null 2>&1
rm -f .eval.env
true
