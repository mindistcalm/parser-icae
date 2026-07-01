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

## Источники поиска

1. **Веб-поиск** — DuckDuckGo (по умолчанию) или Yandex Search API (если задан ключ)
2. **VK API** — поиск постов во ВКонтакте (нужен токен)
3. **RSS** — опционально, если добавите рабочие ленты в `config.yaml`

## Веб-интерфейс

Удобный UI на React + shadcn для запуска поиска, просмотра упоминаний и управления API-ключами.

### Запуск

```bash
cd /home/mindistcalm/Desktop/parser
./start-web.sh
```

Или вручную:

```bash
source .venv/bin/activate
pip install -e .
cd web && npm install && npm run build && cd ..
icae-web
```

Откройте в браузере: **http://localhost:8000**

Для разработки фронтенда (с hot-reload):

```bash
# терминал 1
icae-web

# терминал 2
cd web && npm run dev
# → http://localhost:5173 (проксирует /api на :8000)
```

### Разделы интерфейса

| Страница | Возможности |
|----------|-------------|
| **Главная** | Статус API, запуск поиска за месяц, прогресс в реальном времени, скачивание отчёта |
| **Упоминания** | Таблица всех найденных публикаций с фильтром |
| **Отчёты** | Список Excel/HTML файлов для скачивания |
| **Настройки** | Сохранение токенов в `env.txt` |

### API-ключи (env.txt)

Токены сохраняются через веб-интерфейс в файл `env.txt`:

```
VK_ACCESS_TOKEN=...
YANDEX_SEARCH_API_KEY=...
YANDEX_FOLDER_ID=...
```

## GitHub Pages

Сайт публикуется автоматически при push в `main`:

**https://mindistcalm.github.io/parser-icae/**

### Первоначальная настройка (один раз)

1. GitHub → **Settings** → **Pages**
2. **Source** → **GitHub Actions**
3. Запушьте `main` — workflow соберёт и опубликует сайт

### Что работает на Pages

| Функция | GitHub Pages | Локально |
|---------|:------------:|:--------:|
| Просмотр упоминаний | ✅ | ✅ |
| Скачивание отчётов | ✅ | ✅ |
| Запуск поиска | ❌ | ✅ |
| Настройка API-ключей | ❌ | ✅ |

### Обновить данные на сайте

Локально: `icae-parser run` → `git push`

Или в GitHub: **Actions** → **Deploy GitHub Pages** → **Run workflow** с опцией `run_parser`.

Опциональные secrets: `VK_ACCESS_TOKEN`, `YANDEX_SEARCH_API_KEY`, `YANDEX_FOLDER_ID`.

## Быстрый старт (CLI)

```bash
cd parser
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Создать .env и заполнить токены (опционально, но рекомендуется)
icae-parser init
```

### Настройка API (рекомендуется)

Скопируйте `.env.example` → `.env` и заполните:

| Переменная | Зачем |
|------------|-------|
| `VK_ACCESS_TOKEN` | Поиск постов ВКонтакте ([документация VK](https://dev.vk.com/ru/api/access-token/getting-started)) |
| `YANDEX_SEARCH_API_KEY` | Стабильный поиск через [Yandex Search API](https://yandex.cloud/ru/docs/search-api/) |
| `YANDEX_FOLDER_ID` | ID каталога в Yandex Cloud |

Без API-ключей используется DuckDuckGo. Для максимальной полноты рекомендуется VK-токен и Yandex Search API.

### Запуск в конце месяца

```bash
# Поиск + отчёт за прошлый месяц (например, 30 июня → данные за июнь)
icae-parser run

# За конкретный месяц
icae-parser run --month 2025-06

# Только поиск
icae-parser search --month 2025-06

# Только отчёт по уже собранным данным
icae-parser report --month 2025-06
```

Отчёты сохраняются в папку `reports/`:
- `icae_mentions_2025_06.xlsx` — Excel для отчётности
- `icae_mentions_2025_06.html` — HTML для просмотра в браузере

## Автозапуск (cron)

Добавьте в crontab задачу на последний день месяца в 18:00:

```cron
0 18 28-31 * * [ "$(date +\%d -d tomorrow)" = "01" ] && cd /home/mindistcalm/Desktop/parser && .venv/bin/icae-parser run >> logs/parser.log 2>&1
```

Или проще — 1-го числа каждого месяца в 9:00 за прошлый месяц:

```cron
0 9 1 * * cd /home/mindistcalm/Desktop/parser && .venv/bin/icae-parser run >> logs/parser.log 2>&1
```

## Настройка

Все параметры — в `config.yaml`:

- `search_keywords` — поисковые фразы
- `mention_patterns` / `city_patterns` — фильтры релевантности
- `exclude_domains` / `exclude_urls` — свои ресурсы для исключения
- `rss_feeds` — RSS-ленты СМИ

Добавьте в `exclude_urls` другие свои страницы, если появятся новые.

## Структура проекта

```
parser/
├── config.yaml          # настройки организации и поиска
├── .env                 # токены API (не коммитить)
├── data/mentions.db     # база найденных упоминаний
├── reports/             # готовые отчёты
└── src/parser/          # код приложения
```

## Ограничения

- Поиск в Telegram требует отдельной интеграции; сейчас Telegram-посты попадают через Yandex.
- HTML-поиск Yandex может меняться — для продакшена лучше API-ключ.
- VK API `newsfeed.search` ищет публичные посты, доступные методу; для полноты используйте и Yandex `site:vk.com`.
- Упоминания без даты публикации включаются в отчёт с пометкой «не указана» — проверьте вручную.
# parser-icae
