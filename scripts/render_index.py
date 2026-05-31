from __future__ import annotations

"""Render the Neon Tokyo top page from AI Arena and prices-jp data only.

Daily / Weekly pages are being retired. This renderer intentionally does not
read legacy research or backtest artifacts. The TOP page is allowed to depend only on:
- site/data/japan/ai-arena/hero/latest.json
- site/data/japan/ai-arena/summary/latest.json
- site/data/prices-jp/latest.json

If AI Arena hero data is temporarily missing, the page falls back to AI Arena
summary data. If both Arena payloads are unavailable, it renders a minimal market
pulse from prices-jp so that the homepage remains valid HTML, but it still does
not depend on Daily / Weekly artifacts.
"""

from datetime import datetime
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

AGENT_THEME_TONE = {
    "red": "growth",
    "purple": "topix",
    "violet": "topix",
    "cyan": "nikkei",
    "light_blue": "nikkei",
    "blue": "topix",
    "green": "growth",
    "yellow": "growth",
    "amber": "growth",
    "pink": "growth",
    "magenta": "growth",
    "indigo": "topix",
    "indigo_blue": "topix",
}

AGENT_COLOR_BY_ID = {
    "KYOU": "#FF4B5C",
    "NAGARE": "#B779FF",
    "MAMORU": "#7DF9FF",
    "SAGURI": "#5DFFB1",
    "MATSU": "#FFD166",
    "KAESHI": "#FF4FD8",
    "HIZUMI": "#4F46E5",
}


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


def agent_color(agent: dict[str, Any]) -> str:
    aid = str(agent.get("agent_id") or agent.get("id") or "").upper()
    return AGENT_COLOR_BY_ID.get(aid) or str(agent.get("color") or "#7DF9FF")


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except Exception:
        return None


def split_adjusted_closes(bars: list[dict[str, Any]]) -> list[tuple[str, float]]:
    """Return a continuous close series by back-adjusting obvious split-like jumps.

    This is a prices-jp-only fallback. It does not read Daily / Weekly outputs.
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
        # Keep vertical margin so the neon trace never touches the SVG edge.
        out.append(int(round(18 + ((v - lo) / (hi - lo)) * 68)))
    return out


def build_market_pulse(prices: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a minimal NIKKEI/TOPIX/GROWTH fallback from prices-jp only."""
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
            "name": label,
            "symbol": cfg["symbol"],
            "role_label": label,
            "tone": cfg["tone"],
            "points": ",".join(str(x) for x in points),
            "performance_pct": perf,
            "performance_label": pct(perf, 1),
            "performance_class": pct_class(perf),
            "date_start": weeks[0][0] if weeks else None,
            "date_end": weeks[-1][0] if weeks else None,
            "color": "#7DF9FF",
            "icon_src": "",
            "is_agent": False,
        })
    return out


def _agent_tone(agent: dict[str, Any]) -> str:
    tone = str(agent.get("tone") or "").strip().lower()
    if tone in {"nikkei", "topix", "growth"}:
        return tone
    theme = str(agent.get("theme") or agent.get("theme_color") or "cyan").strip().lower()
    return AGENT_THEME_TONE.get(theme, "nikkei")


def _agent_spark_values(agent: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for p in agent.get("sparkline") or []:
        if not isinstance(p, dict):
            continue
        v = as_float(p.get("equity"))
        if v is not None and v > 0:
            values.append(v)
    return values


def build_agent_pulse(hero: dict[str, Any], fallback_summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Build TOP Hero pulse items from AI Arena hero or summary JSON."""
    agents = hero.get("agents") if isinstance(hero, dict) else None

    if not agents:
        # Fallback to AI Arena summary. This keeps the TOP page usable even when
        # an older canonical DB has not exported hero/latest.json yet.
        agents = []
        annual = ((fallback_summary.get("rankings") or {}).get("annual_performance") or [])
        for r in annual:
            if not isinstance(r, dict):
                continue
            agent = r.get("agent") or {}
            aid = str(r.get("agent_id") or agent.get("agent_id") or "")
            if not aid:
                continue
            agents.append({
                "agent_id": aid,
                "display_name": agent.get("name") or aid.upper(),
                "role": aid,
                "role_label": agent.get("role") or agent.get("style") or "AI Agent",
                "theme": str(agent.get("theme_color") or "cyan").lower(),
                "tone": _agent_tone(agent),
                "color": agent_color({**agent, "agent_id": aid}),
                "icon_src": agent.get("image") or f"/assets/ai-arena/agents/{aid}.png",
                "rank": r.get("rank"),
                "return_pct": as_float(r.get("total_return_pct"), 0.0),
                "sparkline": r.get("sparkline") or [],
                "background_label": agent.get("name") or aid.upper(),
            })

    out: list[dict[str, Any]] = []
    for a in agents or []:
        if not isinstance(a, dict):
            continue
        values = _agent_spark_values(a)
        # If sparkline is temporarily unavailable, draw a flat but valid line.
        if len(values) < 2:
            ret = as_float(a.get("return_pct"), 0.0) or 0.0
            values = [100.0, 100.0 * (1 + ret / 100.0)]
        points = normalize_points(values)
        label = str(a.get("display_name") or a.get("name") or a.get("agent_id") or "AGENT").upper()
        ret = as_float(a.get("return_pct"), 0.0)
        out.append({
            "label": label,
            "name": label,
            "symbol": str(a.get("role") or a.get("agent_id") or "AI AGENT"),
            "role_label": str(a.get("role_label") or a.get("role") or "AI Agent"),
            "tone": _agent_tone(a),
            "points": ",".join(str(x) for x in points),
            "performance_pct": ret,
            "performance_label": pct(ret, 1),
            "performance_class": pct_class(ret),
            "color": agent_color(a),
            "icon_src": str(a.get("icon_src") or a.get("image") or ""),
            "rank": a.get("rank"),
            "is_agent": True,
        })
    return out


def build_price_ticker_items(prices: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    """Fallback ticker from prices-jp summary only.

    prices-jp/latest.json is expected to stay in summary mode; bars are not
    required here. This function never reads Daily / Weekly signal files.
    """
    price_items = prices.get("items") or []
    price_by_symbol = {str(x.get("symbol")): x for x in price_items if isinstance(x, dict)}

    # Prefer symbols explicitly present in DEFAULT_TICKERS, then fill from the
    # first available price items. This keeps the ticker non-empty even when a
    # default ETF or stock is temporarily absent from the universe.
    symbols: list[str] = []
    for s in DEFAULT_TICKERS:
        if s in price_by_symbol and s not in symbols:
            symbols.append(s)
    for item in price_items:
        if not isinstance(item, dict):
            continue
        s = str(item.get("symbol") or "")
        if s and s not in symbols:
            symbols.append(s)
        if len(symbols) >= limit:
            break

    out: list[dict[str, Any]] = []
    for s in symbols[:limit]:
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
            "text": f"TOKYO WATCH {s} {item.get('name') or s} {pct(ret, 1)}",
            "type": "WATCH",
            "agent_name": "TOKYO WATCH",
        })
    return out


def build_ai_arena_ticker_items(
    hero: dict[str, Any],
    fallback_summary: dict[str, Any],
    prices: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build the TOP ticker tape from AI Arena first, prices-jp second."""
    items = hero.get("ticker_tape") if isinstance(hero, dict) else None
    if items:
        valid = [x for x in items if isinstance(x, dict) and x.get("text")]
        if valid:
            return valid

    # Fallback from Summary open positions and best trades.
    out: list[dict[str, Any]] = []
    annual = ((fallback_summary.get("rankings") or {}).get("annual_performance") or [])
    agent_name = {
        str(r.get("agent_id")): ((r.get("agent") or {}).get("name") or str(r.get("agent_id")).upper())
        for r in annual
        if isinstance(r, dict)
    }

    portfolio = fallback_summary.get("portfolio") or {}
    for p in portfolio.get("top_positions") or []:
        if not isinstance(p, dict):
            continue
        aid = str(p.get("agent_id") or "")
        name = str(agent_name.get(aid) or aid or "AGENT").upper()
        symbol = str(p.get("ticker") or "")
        company = str(p.get("name") or symbol)
        display = f"{symbol} {company}".strip()
        out.append({
            "agent_id": aid,
            "agent_name": name,
            "type": "IN",
            "symbol": symbol,
            "company_name": company,
            "display_symbol_name": display,
            "text": f"{name} IN {display}",
        })

    for t in ((fallback_summary.get("rankings") or {}).get("best_trades") or [])[:8]:
        if not isinstance(t, dict):
            continue
        aid = str(t.get("agent_id") or "")
        name = str(agent_name.get(aid) or aid or "AGENT").upper()
        symbol = str(t.get("ticker") or "")
        company = str(t.get("name") or symbol)
        display = f"{symbol} {company}".strip()
        out.append({
            "agent_id": aid,
            "agent_name": name,
            "type": "OUT",
            "symbol": symbol,
            "company_name": company,
            "display_symbol_name": display,
            "text": f"{name} OUT {display}",
        })

    return out[:18] if out else build_price_ticker_items(prices)


def build_status(prices: dict[str, Any], hero: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    items = prices.get("items") or []
    dates = []
    for x in items:
        if not isinstance(x, dict):
            continue
        m = x.get("metrics") or {}
        d = m.get("latest_date") or x.get("date_end")
        if d:
            dates.append(str(d)[:10])

    season = hero.get("season") if isinstance(hero, dict) else {}
    summary_season = summary.get("season") if isinstance(summary, dict) else {}

    return {
        "latest_price_date": max(dates) if dates else None,
        "prices_generated_at": prices.get("generated_at"),
        "arena_latest_date": (season or {}).get("latest_date") or (summary_season or {}).get("latest_date"),
        "arena_generated_at": hero.get("generated_at") if isinstance(hero, dict) else None,
        "arena_run_id": (hero.get("run_id") or hero.get("display_run_id")) if isinstance(hero, dict) else None,
    }


def main() -> None:
    e = env()

    prices = read_json(OUT_DIR / "data" / "prices-jp" / "latest.json", {"items": []})
    hero = read_json(OUT_DIR / "data" / "japan" / "ai-arena" / "hero" / "latest.json", {})
    summary = read_json(OUT_DIR / "data" / "japan" / "ai-arena" / "summary" / "latest.json", {})

    market_pulse = build_agent_pulse(hero, summary)
    if not market_pulse:
        market_pulse = build_market_pulse(prices)

    ticker_items = build_ai_arena_ticker_items(hero, summary, prices)

    html = e.get_template("index.html.j2").render(
        brand="Neon Tokyo Signals",
        tagline="AI Arena JP is live after the Tokyo close.",
        generated_at=generated_at(),
        prices=prices,
        ai_arena_hero=hero,
        ai_arena_summary=summary,
        market_pulse=market_pulse,
        ticker_items=ticker_items,
        status=build_status(prices, hero, summary),
    )

    write_text(OUT_DIR / "index.html", html)
    copy_asset("base.css", "base.css")
    copy_asset("index.css", "index.css")


if __name__ == "__main__":
    main()
