# Мониторинг упоминаний ИЦАЭ Томска

Приложение автоматизирует ежемесячный поиск упоминаний **Информационного центра по атомной энергии (ИЦАЭ)** в Томске в интернете: ВКонтакте, новостных сайтах, сайтах других организаций.

В конце месяца формируется отчёт со списком ресурсов, где упомянули ИЦАЭ.

## Что собирается

| Поле | Описание |
|------|----------|
| Ресурс | Название сайта / ВКонтакте |
| Заголовок | Название поста или статьи |
| Ссылка | URL на публикацию |
| Дата | Дата публикации (если доступна) |

Собственные страницы (myatom.ru, vk.com/myatomtomsk, t.me/myatom_Tomsk и др.) **исключаются** из отчёта.

## Источники поиска (без API-ключей)

1. **DuckDuckGo** — веб-поиск по ключевым фразам, включая `site:vk.com`
2. **RSS** — опционально, если добавите рабочие ленты в `config.yaml`

Токены и API-ключи **не требуются**.

## Требования

| Компонент | Версия | Зачем |
|-----------|--------|-------|
| Python | 3.10+ | парсер, API |
| Node.js | 18+ | сборка веб-интерфейса |
| Git | любая | клонирование репозитория |

### Установка требований (одна команда)

**Windows (PowerShell или cmd):**

```powershell
git clone https://github.com/mindistcalm/parser-icae.git
cd parser-icae
.\install-deps.bat
.\run.bat
```

**Linux / macOS:**

```bash
git clone https://github.com/mindistcalm/parser-icae.git
cd parser-icae
chmod +x install-deps.sh run.sh
./install-deps.sh
./run.sh
```

### Установка вручную

**Windows (winget):**

```powershell
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```

После установки **перезапустите терминал**. При установке Python отметьте **Add python.exe to PATH**.

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

**Fedora:**

```bash
sudo dnf install -y python3 python3-pip nodejs npm
```

**macOS (Homebrew):**

```bash
brew install python@3.12 node
```

### Проверка

```bash
python3 --version    # Python 3.10+
node -v            # v18+
npm -v
```

Windows:

```powershell
py -3 --version
node -v
```

## Быстрый старт (одна команда)

Нужны **Python 3.10+** и **Node.js 18+** (см. выше, если ещё не установлены).

### Windows

```powershell
git clone https://github.com/mindistcalm/parser-icae.git
cd parser-icae
.\run.bat
```

Или в PowerShell: `.\run.ps1`

Двойной клик по `run.bat` тоже работает.

### Linux / macOS

```bash
git clone https://github.com/mindistcalm/parser-icae.git
cd parser-icae
chmod +x run.sh
./run.sh
```

Скрипт сам:
1. создаёт `.venv` и ставит Python-зависимости
2. делает `npm install` + сборку фронтенда (при первом запуске)
3. открывает **http://localhost:8000**

Другой порт: `PORT=8001 ./run.sh` (Windows: `$env:PORT=8001; .\run.ps1`)

Пропустить сборку фронтенда: `SKIP_BUILD=1 ./run.sh`

## Веб-интерфейс

UI на React + shadcn для запуска поиска, просмотра упоминаний и скачивания отчётов.

### Запуск

```bash
./run.sh
```

Откройте в браузере: **http://localhost:8000**

### Разделы интерфейса

| Страница | Возможности |
|----------|-------------|
| **Главная** | Запуск поиска за месяц, прогресс, скачивание отчёта |
| **Упоминания** | Таблица публикаций с фильтром |
| **Отчёты** | Excel/HTML файлы |
| **Настройки** | Редактирование `config.yaml` |

## GitHub Pages

**https://mindistcalm.github.io/parser-icae/**

### Настройка (один раз)

1. GitHub → **Settings** → **Pages** → **Source: GitHub Actions**
2. Push в `main`

### Обновить данные на сайте

- Локально: `icae-parser run` → `git push`
- Или: **Actions** → **Deploy GitHub Pages** → **Run workflow** с `run_parser`

На Pages доступен только просмотр; поиск — локально или через workflow.

## Быстрый старт (CLI)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
icae-parser run
```

### Запуск в конце месяца

```bash
icae-parser run                    # прошлый месяц
icae-parser run --month 2025-06    # конкретный месяц
```

## Настройка

Все параметры — в `config.yaml`:

- `search_keywords` — поисковые фразы
- `exclude_urls` / `exclude_domains` — свои ресурсы для исключения
- `rss_feeds` — RSS-ленты СМИ

## Ограничения

- Поиск через DuckDuckGo — без гарантии полноты, возможны задержки
- ВКонтакте ищется через веб-поиск (`site:vk.com`), не через VK API
- Telegram напрямую не парсится
- Упоминания без даты помечаются «не указана» — проверьте вручную
