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

echo "Запуск на http://localhost:8000"
.venv/bin/icae-web
