from __future__ import annotations

import re
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

DATE_META_NAMES = (
    "article:published_time",
    "og:published_time",
    "pubdate",
    "publishdate",
    "date",
    "DC.date.issued",
)


def fetch_publication_date(url: str, timeout: float = 10) -> datetime | None:
    """Пытается извлечь дату публикации со страницы."""
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "icae-mention-parser/1.0"},
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.HTTPError:
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    for prop in DATE_META_NAMES:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        if tag and tag.get("content"):
            parsed = _parse_date(tag["content"])
            if parsed:
                return parsed

    time_tag = soup.find("time", attrs={"datetime": True})
    if time_tag:
        parsed = _parse_date(time_tag["datetime"])
        if parsed:
            return parsed

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        text = script.get_text(strip=True)
        match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', text)
        if match:
            parsed = _parse_date(match.group(1))
            if parsed:
                return parsed

    return None


def _parse_date(value: str) -> datetime | None:
    try:
        return date_parser.parse(value).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None
