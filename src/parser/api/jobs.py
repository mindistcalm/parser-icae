from __future__ import annotations

import threading
import uuid
from datetime import datetime

from parser.api.schemas import JobOut, JobStatus
from parser.config import load_config
from parser.engine import SearchEngine, month_label
from parser.report import ReportGenerator


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobOut] = {}
        self._lock = threading.Lock()

    def get(self, job_id: str) -> JobOut | None:
        with self._lock:
            return self._jobs.get(job_id)

    def start_run(self, year: int, month: int) -> str:
        job_id = str(uuid.uuid4())
        month_str = month_label(year, month)
        job = JobOut(
            id=job_id,
            status=JobStatus.PENDING,
            month=month_str,
            started_at=datetime.now(),
        )
        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(
            target=self._run_job,
            args=(job_id, year, month),
            daemon=True,
        )
        thread.start()
        return job_id

    def _update(self, job_id: str, **kwargs) -> None:
        with self._lock:
            job = self._jobs[job_id]
            self._jobs[job_id] = job.model_copy(update=kwargs)

    def _append_log(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            logs = [*job.logs, message]
            self._jobs[job_id] = job.model_copy(update={"logs": logs})

    def _run_job(self, job_id: str, year: int, month: int) -> None:
        self._update(job_id, status=JobStatus.RUNNING)
        try:
            config = load_config()
            engine = SearchEngine(config)

            def on_progress(msg: str) -> None:
                self._append_log(job_id, msg)

            self._append_log(job_id, f"Старт поиска за {month_label(year, month)}")
            mentions = engine.collect(year, month, verbose=False, on_progress=on_progress)

            generator = ReportGenerator(config)
            xlsx_path, html_path = generator.generate(mentions, year, month)

            self._update(
                job_id,
                status=JobStatus.COMPLETED,
                mentions_count=len(mentions),
                report_xlsx=xlsx_path.name,
                report_html=html_path.name,
                finished_at=datetime.now(),
            )
            self._append_log(job_id, "Готово!")
        except Exception as exc:
            self._update(
                job_id,
                status=JobStatus.FAILED,
                error=str(exc),
                finished_at=datetime.now(),
            )
            self._append_log(job_id, f"Ошибка: {exc}")


job_manager = JobManager()
