#!/usr/bin/env bash
# Установка системных требований: Python 3.10+ и Node.js 18+
set -euo pipefail

log() { echo "==> $*"; }
ok() { echo "  ✓ $*"; }
warn() { echo "  ! $*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

check_python() {
  for cmd in python3 python; do
    if have "$cmd"; then
      ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
      major=${ver%%.*}
      minor=${ver#*.}
      if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
        ok "Python $ver ($cmd)"
        return 0
      fi
      warn "Python $ver найден, нужен 3.10+"
    fi
  done
  return 1
}

check_node() {
  if have node; then
    ver=$(node -v | tr -d v)
    major=${ver%%.*}
    if [ "$major" -ge 18 ]; then
      ok "Node.js $ver"
      return 0
    fi
    warn "Node.js $ver найден, нужен 18+"
  fi
  return 1
}

install_ubuntu_debian() {
  log "Ubuntu/Debian: установка через apt"
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip curl ca-certificates

  if ! check_node 2>/dev/null; then
    log "Установка Node.js 22 через NodeSource"
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt install -y nodejs
  fi
}

install_fedora() {
  log "Fedora: установка через dnf"
  sudo dnf install -y python3 python3-pip nodejs npm
}

install_arch() {
  log "Arch: установка через pacman"
  sudo pacman -Sy --noconfirm python python-pip nodejs npm
}

install_macos() {
  if ! have brew; then
    log "Установка Homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  log "macOS: установка через Homebrew"
  brew install python@3.12 node
  warn "Добавьте в PATH при необходимости: brew link python@3.12"
}

log "Проверка требований ИЦАЭ Parser"
echo ""

need_python=1
need_node=1
check_python && need_python=0 || true
check_node && need_node=0 || true

if [ "$need_python" -eq 0 ] && [ "$need_node" -eq 0 ]; then
  log "Всё установлено. Запуск: ./run.sh"
  exit 0
fi

echo ""
log "Чего-то не хватао — пробую установить..."
echo ""

if [[ "$OSTYPE" == "darwin"* ]]; then
  install_macos
elif [ -f /etc/debian_version ]; then
  install_ubuntu_debian
elif [ -f /etc/fedora-release ]; then
  install_fedora
elif [ -f /etc/arch-release ]; then
  install_arch
else
  warn "Автоустановка для этой ОС не настроена."
  echo ""
  echo "Установите вручную:"
  echo "  Python 3.10+: https://www.python.org/downloads/"
  echo "  Node.js 18+:  https://nodejs.org/"
  exit 1
fi

echo ""
log "Повторная проверка"
check_python || { warn "Python не установлен"; exit 1; }
check_node || { warn "Node.js не установлен"; exit 1; }
echo ""
log "Готово! Запуск приложения: ./run.sh"
