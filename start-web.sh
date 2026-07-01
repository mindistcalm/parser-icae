#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

export NVM_DIR="$HOME/.nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 22 >/dev/null 2>&1 || true

# Backend deps
.venv/bin/pip install -e . -q

# Frontend build
if [ -d web/node_modules ]; then
  (cd web && npm run build)
fi

PORT="${PORT:-8000}"
OLD_PID="$(lsof -ti :"$PORT" 2>/dev/null || true)"
if [ -n "$OLD_PID" ]; then
  echo "Порт $PORT занят (PID $OLD_PID) — останавливаю предыдущий сервер..."
  kill $OLD_PID 2>/dev/null || true
  sleep 1
fi

echo "Запуск на http://localhost:$PORT"
PORT="$PORT" .venv/bin/icae-web
