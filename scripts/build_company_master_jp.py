#!/usr/bin/env python3
from __future__ import annotations

"""Build company_master_jp from JPX listed issues and optional theme overlays.

This fills the previously empty company_master_jp table so HIZUMI can use
official TSE 33-sector metadata for relative valuation.

Inputs
------
- JPX_LISTED_ISSUES_CSV: data/universe/jpx_listed_issues_jp.csv
- THEME_OVERLAY_CSV: optional CSV with symbol/theme_tags/valuation_profile/manual flags.
  Default: data/universe/jp_forced_include_theme.csv if it exists.
- PRICE_DUCKDB_PATH: canonical DuckDB path.

DuckDB outputs
--------------
- company_master_jp
- company_master_jp_diag

The script is idempotent: it replaces company_master_jp from the latest JPX CSV.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("PRICE_DUCKDB_PATH", "data/cache/neon_tokyo_jp.duckdb"))
JPX_CSV = Path(os.getenv("JPX_LISTED_ISSUES_CSV", "data/universe/jpx_listed_issues_jp.csv"))
THEME_CSV = Path(os.getenv("THEME_OVERLAY_CSV", "data/universe/jp_forced_include_theme.csv"))
DIAG_JSON = Path(os.getenv("COMPANY_MASTER_DIAG_JSON", "site/data/japan/ai-arena/diagnostics/company-master-latest.json"))

FINANCIAL_33 = {"7050", "7100", "7150", "7200"}  # Banks, Securities, Insurance, Other Financing Business
CYCLICAL_33 = {"3050", "3100", "3200", "3250", "3300", "3350", "3400", "3450", "3500", "5200", "5250", "6050"}
INDUSTRIAL_QUALITY_33 = {"3600", "3650", "3700", "3750", "3800"}
TECH_GROWTH_33 = {"5250"}  # Information & Communication
HEALTHCARE_33 = {"3250"}  # Pharmaceutical
ASSET_VALUE_33 = {"8050", "8055"}  # Real Estate, Warehouse/Harbor Transportation

THEME_PROFILE_OVERRIDES = {
    "space": "space_robotics_growth",
    "robotics": "space_robotics_growth",
    "drone": "space_robotics_growth",
    "defense": "defense_industrial",
    "semiconductor": "industrial_quality",
    "semiconductor_equipment": "industrial_quality",
    "ai": "tech_growth",
    "ai_software": "tech_growth",
    "data_center": "power_infrastructure",
    "power_infrastructure": "power_infrastructure",
    "fintech": "tech_growth",
    "biotech": "biotech_high_risk",
}


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def norm_symbol(value: Any) -> str:
    s = "" if value is None else str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s.isdigit() and len(s) == 4:
        return f"{s}.T"
    return s.upper()


def safe_str(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def theme_list(value: Any) -> list[str]:
    raw = safe_str(value)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x).strip().lower() for x in parsed if str(x).strip()]
    except Exception:
        pass
    for sep in [";", "|", "/", ","]:
        raw = raw.replace(sep, ",")
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def base_profile(sector_33_code: str, sector_33_name: str) -> str:
    code = str(sector_33_code or "").zfill(4)
    name = str(sector_33_name or "")
    if code in FINANCIAL_33 or any(k in name for k in ["銀行", "証券", "保険", "その他金融"]):
        return "financial_value"
    if code in TECH_GROWTH_33 or "情報" in name or "通信" in name:
        return "tech_growth"
    if code in INDUSTRIAL_QUALITY_33 or any(k in name for k in ["機械", "電気機器", "精密機器"]):
        return "industrial_quality"
    if code in CYCLICAL_33 or any(k in name for k in ["化学", "鉄鋼", "非鉄", "鉱業", "石油", "建設", "海運"]):
        return "cyclical_value"
    if code in ASSET_VALUE_33 or any(k in name for k in ["不動産", "倉庫"]):
        return "asset_value"
    if "医薬" in name:
        return "healthcare_quality"
    return "general"


def load_theme_overlay(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["symbol", "theme_tags_json", "valuation_profile", "is_manual_theme_include"])
    df = pd.read_csv(path, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    if "symbol" not in df.columns:
        for c in ["ticker", "code", "local_code"]:
            if c in df.columns:
                df["symbol"] = df[c]
                break
    if "symbol" not in df.columns:
        return pd.DataFrame(columns=["symbol", "theme_tags_json", "valuation_profile", "is_manual_theme_include"])
    df["symbol"] = df["symbol"].map(norm_symbol)
    tag_col = next((c for c in ["theme_tags_json", "theme_tags", "themes", "theme"] if c in df.columns), None)
    profile_col = next((c for c in ["valuation_profile", "profile"] if c in df.columns), None)
    manual_col = next((c for c in ["is_manual_theme_include", "manual_theme_include", "forced_include", "force_include"] if c in df.columns), None)
    out = pd.DataFrame({"symbol": df["symbol"]})
    out["theme_tags_json"] = df[tag_col].map(lambda v: json.dumps(theme_list(v), ensure_ascii=False)) if tag_col else "[]"
    out["valuation_profile"] = df[profile_col].map(safe_str) if profile_col else ""
    out["is_manual_theme_include"] = df[manual_col].map(lambda v: str(v).lower() in {"1", "true", "yes", "y", "on"}) if manual_col else True
    return out.drop_duplicates("symbol", keep="last")


def main() -> int:
    db_path = resolve(DB_PATH)
    jpx_csv = resolve(JPX_CSV)
    theme_csv = resolve(THEME_CSV)
    diag_json = resolve(DIAG_JSON)
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB not found: {db_path}")
    if not jpx_csv.exists():
        raise FileNotFoundError(f"JPX normalized CSV not found: {jpx_csv}; run fetch_jpx_listed_issues_jp.py first")

    jpx = pd.read_csv(jpx_csv, dtype=str).fillna("")
    jpx["symbol"] = jpx["symbol"].map(norm_symbol)
    theme = load_theme_overlay(theme_csv)

    merged = jpx.merge(theme, on="symbol", how="left", suffixes=("", "_theme"))
    now = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for _, r in merged.iterrows():
        tags = theme_list(r.get("theme_tags_json"))
        profile = safe_str(r.get("valuation_profile")) or base_profile(safe_str(r.get("sector_33_code")), safe_str(r.get("sector_33_name")))
        for tag in tags:
            profile = THEME_PROFILE_OVERRIDES.get(tag, profile)
        rows.append({
            "symbol": norm_symbol(r.get("symbol")),
            "local_code": safe_str(r.get("local_code")),
            "company_name": safe_str(r.get("company_name")),
            "market": safe_str(r.get("market")),
            "sector_33_code": safe_str(r.get("sector_33_code")).zfill(4) if safe_str(r.get("sector_33_code")) else "",
            "sector_33_name": safe_str(r.get("sector_33_name")),
            "sector_17_code": safe_str(r.get("sector_17_code")).zfill(2) if safe_str(r.get("sector_17_code")) else "",
            "sector_17_name": safe_str(r.get("sector_17_name")),
            "size_code": safe_str(r.get("size_code")),
            "size_name": safe_str(r.get("size_name")),
            "theme_tags_json": json.dumps(tags, ensure_ascii=False),
            "valuation_profile": profile,
            "is_manual_theme_include": bool(r.get("is_manual_theme_include")) if not pd.isna(r.get("is_manual_theme_include")) else False,
            "source": "jpx_listed_issues+theme_overlay" if tags else "jpx_listed_issues",
            "updated_at": now,
        })

    out = pd.DataFrame(rows).drop_duplicates("symbol", keep="first")
    conn = duckdb.connect(str(db_path))
    conn.register("_company_master_jp", out)
    conn.execute("CREATE OR REPLACE TABLE company_master_jp AS SELECT * FROM _company_master_jp")
    conn.unregister("_company_master_jp")

    diag = {
        "schema_version": "company_master_jp_diag_v1",
        "generated_at": now,
        "duckdb": str(db_path),
        "source_csv": str(jpx_csv),
        "theme_csv": str(theme_csv) if theme_csv.exists() else None,
        "rows": int(len(out)),
        "unique_symbols": int(out["symbol"].nunique()),
        "sector_33_count": int(out["sector_33_code"].replace("", pd.NA).dropna().nunique()),
        "manual_theme_rows": int(out["is_manual_theme_include"].sum()),
        "valuation_profiles": out["valuation_profile"].value_counts().to_dict(),
    }
    diag_json.parent.mkdir(parents=True, exist_ok=True)
    diag_json.write_text(json.dumps(diag, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"company_master_jp rows={diag['rows']} unique_symbols={diag['unique_symbols']} sector_33_count={diag['sector_33_count']}")
    print(f"Wrote {diag_json}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
