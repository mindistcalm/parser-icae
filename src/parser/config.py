from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class OrganizationConfig(BaseModel):
    full_name: str
    short_name: str
    city: str


class RssFeedConfig(BaseModel):
    name: str
    url: str


class SearchConfig(BaseModel):
    max_results_per_query: int = 50
    request_delay_seconds: float = 1.5


class StorageConfig(BaseModel):
    database_path: str = "data/mentions.db"


class ReportsConfig(BaseModel):
    output_dir: str = "reports"


class AppConfig(BaseModel):
    organization: OrganizationConfig
    search_keywords: list[str]
    mention_patterns: list[str]
    city_patterns: list[str]
    exclude_domains: list[str] = Field(default_factory=list)
    exclude_urls: list[str] = Field(default_factory=list)
    exclude_url_fragments: list[str] = Field(default_factory=list)
    exclude_url_patterns: list[str] = Field(default_factory=list)
    rss_feeds: list[RssFeedConfig] = Field(default_factory=list)
    search: SearchConfig = Field(default_factory=SearchConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)


def find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / "config.yaml").exists():
            return parent
    return Path.cwd()


def load_config(config_path: Path | None = None) -> AppConfig:
    root = find_project_root()
    path = config_path or root / "config.yaml"
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return AppConfig.model_validate(raw)
