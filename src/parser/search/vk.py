from __future__ import annotations

import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from dateutil import parser as date_parser

from parser.config import AppConfig, EnvSettings
from parser.models import Mention, SourceType
from parser.search.base import SearchProvider

VK_API_URL = "https://api.vk.com/method/newsfeed.search"
VK_VERSION = "5.199"


class VkSearchProvider(SearchProvider):
    name = "VK"

    def __init__(self, config: AppConfig, env: EnvSettings) -> None:
        self.config = config
        self.env = env
        self.delay = config.search.request_delay_seconds

    def search(self, query: str, year: int, month: int) -> list[Mention]:
        if not self.env.vk_access_token:
            return []

        start_ts = int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp())
        if month == 12:
            end_dt = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_dt = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        end_ts = int(end_dt.timestamp()) - 1

        mentions: list[Mention] = []
        offset = 0
        count = 100

        with httpx.Client(timeout=30) as client:
            while offset < self.config.search.max_results_per_query:
                params = {
                    "q": query,
                    "count": min(count, self.config.search.max_results_per_query - offset),
                    "start_time": start_ts,
                    "end_time": end_ts,
                    "access_token": self.env.vk_access_token,
                    "v": VK_VERSION,
                }
                resp = client.get(VK_API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

                if "error" in data:
                    error = data["error"]
                    raise RuntimeError(
                        f"VK API error {error.get('error_code')}: {error.get('error_msg')}"
                    )

                items = data.get("response", {}).get("items", [])
                if not items:
                    break

                for item in items:
                    post = self._item_to_mention(item, query)
                    if post:
                        mentions.append(post)

                offset += len(items)
                if len(items) < count:
                    break
                time.sleep(self.delay)

        return mentions

    def _item_to_mention(self, item: dict, query: str) -> Mention | None:
        post_type = item.get("type")
        if post_type != "post":
            return None

        post = item.get("post", item)
        owner_id = post.get("owner_id", 0)
        post_id = post.get("id", 0)
        if not post_id:
            return None

        text = post.get("text", "")
        date_ts = post.get("date")
        published = (
            datetime.fromtimestamp(date_ts, tz=timezone.utc).replace(tzinfo=None)
            if date_ts
            else None
        )

        if owner_id < 0:
            group_id = abs(owner_id)
            url = f"https://vk.com/wall-{group_id}_{post_id}"
            source_name = f"ВКонтакте (группа {group_id})"
        else:
            url = f"https://vk.com/wall{owner_id}_{post_id}"
            source_name = "ВКонтакте"

        title = text.split("\n", 1)[0][:200] if text else f"Пост {post_id}"
        if len(title) < 10 and text:
            title = text[:200]

        return Mention(
            source_name=source_name,
            title=title.strip() or url,
            url=url,
            published_at=published,
            source_type=SourceType.VK,
            snippet=text[:500],
            search_query=query,
        )
