from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse

from parser.config import AppConfig
from parser.models import Mention


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def is_excluded_url(url: str, config: AppConfig) -> bool:
    lowered = url.lower()
    for excluded in config.exclude_urls:
        if excluded.lower() in lowered:
            return True
    for fragment in config.exclude_url_fragments:
        if fragment.lower() in lowered:
            return True

    for pattern in config.exclude_url_patterns:
        if pattern.lower() in lowered:
            return True

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().removeprefix("www.")
    for domain in config.exclude_domains:
        if host == domain.lower() or host.endswith("." + domain.lower()):
            return True
    return False


def mentions_organization(text: str, config: AppConfig) -> bool:
    normalized = _normalize_text(text)
    return any(pattern in normalized for pattern in config.mention_patterns)


def mentions_tomsk(text: str, config: AppConfig) -> bool:
    normalized = _normalize_text(text)
    return any(pattern in normalized for pattern in config.city_patterns)


def is_relevant_mention(mention: Mention, config: AppConfig) -> bool:
    if is_excluded_url(mention.url, config):
        return False

    combined = " ".join(
        filter(None, [mention.title, mention.snippet, mention.url])
    )
    if not mentions_organization(combined, config):
        return False

    # Для общих запросов вроде «атомный центр» требуем упоминание Томска
    # или явную привязку к ИЦАЭ
    normalized = _normalize_text(combined)
    has_tomsk = mentions_tomsk(combined, config)
    has_strong_match = any(
        p in normalized
        for p in ("ицаэ", "ицae", "myatom", "информационный центр")
    )
    if not has_tomsk and not has_strong_match:
        return False

    return True


def is_in_month(dt: datetime | None, year: int, month: int) -> bool:
    if dt is None:
        return True  # без даты оставляем, но помечаем в отчёте
    return dt.year == year and dt.month == month


def filter_mentions(
    mentions: list[Mention],
    config: AppConfig,
    year: int,
    month: int,
) -> list[Mention]:
    seen: set[str] = set()
    result: list[Mention] = []

    for mention in mentions:
        if not is_relevant_mention(mention, config):
            continue
        if mention.published_at and not is_in_month(
            mention.published_at, year, month
        ):
            continue
        key = mention.url_normalized
        if key in seen:
            continue
        seen.add(key)
        result.append(mention)

    return result
