#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -d .venv ]; then
  echo "Создаю виртуальное окружение .venv ..."
  python3 -m venv .venv
fi

export NVM_DIR="$HOME/.nvm"
# shellcheck source=/dev/null
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 22 >/dev/null 2>&1 || true

# Только pip из venv — не используйте системный pip install
.venv/bin/pip install -e . -q

# Frontend build
if [ -d web/node_modules ]; then
  (cd web && npm run build)
fi

PORT="${PORT:-8000}"

free_port() {
  local pids
  pids="$(lsof -ti :"$PORT" 2>/dev/null || true)"
  if [ -z "$pids" ]; then
    return 0
  fi
  echo "Порт $PORT занят — останавливаю процесс(ы): $pids"
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  for _ in 1 2 3 4 5; do
    sleep 1
    pids="$(lsof -ti :"$PORT" 2>/dev/null || true)"
    [ -z "$pids" ] && return 0
  done
  echo "Принудительная остановка: $pids"
  # shellcheck disable=SC2086
  kill -9 $pids 2>/dev/null || true
  sleep 1
}

free_port

if lsof -ti :"$PORT" >/dev/null 2>&1; then
  echo "Ошибка: порт $PORT всё ещё занят. Завершите процесс вручную:"
  echo "  lsof -ti :$PORT | xargs kill -9"
  exit 1
fi

echo "Запуск на http://localhost:$PORT"
PORT="$PORT" .venv/bin/icae-web
