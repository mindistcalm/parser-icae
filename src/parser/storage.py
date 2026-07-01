from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from parser.models import Mention, SourceType


class MentionStorage:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    url_normalized TEXT NOT NULL UNIQUE,
                    published_at TEXT,
                    source_type TEXT NOT NULL,
                    snippet TEXT,
                    search_query TEXT,
                    report_month TEXT NOT NULL,
                    found_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mentions_month ON mentions(report_month)"
            )

    def save_mentions(self, mentions: list[Mention], report_month: str) -> int:
        inserted = 0
        with self._connect() as conn:
            for m in mentions:
                try:
                    conn.execute(
                        """
                        INSERT INTO mentions (
                            source_name, title, url, url_normalized,
                            published_at, source_type, snippet,
                            search_query, report_month, found_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            m.source_name,
                            m.title,
                            m.url,
                            m.url_normalized,
                            m.published_at.isoformat() if m.published_at else None,
                            m.source_type.value,
                            m.snippet,
                            m.search_query,
                            report_month,
                            m.found_at.isoformat(),
                        ),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass
        return inserted

    def get_mentions_for_month(self, report_month: str) -> list[Mention]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM mentions
                WHERE report_month = ?
                ORDER BY published_at DESC NULLS LAST, source_name
                """,
                (report_month,),
            ).fetchall()

        result: list[Mention] = []
        for row in rows:
            published = (
                datetime.fromisoformat(row["published_at"])
                if row["published_at"]
                else None
            )
            result.append(
                Mention(
                    source_name=row["source_name"],
                    title=row["title"],
                    url=row["url"],
                    published_at=published,
                    source_type=SourceType(row["source_type"]),
                    snippet=row["snippet"] or "",
                    search_query=row["search_query"] or "",
                    found_at=datetime.fromisoformat(row["found_at"]),
                )
            )
        return result

    def count_for_month(self, report_month: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM mentions WHERE report_month = ?",
                (report_month,),
            ).fetchone()
        return int(row["cnt"]) if row else 0

    def list_months(self) -> list[dict[str, int | str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT report_month, COUNT(*) AS cnt
                FROM mentions
                GROUP BY report_month
                ORDER BY report_month DESC
                """
            ).fetchall()
        return [{"month": row["report_month"], "count": row["cnt"]} for row in rows]

