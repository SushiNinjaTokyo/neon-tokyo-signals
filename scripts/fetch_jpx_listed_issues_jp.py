#!/usr/bin/env python3
from __future__ import annotations

"""Fetch JPX/TSE listed issues and normalize 33-sector metadata.

Inputs
------
- JPX_LISTED_ISSUES_URL: URL for JPX list of TSE-listed issues.
  Default: Japanese JPX data_j.xls.
- JPX_LISTED_ISSUES_LOCAL_PATH: optional local Excel/CSV path. If present,
  this takes precedence over network download.
- JPX_LISTED_ISSUES_OUT_CSV: normalized CSV output path.
- JPX_LISTED_ISSUES_OUT_JSON: optional normalized JSON output path.

Outputs
-------
- data/universe/jpx_listed_issues_jp.csv
- data/universe/jpx_listed_issues_jp.json

Design
------
The output is intentionally a flat CSV so the next step
`build_company_master_jp.py` can be deterministic and easy to debug.
The script does not mutate DuckDB directly.
"""

import json
import os
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JPX_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
OUT_CSV = Path(os.getenv("JPX_LISTED_ISSUES_OUT_CSV", "data/universe/jpx_listed_issues_jp.csv"))
OUT_JSON = Path(os.getenv("JPX_LISTED_ISSUES_OUT_JSON", "data/universe/jpx_listed_issues_jp.json"))
LOCAL_PATH = os.getenv("JPX_LISTED_ISSUES_LOCAL_PATH", "").strip()
URL = os.getenv("JPX_LISTED_ISSUES_URL", DEFAULT_JPX_URL).strip() or DEFAULT_JPX_URL


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_code(value: Any) -> str:
    raw = safe_str(value)
    if raw.endswith(".0"):
        raw = raw[:-2]
    raw = raw.zfill(4) if raw.isdigit() and len(raw) <= 4 else raw
    return raw


def normalize_ticker(local_code: Any) -> str:
    code = normalize_code(local_code)
    return f"{code}.T" if code and code.isdigit() and len(code) == 4 else code


def find_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized = {c: c.replace(" ", "").replace("　", "").lower() for c in columns}
    for cand in candidates:
        key = cand.replace(" ", "").replace("　", "").lower()
        for original, norm in normalized.items():
            if norm == key or key in norm:
                return original
    return None


def download_to_temp(url: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="jpx_listed_issues_")) / "jpx_listed_issues.xls"
    print(f"Downloading JPX listed issues: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 neon-tokyo-signals"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        tmp.write_bytes(resp.read())
    print(f"Downloaded {tmp} size={tmp.stat().st_size}")
    return tmp


def read_source(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path, dtype=str)
    # JPX currently publishes .xls. pandas needs xlrd for this; the workflow installs it.
    return pd.read_excel(path, dtype=str)


def normalize(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = [safe_str(c) for c in df.columns]
    cols = list(df.columns)

    col_date = find_column(cols, ["日付", "Effective Date", "Date"])
    col_code = find_column(cols, ["コード", "Local Code", "LocalCode"])
    col_name = find_column(cols, ["銘柄名", "Name", "Name (English)"])
    col_market = find_column(cols, ["市場・商品区分", "Section/Products", "Market"])
    col_33_code = find_column(cols, ["33業種コード", "33 Sector(Code)", "33 Sector Code"])
    col_33_name = find_column(cols, ["33業種区分", "33 Sector(name)", "33 Sector Name"])
    col_17_code = find_column(cols, ["17業種コード", "17 Sector(Code)", "17 Sector Code"])
    col_17_name = find_column(cols, ["17業種区分", "17 Sector(name)", "17 Sector Name"])
    col_size_code = find_column(cols, ["規模コード", "Size Code"])
    col_size_name = find_column(cols, ["規模区分", "Size", "Scale Category"])

    required = {
        "local_code": col_code,
        "name": col_name,
        "market": col_market,
        "sector_33_code": col_33_code,
        "sector_33_name": col_33_name,
        "sector_17_code": col_17_code,
        "sector_17_name": col_17_name,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise SystemExit(f"JPX listed issues file does not contain expected columns: {missing}; columns={cols}")

    rows: list[dict[str, Any]] = []
    generated_at = datetime.now(timezone.utc).isoformat()
    for _, r in df.iterrows():
        local_code = normalize_code(r.get(col_code))
        if not local_code or not local_code.isdigit() or len(local_code) != 4:
            continue
        sector_33_code = normalize_code(r.get(col_33_code))
        rows.append({
            "symbol": normalize_ticker(local_code),
            "local_code": local_code,
            "company_name": safe_str(r.get(col_name)),
            "market": safe_str(r.get(col_market)),
            "sector_33_code": sector_33_code,
            "sector_33_name": safe_str(r.get(col_33_name)),
            "sector_17_code": normalize_code(r.get(col_17_code)),
            "sector_17_name": safe_str(r.get(col_17_name)),
            "size_code": normalize_code(r.get(col_size_code)) if col_size_code else "",
            "size_name": safe_str(r.get(col_size_name)) if col_size_name else "",
            "effective_date": safe_str(r.get(col_date)) if col_date else "",
            "source": source,
            "updated_at": generated_at,
        })

    out = pd.DataFrame(rows).drop_duplicates(subset=["symbol"], keep="first")
    out = out.sort_values(["local_code"]).reset_index(drop=True)
    if out.empty:
        raise SystemExit("No listed equity rows were normalized from JPX source.")
    return out


def main() -> int:
    if LOCAL_PATH:
        source_path = resolve(Path(LOCAL_PATH))
        source_label = str(source_path)
        if not source_path.exists():
            raise FileNotFoundError(source_path)
    else:
        source_path = download_to_temp(URL)
        source_label = URL

    df = read_source(source_path)
    out = normalize(df, source_label)

    out_csv = resolve(OUT_CSV)
    out_json = resolve(OUT_JSON)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False, encoding="utf-8")
    out_json.write_text(json.dumps({
        "schema_version": "jpx_listed_issues_jp_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source_label,
        "row_count": int(len(out)),
        "items": out.to_dict(orient="records"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out_csv} rows={len(out)}")
    print(f"Wrote {out_json}")
    print("sector_33_count=", out["sector_33_code"].nunique())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
