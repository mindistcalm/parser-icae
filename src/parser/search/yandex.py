from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from parser.config import AppConfig, EnvSettings
from parser.models import Mention, SourceType
from parser.search.base import SearchProvider

YANDEX_API_URL = "https://searchapi.api.cloud.yandex.net/v2/web/search"
YANDEX_HTML_URL = "https://yandex.ru/search/"


class YandexSearchProvider(SearchProvider):
    name = "Yandex"

    def __init__(self, config: AppConfig, env: EnvSettings) -> None:
        self.config = config
        self.env = env
        self.delay = config.search.request_delay_seconds

    def search(self, query: str, year: int, month: int) -> list[Mention]:
        if self.env.yandex_search_api_key and self.env.yandex_folder_id:
            return self._search_api(query, year, month)
        return self._search_html(query, year, month)

    def _month_bounds(self, year: int, month: int) -> tuple[datetime, datetime]:
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        return start, end

    def _search_api(self, query: str, year: int, month: int) -> list[Mention]:
        start, end = self._month_bounds(year, month)
        body = {
            "query": {
                "searchType": "SEARCH_TYPE_RU",
                "queryText": query,
                "familyMode": "FAMILY_MODE_MODERATE",
                "page": 0,
            },
            "sortSpec": {
                "sortMode": "SORT_MODE_BY_RELEVANCE",
                "sortOrder": "SORT_ORDER_DESC",
            },
            "groupSpec": {
                "groupMode": "GROUP_MODE_FLAT",
                "groupsOnPage": self.config.search.max_results_per_query,
                "docsInGroup": 1,
            },
            "maxPassages": 2,
            "region": "225",
            "l10n": "LOCALIZATION_RU",
            "folderId": self.env.yandex_folder_id,
            "responseFormat": "FORMAT_JSON",
            "userAgent": "icae-mention-parser/1.0",
        }

        headers = {
            "Authorization": f"Api-Key {self.env.yandex_search_api_key}",
            "Content-Type": "application/json",
        }

        mentions: list[Mention] = []
        with httpx.Client(timeout=30) as client:
            resp = client.post(YANDEX_API_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        raw = data.get("rawData")
        if not raw:
            return mentions

        payload = json.loads(base64.b64decode(raw).decode("utf-8"))
        for group in payload.get("response", {}).get("results", []):
            for doc in group.get("grouping", {}).get("group", []):
                doc_data = doc.get("doc", {})
                url = doc.get("url") or doc_data.get("url", "")
                title = self._clean_text(doc_data.get("title", ""))
                snippet = self._clean_text(doc_data.get("passages", [{}])[0].get("passage", ""))
                published = self._parse_date(doc_data.get("modtime") or doc_data.get("date"))

                if published and not (start <= published.replace(tzinfo=timezone.utc) < end):
                    continue

                mentions.append(
                    Mention(
                        source_name=self._host_name(url),
                        title=title or url,
                        url=url,
                        published_at=published,
                        source_type=SourceType.WEB,
                        snippet=snippet,
                        search_query=query,
                    )
                )

        time.sleep(self.delay)
        return mentions

    def _search_html(self, query: str, year: int, month: int) -> list[Mention]:
        """Резервный режим без API-ключа."""
        start, end = self._month_bounds(year, month)
        date_filter = f"date:{start.strftime('%Y%m%d')}..{end.strftime('%Y%m%d')}"
        full_query = f"{query} {date_filter}"

        params = {
            "text": full_query,
            "lr": "67",  # Томская область
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9",
        }

        mentions: list[Mention] = []
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(YANDEX_HTML_URL, params=params, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

        for item in soup.select("li.serp-item, div.Organic"):
            link = item.select_one("a[href]")
            if not link:
                continue
            url = link.get("href", "")
            if not url.startswith("http"):
                continue

            title_el = item.select_one("h2, .OrganicTitle-LinkText, a")
            title = self._clean_text(title_el.get_text() if title_el else url)

            snippet_el = item.select_one(
                ".OrganicTextContentSpan, .text-container, .serp-item__text"
            )
            snippet = self._clean_text(snippet_el.get_text() if snippet_el else "")

            date_el = item.select_one(".Organic-Subtitle, .serp-item__date")
            published = self._parse_date(date_el.get_text() if date_el else None)

            mentions.append(
                Mention(
                    source_name=self._host_name(url),
                    title=title,
                    url=url,
                    published_at=published,
                    source_type=SourceType.WEB,
                    snippet=snippet,
                    search_query=query,
                )
            )

        time.sleep(self.delay)
        return mentions[: self.config.search.max_results_per_query]

    @staticmethod
    def _host_name(url: str) -> str:
        host = urlparse(url).netloc.lower().removeprefix("www.")
        if "vk.com" in host:
            return "ВКонтакте"
        if "t.me" in host or "telegram" in host:
            return "Telegram"
        return host

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"<[^>]+>", "", text).strip()

    @staticmethod
    def _parse_date(value: str | int | None) -> datetime | None:
        if value is None:
            return None
        try:
            if isinstance(value, int):
                return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None)
            return date_parser.parse(str(value), dayfirst=True, fuzzy=True).replace(
                tzinfo=None
            )
        except (ValueError, TypeError, OverflowError):
            return None
