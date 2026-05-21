from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

from render_common import OUT_DIR, copy_asset, env, generated_at, read_json, write_text


MARKET_PULSE_SYMBOLS = {
    "NIKKEI": {"symbol": "1321.T", "tone": "nikkei"},
    "TOPIX": {"symbol": "1306.T", "tone": "topix"},
    "GROWTH": {"symbol": "2516.T", "tone": "growth"},
}

DEFAULT_TICKERS = [
    "8035.T",
    "6857.T",
    "6146.T",
    "6920.T",
    "5803.T",
    "7011.T",
    "6758.T",
    "6503.T",
    "4425.T",
    "135A.T",
    "3993.T",
    "5582.T",
]


def as_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        v = float(value)
        if v != v:
            return default
        return v
    except Exception:
        return default


def pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{digits}f}%"


def pct_class(value: float | None) -> str:
    if value is None:
        return "ret-flat"
    if value > 0:
        return "ret-up"
    if value < 0:
        return "ret-down"
    return "ret-flat"


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except Exception:
        return None


def split_adjusted_closes(bars: list[dict[str, Any]]) -> list[tuple[str, float]]:
    """Return a continuous close series by back-adjusting obvious split-like jumps.

    yfinance occasionally returns unadjusted pre-split prices for JP ETFs such as
    1306.T. A one-day close ratio below ~0.35 is not a market move; it is treated
    as a split-like discontinuity and prior history is scaled into the latest unit.
    This only affects the display chart/performance, never trading logic.
    """
    rows: list[tuple[str, float]] = []
    for b in bars or []:
        d = str(b.get("date") or "")[:10]
        c = as_float(b.get("close"))
        if d and c and c > 0:
            rows.append((d, c))
    rows.sort(key=lambda x: x[0])
    if len(rows) < 2:
        return rows

    adjusted = [[d, c] for d, c in rows]
    for i in range(1, len(adjusted)):
        prev = adjusted[i - 1][1]
        curr = adjusted[i][1]
        if prev <= 0 or curr <= 0:
            continue
        ratio = curr / prev
        if ratio < 0.35 or ratio > 3.2:
            # Back-adjust all previous closes so the series remains continuous.
            factor = ratio
            if ratio > 3.2:
                factor = ratio
            for j in range(i):
                adjusted[j][1] *= factor
    return [(d, float(c)) for d, c in adjusted]


def weekly_sample_last_year(rows: list[tuple[str, float]], max_weeks: int = 53) -> list[tuple[str, float]]:
    if not rows:
        return []
    rows = rows[-260:]
    weekly: dict[tuple[int, int], tuple[str, float]] = {}
    for d, c in rows:
        dt = parse_date(d)
        if not dt:
            continue
        iso = dt.isocalendar()
        weekly[(iso.year, iso.week)] = (d, c)
    sampled = [weekly[k] for k in sorted(weekly.keys())]
    return sampled[-max_weeks:]


def normalize_points(values: list[float]) -> list[int]:
    if not values:
        return [50, 52, 51, 54]
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return [52 for _ in values]
    out = []
    for v in values:
        # Keep some vertical margin so the neon trace never touches the edge.
        out.append(int(round(18 + ((v - lo) / (hi - lo)) * 68)))
    return out


def build_market_pulse(prices: dict[str, Any]) -> list[dict[str, Any]]:
    items = prices.get("items") or []
    by_symbol = {str(x.get("symbol")): x for x in items if isinstance(x, dict)}
    out: list[dict[str, Any]] = []
    for label, cfg in MARKET_PULSE_SYMBOLS.items():
        item = by_symbol.get(cfg["symbol"], {})
        rows = split_adjusted_closes(item.get("bars") or [])
        weeks = weekly_sample_last_year(rows)
        closes = [c for _, c in weeks]
        perf = None
        if len(closes) >= 2 and closes[0] > 0:
            perf = (closes[-1] / closes[0] - 1.0) * 100.0
        points = normalize_points(closes)
        out.append({
            "label": label,
            "symbol": cfg["symbol"],
            "tone": cfg["tone"],
            "points": ",".join(str(x) for x in points),
            "performance_pct": perf,
            "performance_label": pct(perf, 1),
            "performance_class": pct_class(perf),
            "date_start": weeks[0][0] if weeks else None,
            "date_end": weeks[-1][0] if weeks else None,
        })
    return out


def build_ticker_items(prices: dict[str, Any], daily: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    price_items = prices.get("items") or []
    price_by_symbol = {str(x.get("symbol")): x for x in price_items if isinstance(x, dict)}
    daily_items = daily.get("items") or daily.get("all_items") or []

    symbols: list[str] = []
    for x in daily_items:
        s = str(x.get("symbol") or "")
        if s and s not in symbols:
            symbols.append(s)
    for s in DEFAULT_TICKERS:
        if s not in symbols:
            symbols.append(s)

    out: list[dict[str, Any]] = []
    for s in symbols:
        item = price_by_symbol.get(s)
        if not item:
            continue
        metrics = item.get("metrics") or {}
        ret = as_float(metrics.get("return_1d_pct"))
        out.append({
            "symbol": s,
            "name": item.get("name") or s,
            "return_1d_pct": ret,
            "return_1d_label": pct(ret, 1),
            "return_class": pct_class(ret),
        })
        if len(out) >= limit:
            break
    return out


def build_status(prices: dict[str, Any]) -> dict[str, Any]:
    items = prices.get("items") or []
    dates = []
    for x in items:
        m = x.get("metrics") or {}
        d = m.get("latest_date") or x.get("date_end")
        if d:
            dates.append(str(d)[:10])
    return {
        "latest_price_date": max(dates) if dates else None,
        "prices_generated_at": prices.get("generated_at"),
    }


def main() -> None:
    e = env()
    prices = read_json(OUT_DIR / "data" / "prices-jp" / "latest.json", {"items": []})
    daily = read_json(OUT_DIR / "data" / "daily-jp" / "latest.json", {"items": []})
    if not daily.get("items"):
        daily = read_json(OUT_DIR / "data" / "daily-v2-jp" / "latest.json", {"items": []})
    weekly = read_json(OUT_DIR / "data" / "japan" / "weekly" / "latest.json", {"items": []})
    if not weekly.get("items"):
        weekly = read_json(OUT_DIR / "data" / "weekly-jp" / "latest.json", {"items": []})

    top = daily.get("items", [{}])[0] if daily.get("items") else {}
    market_pulse = build_market_pulse(prices)
    ticker_items = build_ticker_items(prices, daily)

    html = e.get_template("index.html.j2").render(
        brand="Neon Tokyo Signals",
        tagline="Japan equity signals after the Tokyo close.",
        generated_at=generated_at(),
        top=top,
        daily=daily,
        weekly=weekly,
        prices=prices,
        market_pulse=market_pulse,
        ticker_items=ticker_items,
        status=build_status(prices),
    )

    write_text(OUT_DIR / "index.html", html)
    copy_asset("base.css", "base.css")
    copy_asset("index.css", "index.css")


if __name__ == "__main__":
    main()
