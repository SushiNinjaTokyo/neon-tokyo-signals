from __future__ import annotations

"""Run management for calendar-year AI Arena seasons.

The key design choice is that every visible season is identified by run_id.
This allows the user to rebuild 2026 with a new rule set without overwriting the
old result. The display layer then points to the chosen run through
arena_display_runs.
"""

from dataclasses import dataclass
from datetime import datetime, date
import hashlib
import json
from pathlib import Path
from typing import Any

import duckdb
import yaml


@dataclass(frozen=True)
class RunConfig:
    run_id: str
    year: int
    run_type: str
    start_date: date
    end_date: date
    initial_capital_jpy: float
    share_lot_size: int
    strategy_rules_version: str
    portfolio_rules_version: str
    rules_hash: str


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def rules_hash_for_files(paths: list[str | Path]) -> str:
    """Return a stable hash of the exact rules used for a run."""
    h = hashlib.sha256()
    for p in paths:
        path = Path(p)
        h.update(str(path).encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()[:16]


def next_rebuild_run_id(conn: duckdb.DuckDBPyConnection, year: int) -> str:
    prefix = f"arena_jp_rebuild_{year}_v"
    rows = conn.execute(
        "SELECT run_id FROM arena_simulation_runs WHERE year = ? AND run_id LIKE ?",
        [year, prefix + "%"],
    ).fetchall()
    max_n = 0
    for (rid,) in rows:
        try:
            max_n = max(max_n, int(str(rid).rsplit("_v", 1)[1]))
        except Exception:
            pass
    return f"{prefix}{max_n + 1:03d}"


def default_live_run_id(year: int) -> str:
    return f"arena_jp_live_{year}"


def create_or_replace_run(
    conn: duckdb.DuckDBPyConnection,
    cfg: RunConfig,
    *,
    reset_run: bool,
    note: str = "",
) -> None:
    """Create run metadata and optionally clear all run-scoped tables."""
    if reset_run:
        for table in [
            "arena_orders",
            "arena_open_positions",
            "arena_trades",
            "arena_equity_curve",
            "arena_yearly_rankings",
            "arena_monthly_rankings",
            "arena_trade_rankings",
        ]:
            conn.execute(f"DELETE FROM {table} WHERE run_id = ?", [cfg.run_id])
        conn.execute("DELETE FROM arena_simulation_runs WHERE run_id = ?", [cfg.run_id])

    now = datetime.utcnow()
    existing = conn.execute("SELECT COUNT(*) FROM arena_simulation_runs WHERE run_id = ?", [cfg.run_id]).fetchone()[0]
    if existing:
        conn.execute(
            """
            UPDATE arena_simulation_runs
            SET updated_at = ?, source_data_end_date = ?, note = ?
            WHERE run_id = ?
            """,
            [now, cfg.end_date, note, cfg.run_id],
        )
        return

    conn.execute(
        """
        INSERT INTO arena_simulation_runs (
          run_id, year, run_type, status, start_date, end_date,
          initial_capital_jpy, share_lot_size,
          reset_positions_at_year_start, force_close_positions_at_year_end,
          strategy_rules_version, portfolio_rules_version, rules_hash,
          source_data_start_date, source_data_end_date,
          parent_run_id, promoted_from_run_id,
          is_display_run, is_official, rules_locked,
          created_at, updated_at, frozen_at, note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            cfg.run_id,
            cfg.year,
            cfg.run_type,
            "active",
            cfg.start_date,
            cfg.end_date,
            cfg.initial_capital_jpy,
            cfg.share_lot_size,
            True,
            True,
            cfg.strategy_rules_version,
            cfg.portfolio_rules_version,
            cfg.rules_hash,
            cfg.start_date,
            cfg.end_date,
            None,
            None,
            False,
            False,
            False,
            now,
            now,
            None,
            note,
        ],
    )


def promote_display_run(
    conn: duckdb.DuckDBPyConnection,
    *,
    year: int,
    run_id: str,
    display_type: str = "current",
    note: str = "",
) -> None:
    """Make run_id the display source for the selected year."""
    now = datetime.utcnow()
    conn.execute(
        "DELETE FROM arena_display_runs WHERE year = ? AND display_type = ?",
        [year, display_type],
    )
    conn.execute(
        """
        INSERT INTO arena_display_runs (year, display_type, run_id, status, selected_at, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [year, display_type, run_id, "active_display", now, note],
    )
    conn.execute("UPDATE arena_simulation_runs SET is_display_run = FALSE WHERE year = ?", [year])
    conn.execute("UPDATE arena_simulation_runs SET is_display_run = TRUE, updated_at = ? WHERE run_id = ?", [now, run_id])


def resolve_display_run(conn: duckdb.DuckDBPyConnection, year: int, display_type: str = "current") -> str | None:
    row = conn.execute(
        """
        SELECT run_id FROM arena_display_runs
        WHERE year = ? AND display_type = ? AND status = 'active_display'
        ORDER BY selected_at DESC
        LIMIT 1
        """,
        [year, display_type],
    ).fetchone()
    if row:
        return str(row[0])
    row = conn.execute(
        """
        SELECT run_id FROM arena_simulation_runs
        WHERE year = ?
        ORDER BY is_display_run DESC, updated_at DESC, created_at DESC
        LIMIT 1
        """,
        [year],
    ).fetchone()
    return str(row[0]) if row else None
