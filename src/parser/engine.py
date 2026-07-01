from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date

from parser.config import AppConfig, EnvSettings, load_config, load_env
from parser.filters import filter_mentions
from parser.metadata import fetch_publication_date
from parser.models import Mention
from parser.search.duckduckgo import DuckDuckGoSearchProvider
from parser.search.rss import RssSearchProvider
from parser.search.vk import VkSearchProvider
from parser.search.yandex import YandexSearchProvider
from parser.storage import MentionStorage


def month_label(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def previous_month(today: date | None = None) -> tuple[int, int]:
    today = today or date.today()
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


class SearchEngine:
    def __init__(
        self,
        config: AppConfig | None = None,
        env: EnvSettings | None = None,
    ) -> None:
        self.config = config or load_config()
        self.env = env or load_env()
        self.storage = MentionStorage(self.config.storage.database_path)
        self.web_provider: YandexSearchProvider | DuckDuckGoSearchProvider
        if self.env.yandex_search_api_key and self.env.yandex_folder_id:
            self.web_provider = YandexSearchProvider(self.config, self.env)
        else:
            self.web_provider = DuckDuckGoSearchProvider(self.config)

        self.providers = [
            self.web_provider,
            VkSearchProvider(self.config, self.env),
            RssSearchProvider(self.config),
        ]

    def collect(
        self,
        year: int,
        month: int,
        *,
        verbose: bool = True,
        on_progress: Callable[[str], None] | None = None,
    ) -> list[Mention]:
        def log(msg: str) -> None:
            if verbose:
                print(msg)
            if on_progress:
                on_progress(msg)

        all_mentions: list[Mention] = []
        report_month = month_label(year, month)

        vk_queries = list(self.config.search_keywords)
        vk_queries.append("site:vk.com " + self.config.organization.short_name)

        web_name = self.web_provider.name

        for provider in self.providers:
            queries = (
                vk_queries
                if provider.name in (web_name, "Yandex")
                else self.config.search_keywords
                if provider.name == "VK"
                else ["rss"]
            )

            if provider.name == "VK" and not self.env.vk_access_token:
                log("  [VK] пропущен — задайте VK_ACCESS_TOKEN в env.txt")
                continue

            log(f"  [{provider.name}] поиск...")

            for query in queries:
                if query == "rss" and provider.name != "RSS":
                    continue
                if provider.name == "RSS" and query != "rss":
                    provider_query = query
                else:
                    provider_query = query

                try:
                    found = provider.search(provider_query, year, month)
                    filtered = filter_mentions(found, self.config, year, month)
                    all_mentions.extend(filtered)
                    if provider.name != "RSS":
                        log(
                            f"    «{provider_query[:50]}»: "
                            f"найдено {len(found)}, релевантных {len(filtered)}"
                        )
                except Exception as exc:
                    log(f"    ошибка для «{provider_query[:40]}»: {exc}")

                if provider.name != "RSS":
                    time.sleep(self.config.search.request_delay_seconds)

            if provider.name == "RSS":
                rss_count = sum(1 for m in all_mentions if m.source_type.value == "rss")
                log(f"    RSS: релевантных записей {rss_count}")

        # Финальная дедупликация + обогащение дат
        deduped = filter_mentions(all_mentions, self.config, year, month)
        deduped = self._enrich_dates(deduped, year, month, on_progress=on_progress)
        deduped = filter_mentions(deduped, self.config, year, month)
        inserted = self.storage.save_mentions(deduped, report_month)

        log(
            f"\nИтого уникальных упоминаний: {len(deduped)} "
            f"(новых в БД: {inserted})"
        )

        return deduped

    def _enrich_dates(
        self,
        mentions: list[Mention],
        year: int,
        month: int,
        *,
        on_progress: Callable[[str], None] | None = None,
    ) -> list[Mention]:
        enriched: list[Mention] = []
        for m in mentions:
            if m.published_at is not None:
                enriched.append(m)
                continue
            fetched = fetch_publication_date(m.url)
            if fetched:
                m.published_at = fetched
            enriched.append(m)
        with_dates = sum(1 for m in enriched if m.published_at)
        msg = f"  Даты публикации: {with_dates}/{len(enriched)}"
        if on_progress:
            on_progress(msg)
        return enriched

    def get_stored(self, year: int, month: int) -> list[Mention]:
        return self.storage.get_mentions_for_month(month_label(year, month))
