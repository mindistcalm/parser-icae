#!/usr/bin/env bash
# Универсальный запуск: Linux, macOS, Git Bash (Windows)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PORT="${PORT:-8000}"
SKIP_BUILD="${SKIP_BUILD:-0}"

log() { echo "==> $*"; }

find_python() {
  for cmd in python3 python py; do
    if command -v "$cmd" >/dev/null 2>&1; then
      if [ "$cmd" = "py" ]; then
        py -3 -c "import sys" >/dev/null 2>&1 && { echo "py -3"; return 0; }
      else
        "$cmd" -c "import sys" >/dev/null 2>&1 && { echo "$cmd"; return 0; }
      fi
    fi
  done
  echo "Python 3 не найден. Установите Python 3.10+ с https://python.org" >&2
  exit 1
}

PYTHON="$(find_python)"
log "Python: $PYTHON"

if [ ! -d .venv ]; then
  log "Создаю виртуальное окружение .venv"
  if [ "$PYTHON" = "py -3" ]; then
    py -3 -m venv .venv
  else
    $PYTHON -m venv .venv
  fi
fi

# Windows Git Bash: Scripts/, Unix: bin/
if [ -f .venv/Scripts/pip.exe ]; then
  PIP=".venv/Scripts/pip.exe"
  ICAE_WEB=".venv/Scripts/icae-web.exe"
  PYTHON_VENV=".venv/Scripts/python.exe"
else
  PIP=".venv/bin/pip"
  ICAE_WEB=".venv/bin/icae-web"
  PYTHON_VENV=".venv/bin/python"
fi

log "Устанавливаю зависимости Python"
"$PIP" install -e . -q

setup_node() {
  if [ -n "${NVM_DIR:-}" ] && [ -s "$NVM_DIR/nvm.sh" ]; then
    # shellcheck source=/dev/null
    . "$NVM_DIR/nvm.sh"
    nvm use 22 >/dev/null 2>&1 || nvm use --lts >/dev/null 2>&1 || true
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "Предупреждение: npm не найден — пропускаю сборку фронтенда." >&2
    echo "Установите Node.js 18+ с https://nodejs.org" >&2
    return 1
  fi

  log "Node: $(node -v), npm: $(npm -v)"
  (
    cd web
    if [ ! -d node_modules ]; then
      log "npm install (первый запуск)"
      if [ -f package-lock.json ]; then npm ci; else npm install; fi
    fi
    log "Сборка фронтенда"
    npm run build
  )
}

if [ "$SKIP_BUILD" != "1" ]; then
  setup_node || true
fi

free_port() {
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti :"$PORT" 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "$PORT/tcp" >/dev/null 2>&1 || true
    sleep 1
    return 0
  fi

  if [ -n "$pids" ]; then
    log "Порт $PORT занят — останавливаю: $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 2
    pids="$(lsof -ti :"$PORT" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
      sleep 1
    fi
  fi
}

free_port

log "Запуск на http://localhost:$PORT"
log "Остановка: Ctrl+C"

export PORT
if [ -x "$ICAE_WEB" ]; then
  exec "$ICAE_WEB"
else
  exec "$PYTHON_VENV" -m parser.api.server
fi
