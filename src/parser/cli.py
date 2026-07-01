from __future__ import annotations

import re
from datetime import date

import typer

from parser.config import load_config
from parser.engine import SearchEngine, month_label, previous_month
from parser.report import ReportGenerator

app = typer.Typer(
    name="icae-parser",
    help="Мониторинг упоминаний ИЦАЭ Томска в интернете",
    no_args_is_help=True,
)


def _parse_month(value: str | None) -> tuple[int, int]:
    if value is None:
        return previous_month()
    match = re.fullmatch(r"(\d{4})-(\d{2})", value.strip())
    if not match:
        raise typer.BadParameter("Формат месяца: YYYY-MM, например 2025-06")
    year, month = int(match.group(1)), int(match.group(2))
    if month < 1 or month > 12:
        raise typer.BadParameter("Месяц должен быть от 01 до 12")
    return year, month


@app.command("search")
def search_cmd(
    month: str = typer.Option(
        None,
        "--month",
        "-m",
        help="Месяц отчёта (YYYY-MM). По умолчанию — прошлый месяц.",
    ),
) -> None:
    """Собрать упоминания за указанный месяц."""
    year, mon = _parse_month(month)
    typer.echo(f"Поиск упоминаний за {month_label(year, mon)}...\n")

    engine = SearchEngine()
    engine.collect(year, mon)


@app.command("report")
def report_cmd(
    month: str = typer.Option(
        None,
        "--month",
        "-m",
        help="Месяц отчёта (YYYY-MM). По умолчанию — прошлый месяц.",
    ),
) -> None:
    """Сформировать отчёт по уже собранным данным."""
    year, mon = _parse_month(month)
    engine = SearchEngine()
    mentions = engine.get_stored(year, mon)

    if not mentions:
        typer.echo(
            f"В базе нет данных за {month_label(year, mon)}. "
            "Сначала выполните: icae-parser search --month ..."
        )
        raise typer.Exit(code=1)

    generator = ReportGenerator()
    xlsx_path, html_path = generator.generate(mentions, year, mon)

    typer.echo(f"Отчёт сформирован ({len(mentions)} записей):")
    typer.echo(f"  Excel: {xlsx_path}")
    typer.echo(f"  HTML:  {html_path}")


@app.command("run")
def run_cmd(
    month: str = typer.Option(
        None,
        "--month",
        "-m",
        help="Месяц отчёта (YYYY-MM). По умолчанию — прошлый месяц.",
    ),
) -> None:
    """Поиск + формирование отчёта (основная команда в конце месяца)."""
    year, mon = _parse_month(month)
    typer.echo(f"=== Мониторинг ИЦАЭ за {month_label(year, mon)} ===\n")

    engine = SearchEngine()
    mentions = engine.collect(year, mon)

    generator = ReportGenerator()
    xlsx_path, html_path = generator.generate(mentions, year, mon)

    typer.echo("\nОтчёт:")
    typer.echo(f"  Excel: {xlsx_path}")
    typer.echo(f"  HTML:  {html_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
