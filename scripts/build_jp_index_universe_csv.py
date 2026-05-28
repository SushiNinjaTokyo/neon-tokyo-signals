#!/usr/bin/env python3
"""
Build a de-duplicated Japanese equity universe CSV for Neon Tokyo Signals.

Sources:
- TOPIX Component Stocks Weight CSV -> TOPIX 500 = Core30 + Large70 + Mid400
- JPX Prime 150 Constituents List with Weight CSV
- TSE Growth Market 250 constituent PDF
- JPX Start-Up Acceleration 100 constituent PDF

Outputs:
- data/universe/jp_index_universe.csv
- site/data/japan/universe/jp_index_universe.csv
- site/data/japan/universe/jp_index_universe.json
- site/data/japan/universe/diagnostics.json

Design notes:
- This script intentionally does NOT rely on yfinance for membership.
- Duplicate tickers are collapsed into one row with source flags.
- The first source in priority order is retained as primary_source.
- TSE Growth Market 250 and Startup 100 PDFs are parsed with PyMuPDF if available.
  Install in GitHub Actions with: python -m pip install pymupdf
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

TOPIX_WEIGHT_URL = "https://www.jpx.co.jp/automation/markets/indices/topix/files/topixweight_j.csv"
JPX_PRIME150_WEIGHT_URL = "https://www.jpx.co.jp/automation/markets/indices/jpx-prime150/files/jpxprime150weight_j.csv"
GROWTH250_PDF_URL = "https://www.jpx.co.jp/english/markets/indices/line-up/files/e_mei2_31_mothers.pdf"
STARTUP100_PDF_URL = "https://www.jpx.co.jp/english/markets/indices/line-up/files/e_mei2_42_SU100.pdf"

SOURCE_PRIORITY = [
    "topix500",
    "jpx_prime150",
    "growth250",
    "jpx_startup100",
]

SOURCE_LABELS = {
    "topix500": "TOPIX 500",
    "jpx_prime150": "JPX Prime 150",
    "growth250": "TSE Growth Market 250",
    "jpx_startup100": "JPX Startup 100",
}

TOPIX500_CLASSES = {"TOPIX Core30", "TOPIX Large70", "TOPIX Mid400"}
CODE_RE = re.compile(r"^(?:\d{4}|\d{3}A)$")
YEAR_LIKE_CODE_RE = re.compile(r"^(?:19|20)\d{2}$")
PDF_CODE_BLOCKLIST = {"2023", "2024", "2025", "2026", "2027", "2028", "2029"}


@dataclass
class Security:
    code: str
    ticker: str
    name: str = ""
    sector: str = ""
    market: str = ""
    sources: Dict[str, bool] = field(default_factory=dict)
    source_details: Dict[str, str] = field(default_factory=dict)
    source_urls: Dict[str, str] = field(default_factory=dict)

    def merge(self, other: "Security") -> None:
        if not self.name and other.name:
            self.name = other.name
        if not self.sector and other.sector:
            self.sector = other.sector
        if not self.market and other.market:
            self.market = other.market
        self.sources.update(other.sources)
        self.source_details.update({k: v for k, v in other.source_details.items() if v})
        self.source_urls.update({k: v for k, v in other.source_urls.items() if v})

    @property
    def primary_source(self) -> str:
        for src in SOURCE_PRIORITY:
            if self.sources.get(src):
                return src
        return "unknown"

    def as_row(self) -> Dict[str, str]:
        source_list = [src for src in SOURCE_PRIORITY if self.sources.get(src)]
        return {
            "ticker": self.ticker,
            "code": self.code,
            "name": self.name,
            "market": self.market,
            "sector": self.sector,
            "primary_source": self.primary_source,
            "sources": "|".join(source_list),
            "is_topix500": "1" if self.sources.get("topix500") else "0",
            "is_jpx_prime150": "1" if self.sources.get("jpx_prime150") else "0",
            "is_growth250": "1" if self.sources.get("growth250") else "0",
            "is_jpx_startup100": "1" if self.sources.get("jpx_startup100") else "0",
            "source_detail": "|".join(
                f"{src}:{self.source_details.get(src, '')}" for src in source_list
            ),
            "source_url": "|".join(
                self.source_urls.get(src, "") for src in source_list if self.source_urls.get(src)
            ),
        }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs(paths: Iterable[Path]) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 NeonTokyoSignals/1.0 (+https://neon-tokyo-signals.vercel.app/)"
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read()


def decode_csv_bytes(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp932", "shift_jis", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def normalize_code(code: str) -> str:
    c = str(code).strip().upper()
    c = re.sub(r"\.0$", "", c)
    return c


def make_ticker(code: str) -> str:
    return f"{normalize_code(code)}.T"


def is_valid_code_token(code: str, *, source: str = "", name: str = "") -> bool:
    """Validate a security-code token extracted from official files.

    JPX PDF tables sometimes contain dates/years near the table body. A simple
    `four-digit` regex can accidentally treat `2025` as a ticker. CSV sources are
    stricter and usually have explicit code columns, but PDF sources need extra
    guards.
    """
    c = normalize_code(code)
    if not c or not CODE_RE.match(c):
        return False
    if source in {"growth250", "jpx_startup100", "pdf"}:
        if c in PDF_CODE_BLOCKLIST or YEAR_LIKE_CODE_RE.match(c):
            return False
        n = normalize_text(name).upper()
        if not n or n in {c, f"{c}.T", f"{c}.JP"}:
            return False
    return True


def normalize_text(s: object) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s).strip())


def read_csv_dicts_from_url(url: str) -> Tuple[List[Dict[str, str]], str]:
    raw = fetch_bytes(url)
    text = decode_csv_bytes(raw)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    return rows, text


def pick_col(row: Dict[str, str], candidates: Sequence[str]) -> str:
    # Exact first
    for c in candidates:
        if c in row:
            return row.get(c, "")
    # Fuzzy fallback
    keys = list(row.keys())
    for c in candidates:
        for k in keys:
            if c in k:
                return row.get(k, "")
    return ""


def build_topix500() -> List[Security]:
    rows, _ = read_csv_dicts_from_url(TOPIX_WEIGHT_URL)
    out: List[Security] = []
    for row in rows:
        code = normalize_code(pick_col(row, ["コード", "Code"]))
        name = normalize_text(pick_col(row, ["銘柄名", "銘柄名称", "Name"]))
        sector = normalize_text(pick_col(row, ["業種", "Sector"]))
        cls = normalize_text(pick_col(row, ["ニューインデックス区分", "New Index Series", "Index Classification"]))
        if not code or not CODE_RE.match(code):
            continue
        if cls not in TOPIX500_CLASSES:
            continue
        out.append(
            Security(
                code=code,
                ticker=make_ticker(code),
                name=name,
                sector=sector,
                market="Prime/TOPIX",
                sources={"topix500": True},
                source_details={"topix500": cls},
                source_urls={"topix500": TOPIX_WEIGHT_URL},
            )
        )
    return out


def build_jpx_prime150() -> List[Security]:
    rows, _ = read_csv_dicts_from_url(JPX_PRIME150_WEIGHT_URL)
    out: List[Security] = []
    for row in rows:
        code = normalize_code(pick_col(row, ["コード", "Code"]))
        name = normalize_text(pick_col(row, ["銘柄名称", "銘柄名", "Name"]))
        sector = normalize_text(pick_col(row, ["業種", "Sector"]))
        if not code or not CODE_RE.match(code):
            continue
        out.append(
            Security(
                code=code,
                ticker=make_ticker(code),
                name=name,
                sector=sector,
                market="Prime",
                sources={"jpx_prime150": True},
                source_details={"jpx_prime150": "constituent"},
                source_urls={"jpx_prime150": JPX_PRIME150_WEIGHT_URL},
            )
        )
    return out


def extract_pdf_words_with_pymupdf(pdf_bytes: bytes) -> List[Tuple[int, float, float, float, float, str]]:
    try:
        import fitz  # PyMuPDF
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "PyMuPDF is required for PDF constituent parsing. Install with: python -m pip install pymupdf"
        ) from exc

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    words: List[Tuple[int, float, float, float, float, str]] = []
    for page_index, page in enumerate(doc):
        for w in page.get_text("words"):
            x0, y0, x1, y1, text, *_ = w
            words.append((page_index, float(x0), float(y0), float(x1), float(y1), str(text)))
    return words


def group_words_by_line(words: List[Tuple[int, float, float, float, float, str]], y_tol: float = 3.0) -> List[List[Tuple[int, float, float, float, float, str]]]:
    lines: List[List[Tuple[int, float, float, float, float, str]]] = []
    for page in sorted({w[0] for w in words}):
        page_words = sorted([w for w in words if w[0] == page], key=lambda w: (w[2], w[1]))
        current: List[Tuple[int, float, float, float, float, str]] = []
        current_y: Optional[float] = None
        for w in page_words:
            y = w[2]
            if current_y is None or abs(y - current_y) <= y_tol:
                current.append(w)
                current_y = y if current_y is None else (current_y + y) / 2
            else:
                if current:
                    lines.append(sorted(current, key=lambda t: t[1]))
                current = [w]
                current_y = y
        if current:
            lines.append(sorted(current, key=lambda t: t[1]))
    return lines


def parse_pdf_constituents(pdf_url: str, source_key: str, default_market: str = "") -> List[Security]:
    """
    Parse JPX constituent PDFs that use multi-column tables.

    The parser is intentionally code-first:
    - It searches for security codes (4 digits or 3 digits + A)
    - It captures text to the right of each code until the next code/row marker when possible
    - If the PDF layout separates code and name columns, it still preserves code and leaves name blank
      rather than fabricating names.
    """
    pdf_bytes = fetch_bytes(pdf_url)
    words = extract_pdf_words_with_pymupdf(pdf_bytes)
    lines = group_words_by_line(words)
    securities: Dict[str, Security] = {}

    skip_words = {
        "No.", "No", "Code", "Name", "Mkt", "Sector", "Addition", "Deletion", "Copyright", "Published"
    }

    for line in lines:
        tokens = [(w[1], w[5]) for w in line]
        # Remove page headers/footers and obvious non-table sections.
        texts = [t for _, t in tokens]
        if not texts or any(t.startswith("Copyright") for t in texts):
            continue
        if "Code" in texts and "Name" in texts:
            continue

        # Find all code token positions on this line.
        code_positions = [(i, x, normalize_code(t)) for i, (x, t) in enumerate(tokens) if CODE_RE.match(normalize_code(t))]
        if not code_positions:
            continue

        for pos_idx, (i, x, code) in enumerate(code_positions):
            # Names usually follow code until the next numbered row/code block.
            next_i = code_positions[pos_idx + 1][0] if pos_idx + 1 < len(code_positions) else len(tokens)
            raw_name_tokens: List[str] = []
            for _, t in tokens[i + 1: next_i]:
                nt = normalize_text(t)
                if not nt or nt in skip_words:
                    continue
                # Drop row numbers and known market abbreviations when they are isolated.
                if re.fullmatch(r"\d{1,3}", nt):
                    continue
                if nt in {"P", "G", "S"}:
                    # For Startup100 PDF this is market, not name.
                    continue
                raw_name_tokens.append(nt)
            name = normalize_text(" ".join(raw_name_tokens))

            # Avoid polluting names with sector fragments in Startup100; this is a heuristic.
            for marker in [
                " Info & Com", " Real Estate", " Retail Trade", " Services", " Pharmaceutical",
                " Insurance", " Construction", " Chemicals", " Other Products", " Precision Instruments",
                " Securities and Commodities Futures", " Electric Power and Gas", " Wholesale Trade",
            ]:
                if marker in name:
                    name = name.split(marker)[0].strip()

            if not is_valid_code_token(code, source=source_key, name=name):
                continue

            sec = Security(
                code=code,
                ticker=make_ticker(code),
                name=name,
                sector="",
                market=default_market,
                sources={source_key: True},
                source_details={source_key: "constituent"},
                source_urls={source_key: pdf_url},
            )
            if code not in securities:
                securities[code] = sec
            elif name and not securities[code].name:
                securities[code].name = name
    return list(securities.values())


def build_growth250() -> List[Security]:
    # Effective Oct. 31, 2025 periodic review PDF; subsequent component changes should be handled by replacing URL if JPX publishes a newer component PDF.
    return parse_pdf_constituents(GROWTH250_PDF_URL, "growth250", default_market="Growth")


def build_startup100() -> List[Security]:
    return parse_pdf_constituents(STARTUP100_PDF_URL, "jpx_startup100", default_market="Growth/Prime/Standard")


def combine_security_lists(lists: Sequence[Sequence[Security]]) -> List[Security]:
    merged: Dict[str, Security] = {}
    for securities in lists:
        for sec in securities:
            if not is_valid_code_token(sec.code, source="csv", name=sec.name):
                continue
            if sec.code in merged:
                merged[sec.code].merge(sec)
            else:
                merged[sec.code] = sec
    return sorted(merged.values(), key=lambda s: (s.ticker, s.primary_source))


def write_csv(path: Path, securities: Sequence[Security]) -> None:
    fields = [
        "ticker", "code", "name", "market", "sector", "primary_source", "sources",
        "is_topix500", "is_jpx_prime150", "is_growth250", "is_jpx_startup100",
        "source_detail", "source_url",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for sec in securities:
            writer.writerow(sec.as_row())


def write_json(path: Path, securities: Sequence[Security]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "neon_tokyo_jp_index_universe_v1",
        "generated_at_utc": now_iso(),
        "count": len(securities),
        "sources": SOURCE_LABELS,
        "rows": [sec.as_row() for sec in securities],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_diagnostics(path: Path, securities: Sequence[Security], source_counts: Dict[str, int], errors: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dup_sources = {src: 0 for src in SOURCE_PRIORITY}
    for sec in securities:
        for src in SOURCE_PRIORITY:
            if sec.sources.get(src):
                dup_sources[src] += 1
    diagnostics = {
        "schema_version": "neon_tokyo_jp_index_universe_diagnostics_v1",
        "generated_at_utc": now_iso(),
        "unique_count": len(securities),
        "input_source_counts": source_counts,
        "output_source_flags": dup_sources,
        "errors": errors,
        "source_urls": {
            "topix500": TOPIX_WEIGHT_URL,
            "jpx_prime150": JPX_PRIME150_WEIGHT_URL,
            "growth250": GROWTH250_PDF_URL,
            "jpx_startup100": STARTUP100_PDF_URL,
        },
    }
    path.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-csv", default="data/universe/jp_index_universe.csv")
    parser.add_argument("--site-csv", default="site/data/japan/universe/jp_index_universe.csv")
    parser.add_argument("--site-json", default="site/data/japan/universe/jp_index_universe.json")
    parser.add_argument("--diagnostics", default="site/data/japan/universe/diagnostics.json")
    parser.add_argument("--allow-partial", action="store_true", help="Write output even if one source fails.")
    args = parser.parse_args()

    source_builders = {
        "topix500": build_topix500,
        "jpx_prime150": build_jpx_prime150,
        "growth250": build_growth250,
        "jpx_startup100": build_startup100,
    }

    all_lists: List[List[Security]] = []
    source_counts: Dict[str, int] = {}
    errors: Dict[str, str] = {}

    for src, builder in source_builders.items():
        try:
            securities = builder()
            source_counts[src] = len(securities)
            all_lists.append(securities)
            print(f"{src}: {len(securities)} rows")
        except Exception as exc:
            errors[src] = str(exc)
            source_counts[src] = 0
            print(f"ERROR {src}: {exc}", file=sys.stderr)
            if not args.allow_partial:
                raise

    combined = combine_security_lists(all_lists)
    print(f"unique_count: {len(combined)}")

    out_csv = Path(args.out_csv)
    site_csv = Path(args.site_csv)
    site_json = Path(args.site_json)
    diagnostics = Path(args.diagnostics)

    write_csv(out_csv, combined)
    write_csv(site_csv, combined)
    write_json(site_json, combined)
    write_diagnostics(diagnostics, combined, source_counts, errors)

    print(f"Wrote {out_csv}")
    print(f"Wrote {site_csv}")
    print(f"Wrote {site_json}")
    print(f"Wrote {diagnostics}")

    if errors and not args.allow_partial:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
