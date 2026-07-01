from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from parser.api.jobs import job_manager
from parser.api.schemas import (
    DashboardOut,
    JobOut,
    MentionOut,
    MonthSummary,
    OrganizationOut,
    ProviderStatus,
    ReportFile,
    RunRequest,
    RunResponse,
)
from parser.config import find_project_root, load_config
from parser.engine import SearchEngine, month_label, previous_month
from parser.report import MONTH_NAMES_RU

app = FastAPI(title="ИЦАЭ Parser API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mention_to_out(m) -> MentionOut:
    return MentionOut(
        source_name=m.source_name,
        title=m.title,
        url=m.url,
        published_at=m.published_at.isoformat() if m.published_at else None,
        source_type=m.source_type.value,
        snippet=m.snippet,
    )


def _parse_month(month: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})-(\d{2})", month.strip())
    if not match:
        raise HTTPException(400, "Формат месяца: YYYY-MM")
    year, mon = int(match.group(1)), int(match.group(2))
    if mon < 1 or mon > 12:
        raise HTTPException(400, "Месяц должен быть от 01 до 12")
    return year, mon


def _list_reports() -> list[ReportFile]:
    config = load_config()
    reports_dir = find_project_root() / config.reports.output_dir
    if not reports_dir.exists():
        return []

    files: list[ReportFile] = []
    for path in sorted(reports_dir.iterdir(), reverse=True):
        if not path.is_file():
            continue
        match = re.match(r"icae_mentions_(\d{4})_(\d{2})\.(xlsx|html)$", path.name)
        if not match:
            continue
        files.append(
            ReportFile(
                filename=path.name,
                month=f"{match.group(1)}-{match.group(2)}",
                kind=match.group(3),
                size=path.stat().st_size,
            )
        )
    return files


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard() -> DashboardOut:
    config = load_config()
    engine = SearchEngine(config)
    py, pm = previous_month()

    return DashboardOut(
        organization=OrganizationOut(**config.organization.model_dump()),
        providers=ProviderStatus(
            web="DuckDuckGo",
            rss=bool(config.rss_feeds),
        ),
        previous_month=month_label(py, pm),
        months=[MonthSummary(**m) for m in engine.storage.list_months()],
        latest_reports=_list_reports()[:10],
    )


@app.get("/api/mentions", response_model=list[MentionOut])
def get_mentions(month: str) -> list[MentionOut]:
    year, mon = _parse_month(month)
    engine = SearchEngine()
    mentions = engine.get_stored(year, mon)
    return [_mention_to_out(m) for m in mentions]


@app.get("/api/months", response_model=list[MonthSummary])
def get_months() -> list[MonthSummary]:
    engine = SearchEngine()
    return [MonthSummary(**m) for m in engine.storage.list_months()]


@app.post("/api/run", response_model=RunResponse)
def run_search(body: RunRequest) -> RunResponse:
    year, mon = _parse_month(body.month)
    job_id = job_manager.start_run(year, mon)
    return RunResponse(job_id=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str) -> JobOut:
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(404, "Задача не найдена")
    return job


@app.get("/api/reports", response_model=list[ReportFile])
def get_reports() -> list[ReportFile]:
    return _list_reports()


@app.get("/api/reports/{filename}")
def download_report(filename: str) -> FileResponse:
    if not re.fullmatch(r"icae_mentions_\d{4}_\d{2}\.(xlsx|html)", filename):
        raise HTTPException(400, "Недопустимое имя файла")

    config = load_config()
    path = find_project_root() / config.reports.output_dir / filename
    if not path.exists():
        raise HTTPException(404, "Файл не найден")

    media = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if filename.endswith(".xlsx")
        else "text/html"
    )
    return FileResponse(path, media_type=media, filename=filename)


@app.get("/api/month-label")
def get_month_label(month: str) -> dict[str, str]:
    year, mon = _parse_month(month)
    return {
        "month": month_label(year, mon),
        "label": f"{MONTH_NAMES_RU[mon]} {year}",
    }


def mount_frontend() -> None:
    dist = find_project_root() / "web" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="static")
