#!/usr/bin/env python3
"""Экспорт данных парсера в статические файлы для GitHub Pages."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from parser.config import find_project_root, load_config
from parser.engine import SearchEngine, month_label, previous_month
from parser.report import ReportGenerator

ROOT = find_project_root()
PUBLIC = ROOT / "web" / "public"
DATA_DIR = PUBLIC / "data"
REPORTS_OUT = PUBLIC / "reports"

REPORT_NAME_RE = re.compile(r"icae_mentions_(\d{4})_(\d{2})\.(xlsx|html)$")


def _list_reports_from_dir(directory: Path) -> list[dict]:
    if not directory.exists():
        return []

    files: list[dict] = []
    for path in sorted(directory.iterdir(), reverse=True):
        if not path.is_file():
            continue
        match = REPORT_NAME_RE.match(path.name)
        if not match:
            continue
        files.append(
            {
                "filename": path.name,
                "month": f"{match.group(1)}-{match.group(2)}",
                "kind": match.group(3),
                "size": path.stat().st_size,
            }
        )
    return files


def _ensure_reports(engine: SearchEngine, config) -> Path:
    """Создаёт Excel/HTML отчёты для всех месяцев в БД (если ещё нет)."""
    generator = ReportGenerator(config)
    reports_dir = ROOT / config.reports.output_dir
    reports_dir.mkdir(parents=True, exist_ok=True)

    for entry in engine.storage.list_months():
        month = entry["month"]
        year, mon = map(int, month.split("-"))
        base = f"icae_mentions_{year:04d}_{mon:02d}"
        html_path = reports_dir / f"{base}.html"
        xlsx_path = reports_dir / f"{base}.xlsx"
        if not html_path.exists() or not xlsx_path.exists():
            mentions = engine.get_stored(year, mon)
            generator.generate(mentions, year, mon)

    return reports_dir


def export() -> None:
    config = load_config()
    engine = SearchEngine()
    py, pm = previous_month()

    reports_dir = _ensure_reports(engine, config)
    months = engine.storage.list_months()
    mentions_by_month: dict[str, list[dict]] = {}

    for entry in months:
        month = entry["month"]
        year, mon = map(int, month.split("-"))
        mentions = engine.get_stored(year, mon)
        mentions_by_month[month] = [
            {
                "source_name": m.source_name,
                "title": m.title,
                "url": m.url,
                "published_at": m.published_at.isoformat() if m.published_at else None,
                "source_type": m.source_type.value,
                "snippet": m.snippet,
            }
            for m in mentions
        ]
        # актуализируем счётчик в manifest
        entry["count"] = len(mentions_by_month[month])

    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    DATA_DIR.mkdir(parents=True)

    if REPORTS_OUT.exists():
        shutil.rmtree(REPORTS_OUT)
    REPORTS_OUT.mkdir(parents=True)

    for path in reports_dir.iterdir():
        if path.is_file() and path.suffix in {".xlsx", ".html"}:
            shutil.copy2(path, REPORTS_OUT / path.name)

    report_files = _list_reports_from_dir(REPORTS_OUT)

    manifest = {
        "organization": config.organization.model_dump(),
        "providers": {
            "web": "DuckDuckGo",
            "rss": bool(config.rss_feeds),
        },
        "previous_month": month_label(py, pm),
        "months": months,
        "latest_reports": report_files[:20],
        "config": config.model_dump(mode="python"),
        "static": True,
    }

    (DATA_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (DATA_DIR / "reports.json").write_text(
        json.dumps(report_files, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for month, items in mentions_by_month.items():
        (DATA_DIR / f"mentions-{month}.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(
        f"Экспортировано: месяцев={len(months)}, "
        f"упоминаний={sum(len(v) for v in mentions_by_month.values())}, "
        f"отчётов={len(report_files)}"
    )


if __name__ == "__main__":
    export()
