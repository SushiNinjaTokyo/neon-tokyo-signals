from __future__ import annotations

"""Company/fundamental helpers for AI Arena Signals.

This module is intentionally conservative. It never invents valuation numbers;
if DuckDB has no fundamentals for a ticker, the caller receives None/N/A values.
A future EDINET/TDnet integration can populate fundamentals_latest_jp without
changing the Signals page renderer.
"""

from datetime import datetime
from typing import Any

import duckdb


def fetch_company_snapshot(conn: duckdb.DuckDBPyConnection, ticker: str) -> dict[str, Any]:
    company = conn.execute(
        """
        SELECT ticker, code, name_en, name_ja, market, sector, industry, description_en, website
        FROM company_master_jp
        WHERE ticker = ?
        LIMIT 1
        """,
        [ticker],
    ).fetchone()
    if company:
        ccols = ["ticker", "code", "name_en", "name_ja", "market", "sector", "industry", "description_en", "website"]
        out = dict(zip(ccols, company))
    else:
        row = conn.execute(
            "SELECT ticker, name, market, sector, industry FROM universe_master WHERE ticker = ? LIMIT 1",
            [ticker],
        ).fetchone()
        if row:
            out = {"ticker": row[0], "code": str(row[0]).replace(".T", ""), "name_en": row[1], "name_ja": row[1], "market": row[2], "sector": row[3], "industry": row[4], "description_en": "", "website": ""}
        else:
            out = {"ticker": ticker, "code": str(ticker).replace(".T", ""), "name_en": ticker, "name_ja": ticker, "market": "", "sector": "", "industry": "", "description_en": "", "website": ""}

    f = conn.execute(
        """
        SELECT fiscal_period, market_cap_jpy, revenue_jpy, operating_profit_jpy, net_income_jpy,
               equity_jpy, roe_pct, roa_pct, per, pbr, psr, dividend_yield_pct, updated_at
        FROM fundamentals_latest_jp
        WHERE ticker = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        [ticker],
    ).fetchone()
    if f:
        fcols = ["fiscal_period", "market_cap_jpy", "revenue_jpy", "operating_profit_jpy", "net_income_jpy", "equity_jpy", "roe_pct", "roa_pct", "per", "pbr", "psr", "dividend_yield_pct", "updated_at"]
        out["fundamentals"] = dict(zip(fcols, f))
    else:
        out["fundamentals"] = {}
    return out


def upsert_company_from_universe(conn: duckdb.DuckDBPyConnection) -> int:
    """Populate company_master_jp from universe_master as a safe baseline."""
    now = datetime.utcnow()
    conn.execute(
        """
        INSERT INTO company_master_jp
        SELECT ticker, code, name AS name_ja, name AS name_en, market, sector, industry,
               '' AS description_en, '' AS website, ? AS updated_at
        FROM universe_master
        WHERE ticker IS NOT NULL
          AND ticker NOT IN (SELECT ticker FROM company_master_jp)
        """,
        [now],
    )
    return int(conn.execute("SELECT COUNT(*) FROM company_master_jp").fetchone()[0])
