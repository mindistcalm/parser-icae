from __future__ import annotations

import re
import time
from datetime import datetime
from urllib.parse import urlparse

from dateutil import parser as date_parser
from ddgs import DDGS

from parser.config import AppConfig
from parser.models import Mention, SourceType
from parser.search.base import SearchProvider

MONTH_NAMES_RU = {
    1: "январь",
    2: "февраль",
    3: "март",
    4: "апрель",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "август",
    9: "сентябрь",
    10: "октябрь",
    11: "ноябрь",
    12: "декабрь",
}


class DuckDuckGoSearchProvider(SearchProvider):
    name = "DuckDuckGo"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.delay = config.search.request_delay_seconds

    def search(self, query: str, year: int, month: int) -> list[Mention]:
        month_name = MONTH_NAMES_RU[month]
        enriched_query = f"{query} {month_name} {year}"
        max_results = self.config.search.max_results_per_query

        mentions: list[Mention] = []
        try:
            with DDGS() as ddgs:
                results = ddgs.text(
                    enriched_query,
                    region="ru-ru",
                    max_results=max_results,
                )
                for item in results:
                    mention = self._parse_result(item, query, year, month)
                    if mention:
                        mentions.append(mention)
        except Exception:
            # Повтор без месяца — DDG иногда не находит по дате в запросе
            with DDGS() as ddgs:
                results = ddgs.text(
                    query,
                    region="ru-ru",
                    max_results=max_results,
                )
                for item in results:
                    mention = self._parse_result(item, query, year, month)
                    if mention:
                        mentions.append(mention)

        time.sleep(self.delay)
        return mentions

    def _parse_result(
        self, item: dict, query: str, year: int, month: int
    ) -> Mention | None:
        url = item.get("href", "")
        if not url.startswith("http"):
            return None

        title = item.get("title", "").strip()
        snippet = item.get("body", "").strip()
        published = self._extract_date_from_snippet(snippet, year, month)

        return Mention(
            source_name=self._host_name(url),
            title=title or url,
            url=url,
            published_at=published,
            source_type=SourceType.WEB,
            snippet=snippet,
            search_query=query,
        )

    @staticmethod
    def _host_name(url: str) -> str:
        host = urlparse(url).netloc.lower().removeprefix("www.")
        if "vk.com" in host:
            return "ВКонтакте"
        if "t.me" in host:
            return "Telegram"
        return host

    @staticmethod
    def _extract_date_from_snippet(
        snippet: str, year: int, month: int
    ) -> datetime | None:
        patterns = [
            r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})",
            r"(\d{1,2})\s+(январ|феврал|март|апрел|ма[йя]|июн|июл|август|сентябр|октябр|ноябр|декабр)\w*\s+(\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                try:
                    dt = date_parser.parse(match.group(0), dayfirst=True, fuzzy=True)
                    return dt.replace(tzinfo=None)
                except (ValueError, TypeError):
                    continue
        return None
