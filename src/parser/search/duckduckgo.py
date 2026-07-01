from __future__ import annotations

import re
import time
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from parser.config import AppConfig
from parser.models import Mention, SourceType
from parser.search.base import SearchProvider

DDG_URL = "https://html.duckduckgo.com/html/"

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

        mentions: list[Mention] = []
        offset = 0
        page_size = 30
        max_results = self.config.search.max_results_per_query

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        }

        with httpx.Client(timeout=30, follow_redirects=True) as client:
            while len(mentions) < max_results:
                data = {"q": enriched_query, "kl": "ru-ru", "s": str(offset)}
                resp = client.post(DDG_URL, data=data, headers=headers)
                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "lxml")
                results = soup.select(".result")
                if not results:
                    break

                for item in results:
                    mention = self._parse_result(item, query, year, month)
                    if mention:
                        mentions.append(mention)
                    if len(mentions) >= max_results:
                        break

                # Следующая страница
                next_btn = soup.select_one("input.result--more__btn")
                if not next_btn or len(results) < page_size:
                    break
                offset += page_size
                time.sleep(self.delay)

        return mentions

    def _parse_result(
        self, item, query: str, year: int, month: int
    ) -> Mention | None:
        link = item.select_one("a.result__a")
        if not link:
            return None

        url = self._resolve_url(link.get("href", ""))
        if not url.startswith("http"):
            return None

        title = link.get_text(strip=True)
        snippet_el = item.select_one(".result__snippet")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

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
    def _resolve_url(href: str) -> str:
        if href.startswith("//"):
            href = "https:" + href
        if "uddg=" in href:
            parsed = urlparse(href)
            uddg = parse_qs(parsed.query).get("uddg", [""])[0]
            return unquote(uddg)
        return href

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
        # DDG иногда показывает дату в сниппете
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
