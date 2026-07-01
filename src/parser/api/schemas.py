from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProviderStatus(BaseModel):
    web: str = "DuckDuckGo"
    rss: bool = False


class OrganizationOut(BaseModel):
    full_name: str
    short_name: str
    city: str


class MentionOut(BaseModel):
    source_name: str
    title: str
    url: str
    published_at: str | None
    source_type: str
    snippet: str = ""


class MonthSummary(BaseModel):
    month: str
    count: int


class RunRequest(BaseModel):
    month: str = Field(..., description="YYYY-MM")


class RunResponse(BaseModel):
    job_id: str


class JobOut(BaseModel):
    id: str
    status: JobStatus
    month: str
    logs: list[str] = Field(default_factory=list)
    mentions_count: int = 0
    report_xlsx: str | None = None
    report_html: str | None = None
    error: str | None = None
    started_at: datetime
    finished_at: datetime | None = None


class ReportFile(BaseModel):
    filename: str
    month: str
    kind: str
    size: int


class DashboardOut(BaseModel):
    organization: OrganizationOut
    providers: ProviderStatus
    previous_month: str
    months: list[MonthSummary]
    latest_reports: list[ReportFile]


class RssFeedIn(BaseModel):
    name: str
    url: str


class OrganizationIn(BaseModel):
    full_name: str
    short_name: str
    city: str


class SearchSettingsIn(BaseModel):
    max_results_per_query: int = Field(ge=1, le=200)
    request_delay_seconds: float = Field(ge=0.5, le=10)


class StorageSettingsIn(BaseModel):
    database_path: str


class ReportsSettingsIn(BaseModel):
    output_dir: str


class AppConfigIn(BaseModel):
    organization: OrganizationIn
    search_keywords: list[str]
    mention_patterns: list[str]
    city_patterns: list[str]
    exclude_domains: list[str] = Field(default_factory=list)
    exclude_urls: list[str] = Field(default_factory=list)
    exclude_url_fragments: list[str] = Field(default_factory=list)
    exclude_url_patterns: list[str] = Field(default_factory=list)
    rss_feeds: list[RssFeedIn] = Field(default_factory=list)
    search: SearchSettingsIn = Field(default_factory=SearchSettingsIn)
    storage: StorageSettingsIn = Field(default_factory=lambda: StorageSettingsIn(database_path="data/mentions.db"))
    reports: ReportsSettingsIn = Field(default_factory=lambda: ReportsSettingsIn(output_dir="reports"))
