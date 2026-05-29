from __future__ import annotations

"""Trading-calendar helpers for the AI Arena season engine.

The project does not maintain a separate official TSE holiday calendar. For the
simulation engine we therefore derive the tradable calendar from rows that exist
in DuckDB prices_daily. This has two practical advantages:

1. The engine only simulates dates for which it can actually mark positions.
2. Historical rebuilds remain reproducible even when a data provider misses a
   holiday or has a delayed market-pulse ETF date.

When a strict exchange calendar is added later, this module is the only place
that should need to change.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import duckdb


@dataclass(frozen=True)
class SeasonDates:
    year: int
    season_start: date
    season_end: date
    first_trading_date: date | None
    last_trading_date: date | None
    trading_dates: list[date]


def parse_date(value: str | date | datetime | None) -> date | None:
    """Parse an ISO date-like value safely."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)[:10]).date()


def today_jst_date() -> date:
    """Return today's date in the environment's local time.

    GitHub Actions runners are UTC, but the site is updated after the Japan
    session. For year-selection purposes UTC and JST only differ around New Year
    for a few hours. The workflow can pass explicit END_DATE when exactness is
    required.
    """
    return datetime.utcnow().date()


def fetch_trading_dates(
    conn: duckdb.DuckDBPyConnection,
    start_date: str | date,
    end_date: str | date,
    *,
    exclude_market_pulse_only_dates: bool = True,
) -> list[date]:
    """Return sorted trading dates from prices_daily.

    If exclude_market_pulse_only_dates is True, dates that contain only ETF or
    market pulse rows are excluded by joining to universe_master and keeping
    ordinary equities when possible. This avoids using 1306.T/1321.T dates that
    are newer than equity quotes.
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    if start is None or end is None:
        return []

    if exclude_market_pulse_only_dates:
        rows = conn.execute(
            """
            SELECT p.date, COUNT(*) AS n
            FROM prices_daily p
            LEFT JOIN universe_master u USING (ticker)
            WHERE p.date BETWEEN ? AND ?
              AND COALESCE(LOWER(u.asset_type), 'equity') = 'equity'
            GROUP BY p.date
            HAVING COUNT(*) > 0
            ORDER BY p.date
            """,
            [start, end],
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT DISTINCT date
            FROM prices_daily
            WHERE date BETWEEN ? AND ?
            ORDER BY date
            """,
            [start, end],
        ).fetchall()
    return [parse_date(r[0]) for r in rows if parse_date(r[0]) is not None]


def previous_trading_date(trading_dates: list[date], current: date) -> date | None:
    prior = [d for d in trading_dates if d < current]
    return prior[-1] if prior else None


def next_trading_date(trading_dates: list[date], current: date) -> date | None:
    for d in trading_dates:
        if d > current:
            return d
    return None


def trading_days_until_year_end(trading_dates: list[date], current: date) -> int:
    """Count tradable dates remaining after current within the same year."""
    return sum(1 for d in trading_dates if d > current and d.year == current.year)


def build_season_dates(
    conn: duckdb.DuckDBPyConnection,
    year: int,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> SeasonDates:
    season_start = parse_date(start_date) or date(year, 1, 1)
    season_end = parse_date(end_date) or date(year, 12, 31)
    dates = fetch_trading_dates(conn, season_start, season_end)
    return SeasonDates(
        year=year,
        season_start=season_start,
        season_end=season_end,
        first_trading_date=dates[0] if dates else None,
        last_trading_date=dates[-1] if dates else None,
        trading_dates=dates,
    )


def downsample_points(items: list[dict], max_points: int, *, date_key: str = "date") -> list[dict]:
    """Downsample chronological chart points without changing endpoints."""
    if max_points <= 0 or len(items) <= max_points:
        return items
    if len(items) <= 2:
        return items
    step = (len(items) - 1) / float(max_points - 1)
    picked = []
    used = set()
    for i in range(max_points):
        idx = round(i * step)
        if idx not in used and 0 <= idx < len(items):
            picked.append(items[idx])
            used.add(idx)
    if picked and picked[-1] != items[-1]:
        picked[-1] = items[-1]
    return picked
