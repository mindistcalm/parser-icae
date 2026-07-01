from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SettingsOut(BaseModel):
    vk_access_token: str = ""
    yandex_search_api_key: str = ""
    yandex_folder_id: str = ""


class SettingsIn(BaseModel):
    vk_access_token: str = ""
    yandex_search_api_key: str = ""
    yandex_folder_id: str = ""


class ProviderStatus(BaseModel):
    vk: bool
    yandex: bool
    web_fallback: str


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
