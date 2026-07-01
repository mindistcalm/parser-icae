from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    WEB = "web"
    VK = "vk"
    RSS = "rss"


@dataclass
class Mention:
    source_name: str
    title: str
    url: str
    published_at: datetime | None
    source_type: SourceType
    snippet: str = ""
    search_query: str = ""
    found_at: datetime = field(default_factory=datetime.now)

    @property
    def url_normalized(self) -> str:
        url = self.url.lower().rstrip("/")
        if "?" in url:
            url = url.split("?", 1)[0]
        return url
