from __future__ import annotations

import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from parser.config import AppConfig
from parser.models import Mention, SourceType
from parser.search.base import SearchProvider


class RssSearchProvider(SearchProvider):
    name = "RSS"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.delay = config.search.request_delay_seconds

    def search(self, query: str, year: int, month: int) -> list[Mention]:
        del query  # RSS ищет по всем лентам, фильтр — в filters.py
        mentions: list[Mention] = []

        for feed in self.config.rss_feeds:
            mentions.extend(self._parse_feed(feed.name, feed.url, year, month))
            time.sleep(self.delay)

        return mentions

    def _parse_feed(
        self, feed_name: str, feed_url: str, year: int, month: int
    ) -> list[Mention]:
        headers = {
            "User-Agent": "icae-mention-parser/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml",
        }
        mentions: list[Mention] = []

        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(feed_url, headers=headers)
                resp.raise_for_status()
        except httpx.HTTPError:
            return mentions

        soup = BeautifulSoup(resp.content, "lxml-xml")
        items = soup.find_all("item")
        if not items:
            # fallback for malformed feeds
            soup = BeautifulSoup(resp.content, "lxml")
            items = soup.find_all("item")

        for item in items:
            title = (item.find("title").get_text() if item.find("title") else "").strip()
            link_tag = item.find("link")
            url = ""
            if link_tag:
                url = link_tag.get_text(strip=True) or link_tag.get("href", "")
            if not url:
                continue

            description = ""
            desc_tag = item.find("description") or item.find("content:encoded")
            if desc_tag:
                description = BeautifulSoup(
                    desc_tag.get_text(), "lxml"
                ).get_text(" ", strip=True)

            published = self._parse_item_date(item)
            if published and not (published.year == year and published.month == month):
                continue

            mentions.append(
                Mention(
                    source_name=feed_name,
                    title=title or url,
                    url=url,
                    published_at=published,
                    source_type=SourceType.RSS,
                    snippet=description[:500],
                    search_query="rss",
                )
            )

        return mentions

    @staticmethod
    def _parse_item_date(item) -> datetime | None:
        for tag_name in ("pubDate", "published", "updated", "dc:date"):
            tag = item.find(tag_name)
            if not tag:
                continue
            raw = tag.get_text(strip=True)
            try:
                return parsedate_to_datetime(raw).replace(tzinfo=None)
            except (ValueError, TypeError):
                try:
                    return date_parser.parse(raw).replace(tzinfo=None)
                except (ValueError, TypeError):
                    continue
        return None
