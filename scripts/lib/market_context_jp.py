from __future__ import annotations

"""Market context builder for AI Arena Live Lab.

This module intentionally uses only numeric market proxies. It does not fetch or
summarize news, so GPT prompts can discuss market regime without inventing
unsupported catalysts.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

JST = timezone(timedelta(hours=9))

SYMBOLS: dict[str, dict[str, str]] = {
    "nikkei_225": {"label": "Nikkei 225", "symbol": "^N225", "kind": "japan_equity"},
    "topix": {"label": "TOPIX", "symbol": "^TOPX", "kind": "japan_equity"},
    "sp500": {"label": "S&P 500", "symbol": "^GSPC", "kind": "global_equity"},
    "nasdaq": {"label": "NASDAQ Composite", "symbol": "^IXIC", "kind": "global_tech"},
    "russell_2000": {"label": "Russell 2000", "symbol": "^RUT", "kind": "global_small_cap"},
    "usd_jpy": {"label": "USD/JPY", "symbol": "JPY=X", "kind": "fx"},
    "us_10y_yield": {"label": "US 10Y yield proxy", "symbol": "^TNX", "kind": "rates"},
    "semiconductor_proxy": {"label": "SOXX semiconductor ETF", "symbol": "SOXX", "kind": "semiconductor"},
}


def _fmt_pct(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{value:+.2f}%"


def _interpret(key: str, change: float | None) -> str:
    if change is None or not math.isfinite(change):
        return "no reliable latest quote"
    abs_change = abs(change)
    direction = "firm" if change > 0 else "soft" if change < 0 else "flat"
    if key == "nikkei_225":
        return f"Japanese large-cap tape is {direction}"
    if key == "topix":
        return f"broad Japan equity tone is {direction}"
    if key == "sp500":
        return f"US large-cap risk tone is {direction}"
    if key == "nasdaq":
        return f"global technology risk appetite is {direction}"
    if key == "russell_2000":
        return f"US small-cap risk appetite is {direction}"
    if key == "usd_jpy":
        return "yen weakness context" if change > 0 else "yen strength context" if change < 0 else "FX context is flat"
    if key == "us_10y_yield":
        return "higher-rate pressure" if change > 0 else "lower-rate relief" if change < 0 else "rates pressure is flat"
    if key == "semiconductor_proxy":
        return "semiconductor tailwind" if change > 0 else "semiconductor pressure" if change < 0 else "semiconductor proxy is flat"
    return f"market proxy is {direction}"


def _regime(items: list[dict[str, Any]]) -> str:
    by_key = {x.get("key"): x for x in items}
    pieces: list[str] = []
    n225 = by_key.get("nikkei_225", {})
    topix = by_key.get("topix", {})
    nasdaq = by_key.get("nasdaq", {})
    soxx = by_key.get("semiconductor_proxy", {})
    usdjpy = by_key.get("usd_jpy", {})
    tnx = by_key.get("us_10y_yield", {})
    if n225.get("change_pct") is not None and topix.get("change_pct") is not None:
        if float(n225["change_pct"]) > float(topix["change_pct"]):
            pieces.append("Japanese large caps are leading broad TOPIX tone")
        else:
            pieces.append("broad TOPIX tone is matching or leading the Nikkei")
    if nasdaq.get("change_pct") is not None and float(nasdaq["change_pct"]) > 0:
        pieces.append("US technology context is supportive")
    if soxx.get("change_pct") is not None and float(soxx["change_pct"]) > 0:
        pieces.append("semiconductor beta is supportive")
    if usdjpy.get("change_pct") is not None:
        pieces.append("USD/JPY is elevated versus the previous close" if float(usdjpy["change_pct"]) > 0 else "JPY is firmer versus the previous close")
    if tnx.get("change_pct") is not None:
        pieces.append("US yields are a pressure point" if float(tnx["change_pct"]) > 0 else "US yields are offering some rate relief")
    return "; ".join(pieces[:4]) or "Market context is available, but no strong regime signal was detected."


def build_market_context(*, enabled: bool = True, lookback_days: int = 7) -> dict[str, Any]:
    now = datetime.now(JST).isoformat(timespec="seconds")
    if not enabled:
        return {"enabled": False, "as_of": now, "items": [], "regime_summary": "Market context disabled.", "strict_rule": "Do not use external market facts."}
    items: list[dict[str, Any]] = []
    try:
        import yfinance as yf  # type: ignore
    except Exception as exc:
        return {"enabled": False, "as_of": now, "items": [], "regime_summary": f"Market context unavailable: {exc}", "strict_rule": "Do not use external market facts."}
    for key, meta in SYMBOLS.items():
        symbol = meta["symbol"]
        try:
            hist = yf.download(symbol, period=f"{max(3, lookback_days)}d", interval="1d", progress=False, auto_adjust=False, threads=False)
            if hist is None or hist.empty or "Close" not in hist:
                continue
            closes = hist["Close"].dropna()
            if len(closes) < 2:
                continue
            last = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            change_pct = ((last / prev) - 1.0) * 100 if prev else None
            items.append({
                "key": key,
                "label": meta["label"],
                "symbol": symbol,
                "kind": meta["kind"],
                "last": round(last, 4),
                "previous_close": round(prev, 4),
                "change_pct": round(change_pct, 4) if change_pct is not None else None,
                "change_label": _fmt_pct(change_pct),
                "interpretation": _interpret(key, change_pct),
            })
        except Exception:
            continue
    return {
        "enabled": bool(items),
        "as_of": now,
        "items": items,
        "regime_summary": _regime(items),
        "strict_rule": "Use only these numeric market context facts. Do not invent news, causes, catalysts, or geopolitical events.",
    }
