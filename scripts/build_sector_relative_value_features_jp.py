#!/usr/bin/env python3
from __future__ import annotations

"""Build 33-sector relative valuation features for HIZUMI.

This script enriches value_features_daily without requiring a destructive rewrite
of the existing value feature pipeline.

It creates:
- sector_33_valuation_medians
- value_features_sector_relative_jp

It also ALTERs value_features_daily to add sector-relative columns when the table
exists, then updates those columns by ticker/date.  Existing scoring columns are
not overwritten.
"""

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("PRICE_DUCKDB_PATH", "data/cache/neon_tokyo_jp.duckdb"))
DIAG_JSON = Path(os.getenv("SECTOR_RELATIVE_VALUE_DIAG_JSON", "site/data/japan/ai-arena/diagnostics/sector-relative-value-latest.json"))
MIN_SECTOR_SAMPLE = int(os.getenv("SECTOR_RELATIVE_MIN_SAMPLE", "5"))


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def table_exists(conn: duckdb.DuckDBPyConnection, table: str) -> bool:
    return bool(conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [table]).fetchone()[0])


def table_columns(conn: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    return {r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()}


def add_col(conn: duckdb.DuckDBPyConnection, table: str, col: str, typ: str) -> None:
    if col not in table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if math.isnan(v) or math.isinf(v):
        return 0.0
    return max(lo, min(hi, v))


def ratio_score(ratio: Any) -> float:
    try:
        r = float(ratio)
    except Exception:
        return 0.0
    if r <= 0 or math.isnan(r) or math.isinf(r):
        return 0.0
    # ratio=1.0 means sector median. ratio>=1.8 is strongly cheap vs sector.
    return clamp((r - 0.75) / (1.80 - 0.75))


def quality_rel_score(company: Any, median: Any) -> float:
    try:
        c = float(company)
        m = float(median)
    except Exception:
        return 0.5
    if math.isnan(c) or math.isnan(m):
        return 0.5
    # Better than sector median is good; do not over-reward outliers.
    return clamp(0.5 + (c - m) / 30.0)


def safe_div(a: Any, b: Any) -> float | None:
    try:
        x = float(a)
        y = float(b)
        if x <= 0 or y <= 0 or math.isnan(x) or math.isnan(y):
            return None
        return x / y
    except Exception:
        return None


def main() -> int:
    db_path = resolve(DB_PATH)
    diag_json = resolve(DIAG_JSON)
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    conn = duckdb.connect(str(db_path))
    for t in ["company_master_jp", "fundamentals_latest_jp"]:
        if not table_exists(conn, t):
            raise SystemExit(f"{t} table does not exist. Run build_company_master_jp.py and fetch_fundamentals_jp.py first.")

    fcols = table_columns(conn, "fundamentals_latest_jp")
    symbol_col = "symbol" if "symbol" in fcols else "ticker" if "ticker" in fcols else None
    if not symbol_col:
        raise SystemExit("fundamentals_latest_jp must have symbol or ticker")

    fundamentals = conn.execute(f"""
        SELECT
          CAST(f.{symbol_col} AS VARCHAR) AS symbol,
          c.sector_33_code,
          c.sector_33_name,
          c.valuation_profile,
          c.theme_tags_json,
          f.per,
          f.pbr,
          f.psr,
          f.roe_pct,
          f.roa_pct,
          f.operating_margin_pct,
          f.market_cap_jpy
        FROM fundamentals_latest_jp f
        LEFT JOIN company_master_jp c ON CAST(f.{symbol_col} AS VARCHAR) = c.symbol
        WHERE c.sector_33_code IS NOT NULL AND c.sector_33_code <> ''
    """).df()
    if fundamentals.empty:
        raise SystemExit("No fundamentals rows could be joined to company_master_jp sector_33_code")

    valid = fundamentals.copy()
    med_rows=[]
    for (code, name), g in valid.groupby(["sector_33_code", "sector_33_name"], dropna=False):
        def med(col: str):
            s = pd.to_numeric(g[col], errors="coerce")
            s = s[(s > 0) & s.notna()]
            return float(s.median()) if len(s) else None
        def med_any(col: str):
            s = pd.to_numeric(g[col], errors="coerce").dropna()
            return float(s.median()) if len(s) else None
        med_rows.append({
            "sector_33_code": str(code),
            "sector_33_name": str(name),
            "sample_count": int(len(g)),
            "median_per": med("per"),
            "median_pbr": med("pbr"),
            "median_psr": med("psr"),
            "median_roe_pct": med_any("roe_pct"),
            "median_roa_pct": med_any("roa_pct"),
            "median_operating_margin_pct": med_any("operating_margin_pct"),
            "median_market_cap_jpy": med("market_cap_jpy"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    med = pd.DataFrame(med_rows)
    conn.register("_sector_medians", med)
    conn.execute("CREATE OR REPLACE TABLE sector_33_valuation_medians AS SELECT * FROM _sector_medians")
    conn.unregister("_sector_medians")

    merged = fundamentals.merge(med, on=["sector_33_code", "sector_33_name"], how="left")
    rows=[]
    now=datetime.now(timezone.utc).isoformat()
    for _, r in merged.iterrows():
        per_ratio = safe_div(r.get("median_per"), r.get("per"))
        pbr_ratio = safe_div(r.get("median_pbr"), r.get("pbr"))
        psr_ratio = safe_div(r.get("median_psr"), r.get("psr"))
        per_s = ratio_score(per_ratio) if per_ratio is not None else 0.0
        pbr_s = ratio_score(pbr_ratio) if pbr_ratio is not None else 0.0
        psr_s = ratio_score(psr_ratio) if psr_ratio is not None else 0.0
        q_roe = quality_rel_score(r.get("roe_pct"), r.get("median_roe_pct"))
        q_opm = quality_rel_score(r.get("operating_margin_pct"), r.get("median_operating_margin_pct"))
        sample = int(r.get("sample_count") or 0)
        confidence = 1.0 if sample >= 10 else 0.65 if sample >= MIN_SECTOR_SAMPLE else 0.35
        valuation_profile = str(r.get("valuation_profile") or "general")
        if valuation_profile == "financial_value":
            valuation = 0.15 * per_s + 0.60 * pbr_s + 0.05 * psr_s + 0.20 * q_roe
        elif valuation_profile in {"tech_growth", "space_robotics_growth"}:
            valuation = 0.15 * per_s + 0.15 * pbr_s + 0.45 * psr_s + 0.25 * ((q_roe + q_opm) / 2)
        elif valuation_profile in {"industrial_quality", "defense_industrial", "power_infrastructure"}:
            valuation = 0.25 * per_s + 0.20 * pbr_s + 0.20 * psr_s + 0.35 * ((q_roe + q_opm) / 2)
        else:
            valuation = 0.35 * per_s + 0.35 * pbr_s + 0.15 * psr_s + 0.15 * ((q_roe + q_opm) / 2)
        rows.append({
            "symbol": str(r.get("symbol")),
            "sector_33_code": str(r.get("sector_33_code") or ""),
            "sector_33_name": str(r.get("sector_33_name") or ""),
            "valuation_profile": valuation_profile,
            "theme_tags_json": str(r.get("theme_tags_json") or "[]"),
            "sector_relative_per_discount": per_ratio,
            "sector_relative_pbr_discount": pbr_ratio,
            "sector_relative_psr_discount": psr_ratio,
            "sector_relative_valuation_score": round(clamp(valuation) * confidence, 6),
            "sector_relative_quality_score": round(clamp((q_roe + q_opm) / 2), 6),
            "sector_relative_value_confidence": round(confidence, 6),
            "updated_at": now,
        })
    overlay = pd.DataFrame(rows)
    conn.register("_sector_relative", overlay)
    conn.execute("CREATE OR REPLACE TABLE value_features_sector_relative_jp AS SELECT * FROM _sector_relative")
    conn.unregister("_sector_relative")

    if table_exists(conn, "value_features_daily"):
        additions = {
            "sector_33_code": "VARCHAR",
            "sector_33_name": "VARCHAR",
            "valuation_profile": "VARCHAR",
            "theme_tags_json": "VARCHAR",
            "sector_relative_per_discount": "DOUBLE",
            "sector_relative_pbr_discount": "DOUBLE",
            "sector_relative_psr_discount": "DOUBLE",
            "sector_relative_valuation_score": "DOUBLE",
            "sector_relative_quality_score": "DOUBLE",
            "sector_relative_value_confidence": "DOUBLE",
        }
        for c, typ in additions.items():
            add_col(conn, "value_features_daily", c, typ)
        conn.execute("""
            UPDATE value_features_daily vf
            SET
              sector_33_code = sr.sector_33_code,
              sector_33_name = sr.sector_33_name,
              valuation_profile = sr.valuation_profile,
              theme_tags_json = sr.theme_tags_json,
              sector_relative_per_discount = sr.sector_relative_per_discount,
              sector_relative_pbr_discount = sr.sector_relative_pbr_discount,
              sector_relative_psr_discount = sr.sector_relative_psr_discount,
              sector_relative_valuation_score = sr.sector_relative_valuation_score,
              sector_relative_quality_score = sr.sector_relative_quality_score,
              sector_relative_value_confidence = sr.sector_relative_value_confidence
            FROM value_features_sector_relative_jp sr
            WHERE vf.ticker = sr.symbol
        """)
        updated_rows = int(conn.execute("SELECT COUNT(*) FROM value_features_daily WHERE sector_relative_valuation_score IS NOT NULL").fetchone()[0])
    else:
        updated_rows = 0

    diag = {
        "schema_version": "sector_relative_value_features_jp_v1",
        "generated_at": now,
        "duckdb": str(db_path),
        "fundamentals_join_rows": int(len(fundamentals)),
        "sector_count": int(med["sector_33_code"].nunique()),
        "overlay_rows": int(len(overlay)),
        "value_features_daily_rows_with_sector_relative": updated_rows,
        "min_sector_sample": MIN_SECTOR_SAMPLE,
    }
    diag_json = resolve(DIAG_JSON)
    diag_json.parent.mkdir(parents=True, exist_ok=True)
    diag_json.write_text(json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(diag, ensure_ascii=False, indent=2))
    conn.close()
    return 0 if len(overlay) > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
