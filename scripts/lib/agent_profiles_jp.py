from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Any

import pandas as pd


def nz(value: Any, default: float = 0.0) -> float:
    try:
        v = float(value)
        if math.isfinite(v):
            return v
    except Exception:
        pass
    return default


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def scale(value: Any, lo: float, hi: float) -> float:
    v = nz(value, lo)
    if hi == lo:
        return 0.0
    return clamp01((v - lo) / (hi - lo))


def inv_scale(value: Any, lo: float, hi: float) -> float:
    return 1.0 - scale(value, lo, hi)


@dataclass(frozen=True)
class AgentProfile:
    id: str
    name: str
    style_label: str
    universe_rule: str


AGENT_PROFILES: list[AgentProfile] = [
    AgentProfile("daily_striker", "KYOU", "Today’s Momentum Signal", "core_growth_liquid"),
    AgentProfile("weekly_sage", "NAGARE", "Weekly / Trend Flow", "core_growth"),
    AgentProfile("risk_sentinel", "MAMORU", "Risk / Quality Defense", "core_liquid"),
    AgentProfile("discovery_scout", "SAGURI", "Small Cap / Hidden Discovery", "small_discovery"),
    AgentProfile("contrarian_monk", "MATSU", "Pullback / Patient Reversal", "core_growth"),
    AgentProfile("reversal_snapback", "KAESHI", "Reversal / Snapback Signal", "core_growth_liquid"),
    AgentProfile("value_mispricing", "HIZUMI", "Value / Mispricing Signal", "value_candidate"),
]


def _universe_ok(row: pd.Series, rule: str) -> bool:
    asset = str(row.get("asset_type") or "equity").lower()
    if asset != "equity":
        return False
    if bool(row.get("is_excluded")):
        return False
    liq = nz(row.get("liquidity_score"), 0.0)
    if rule == "core_growth_liquid":
        return (bool(row.get("is_core")) or bool(row.get("is_growth")) or bool(row.get("is_small_discovery"))) and liq >= 0.20
    if rule == "core_growth":
        return bool(row.get("is_core")) or bool(row.get("is_growth"))
    if rule == "core_liquid":
        return bool(row.get("is_core")) and liq >= 0.45
    if rule == "small_discovery":
        return bool(row.get("is_small_discovery")) and liq >= 0.12
    if rule == "value_candidate":
        return bool(row.get("is_value_candidate")) and liq >= 0.20
    return True


def score_agent_row(row: pd.Series, profile: AgentProfile) -> tuple[float, dict[str, Any]]:
    liq = nz(row.get("liquidity_score"), 0.0)
    risk = nz(row.get("risk_score"), 0.0)
    trend_d = nz(row.get("trend_score_daily"), 0.0)
    trend_w = nz(row.get("trend_score_weekly_proxy"), 0.0)
    mom = nz(row.get("momentum_score_short"), 0.0)
    rev = nz(row.get("reversal_exhaustion_score"), 0.0)
    vol_re = nz(row.get("volume_reaccumulation_score"), 0.0)
    r1 = nz(row.get("return_1d_pct"), 0.0)
    r5 = nz(row.get("return_5d_pct"), 0.0)
    r20 = nz(row.get("return_20d_pct"), 0.0)
    r60 = nz(row.get("return_60d_pct"), 0.0)
    vs20 = nz(row.get("price_vs_ma20_pct"), 0.0)
    vs50 = nz(row.get("price_vs_ma50_pct"), 0.0)
    dd60 = nz(row.get("max_drawdown_60d_pct"), -50.0)
    dist20 = nz(row.get("distance_from_20d_high_pct"), -100.0)
    dist52 = nz(row.get("distance_from_52w_high_pct"), -100.0)
    range20 = nz(row.get("range_position_20d_0_1"), 0.0)
    range60 = nz(row.get("range_position_60d_0_1"), 0.0)
    range252 = nz(row.get("range_position_252d_0_1"), 0.0)
    vol60 = nz(row.get("volatility_60d_annualized_pct"), 80.0)
    dryup = nz(row.get("volume_dryup_10d"), 1.0)
    rsi = nz(row.get("rsi_14"), 50.0)
    volratio = nz(row.get("volume_ratio_20d"), 1.0)

    value_rerate = scale(r60, -10, 25) * 0.35 + scale(row.get("distance_from_52w_low_pct"), 5, 80) * 0.25 + scale(liq, 0.2, 0.9) * 0.20 + scale(-dist52, 10, 65) * 0.20
    value_mispricing = row.get("value_mispricing_score")
    value_quality = row.get("quality_guard_score")
    value_discount = row.get("valuation_discount_score")
    trap = nz(row.get("value_trap_penalty"), 0.0)
    has_value_features = any(pd.notna(x) for x in [value_mispricing, value_quality, value_discount])

    if profile.id == "daily_striker":
        # KYOU v2: favor fresh high-volume daily breakouts, not generic hot momentum.
        breakout_quality = (
            scale(r1, 0.4, 6.0) * 0.18
            + scale(volratio, 1.2, 4.0) * 0.22
            + scale(range20, 0.65, 1.0) * 0.16
            + scale(dist20, -3.0, 0.5) * 0.10
            + trend_d * 0.16
            + liq * 0.10
        )
        risk_control = clamp01(
            1.0
            - scale(rsi, 70, 86) * 0.45
            - scale(r5, 18, 35) * 0.35
            - scale(vol60, 80, 140) * 0.20
        )
        raw = breakout_quality + risk_control * 0.08
        reasons = ["fresh_daily_breakout", "volume_quality", "overheat_control"]
    elif profile.id == "weekly_sage":
        raw = trend_w * 0.52 + scale(r60, 0, 35) * 0.18 + scale(vs50, -3, 14) * 0.12 + liq * 0.10 + inv_scale(vol60, 35, 100) * 0.08
        reasons = ["weekly_flow", "trend_structure", "relative_strength"]
    elif profile.id == "risk_sentinel":
        low_vol = inv_scale(vol60, 25, 75)
        drawdown_resilience = scale(dd60, -24, -3)
        ma_stability = inv_scale(abs(vs20), 0, 14)
        raw = risk * 0.38 + liq * 0.20 + low_vol * 0.16 + drawdown_resilience * 0.12 + trend_w * 0.08 + ma_stability * 0.06
        reasons = ["low_vol_liquidity", "drawdown_resilience", "capital_preservation"]
    elif profile.id == "discovery_scout":
        small_bonus = 1.0 if bool(row.get("is_small_discovery")) else 0.35
        quality = nz(value_quality, 0.30 if not has_value_features else 0.0)
        trap_guard = 1.0 - trap
        early = scale(r20, -5, 20) * 0.22 + scale(volratio, 0.9, 4.0) * 0.24 + scale(range60, 0.25, 0.85) * 0.13
        raw = early + small_bonus * 0.14 + vol_re * 0.11 + liq * 0.08 + quality * 0.05 + trap_guard * 0.03
        reasons = ["small_cap_discovery", "early_volume_shift", "quality_guard"]
    elif profile.id == "contrarian_monk":
        pullback_depth = scale(-r5, 1.0, 9.0)
        calm_volume = inv_scale(dryup, 0.55, 1.35)
        ma_reversion_zone = inv_scale(abs(vs50), 0, 12)
        rsi_neutral = clamp01(1.0 - abs(rsi - 50.0) / 28.0)
        range_health = scale(range252, 0.35, 0.80)
        raw = trend_w * 0.34 + pullback_depth * 0.18 + calm_volume * 0.14 + ma_reversion_zone * 0.12 + rsi_neutral * 0.10 + liq * 0.08 + range_health * 0.04
        reasons = ["quality_pullback", "trend_still_alive", "cooled_entry"]
    elif profile.id == "reversal_snapback":
        raw = rev * 0.54 + scale(-r5, 2, 16) * 0.16 + vol_re * 0.12 + scale(row.get("distance_from_20d_low_pct"), 0, 14) * 0.08 + liq * 0.10
        reasons = ["oversold_exhaustion", "snapback_pressure", "reaccumulation"]
    elif profile.id == "value_mispricing":
        if has_value_features:
            # HIZUMI v2: fewer, higher-quality value candidates.  Penalize traps strongly.
            raw = (
                nz(value_mispricing, 0.0) * 0.34
                + nz(value_quality, 0.0) * 0.26
                + nz(value_discount, 0.0) * 0.20
                + value_rerate * 0.10
                + risk * 0.06
                + liq * 0.04
                - trap * 0.18
            )
            reasons = ["quality_value_mispricing", "trap_guard", "rerating_signal"]
        else:
            raw = value_rerate * 0.36 + risk * 0.18 + liq * 0.16 + scale(-dist52, 12, 70) * 0.14 + scale(r20, -3, 16) * 0.10 + inv_scale(abs(vs50), 0, 35) * 0.06
            reasons = ["mispricing_proxy", "value_rerating", "trap_guard"]
    else:
        raw = 0.0
        reasons = ["unknown", "", ""]

    liquidity_penalty = 0.0 if liq >= 0.25 else (0.25 - liq) * 0.35
    risk_penalty = 0.0 if risk >= 0.15 else (0.15 - risk) * 0.20
    score = clamp01(raw - liquidity_penalty - risk_penalty)
    return score, {
        "risk_penalty": round(risk_penalty, 6),
        "liquidity_penalty": round(liquidity_penalty, 6),
        "reason_code_1": reasons[0],
        "reason_code_2": reasons[1],
        "reason_code_3": reasons[2],
    }


def action_from_score(score: float) -> tuple[str, str, bool, bool, bool]:
    if score >= 0.68:
        return "Trade", "high", True, False, False
    if score >= 0.52:
        return "Watch", "medium", False, True, False
    return "Ignore", "low", False, False, True


def _empty_agent_scores_frame() -> pd.DataFrame:
    """Return an empty frame with the exact columns expected by agent_scores_daily.

    This prevents downstream KeyError failures when the selected as-of date has
    no tradable equity candidates, for example when market-pulse ETFs have a
    newer date than equities.
    """
    return pd.DataFrame(columns=[
        "date",
        "agent_id",
        "agent_name",
        "ticker",
        "name",
        "universe_bucket",
        "raw_score",
        "normalized_score",
        "rank",
        "action",
        "signal_strength",
        "entry_score",
        "exit_score",
        "risk_penalty",
        "liquidity_penalty",
        "reason_code_1",
        "reason_code_2",
        "reason_code_3",
        "reason_text",
        "is_trade_candidate",
        "is_watch_candidate",
        "is_ignored",
        "created_at",
    ])


def _equity_candidate_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows that can reasonably contribute to agent score coverage.

    Market pulse ETFs may have a newer date than individual equities.  Using
    raw MAX(date) can therefore select a day with only 1306/1321/2516, causing
    zero agent candidates.  Coverage must be measured on equity candidates.
    """
    if df.empty:
        return df
    work = df.copy()
    asset = work.get("asset_type")
    if asset is not None:
        work = work[asset.fillna("equity").astype(str).str.lower().eq("equity")]
    if "is_excluded" in work.columns:
        work = work[~work["is_excluded"].fillna(False).astype(bool)]

    flags = ["is_core", "is_growth", "is_small_discovery", "is_value_candidate"]
    available = [c for c in flags if c in work.columns]
    if available:
        mask = pd.Series(False, index=work.index)
        for c in available:
            mask = mask | work[c].fillna(False).astype(bool)
        work = work[mask]
    return work


def _select_scoring_date(df: pd.DataFrame, as_of_date: str | None = None) -> pd.Timestamp | None:
    """Select a coverage-safe scoring date.

    The selected date is the latest date not later than `as_of_date` whose
    equity-candidate coverage is at least AGENT_SCORE_MIN_DATE_COVERAGE_PCT of
    the maximum observed equity-candidate universe.  Default is 70%.

    This avoids the common JP data issue where market ETFs update one session
    later than single stocks and accidentally become the global MAX(date).
    """
    if df.empty or "date" not in df.columns:
        return None

    work = df.copy()
    work["_date_ts"] = pd.to_datetime(work["date"], errors="coerce")
    work = work[work["_date_ts"].notna()]
    if as_of_date:
        cutoff = pd.to_datetime(as_of_date, errors="coerce")
        if pd.notna(cutoff):
            work = work[work["_date_ts"] <= cutoff]
    if work.empty:
        return None

    equity = _equity_candidate_frame(work)
    if equity.empty:
        return pd.to_datetime(work["_date_ts"]).max()

    denom = int(equity["ticker"].nunique()) if "ticker" in equity.columns else int(len(equity))
    min_pct = float(os.getenv("AGENT_SCORE_MIN_DATE_COVERAGE_PCT", "70") or 70)
    min_symbols_env = int(os.getenv("AGENT_SCORE_MIN_DATE_SYMBOLS", "0") or 0)
    min_symbols = max(min_symbols_env, int(math.ceil(denom * min_pct / 100.0)))
    min_symbols = max(1, min_symbols)

    grouped = (
        equity.groupby(equity["_date_ts"].dt.date)["ticker"].nunique()
        if "ticker" in equity.columns
        else equity.groupby(equity["_date_ts"].dt.date).size()
    )
    eligible = grouped[grouped >= min_symbols]
    if not eligible.empty:
        return pd.Timestamp(max(eligible.index))

    # Fallback: if coverage never reaches threshold, use the date with the most
    # equity candidates rather than a later ETF-only date.
    best_date = grouped.sort_values(ascending=False).index[0]
    return pd.Timestamp(best_date)

def build_agent_scores(features_with_universe: pd.DataFrame, as_of_date: str | None = None) -> pd.DataFrame:
    if features_with_universe.empty:
        return _empty_agent_scores_frame()
    df = features_with_universe.copy()
    latest_date = _select_scoring_date(df, as_of_date=as_of_date)
    if latest_date is None or pd.isna(latest_date):
        return _empty_agent_scores_frame()

    date_series = pd.to_datetime(df["date"], errors="coerce")
    latest = df[date_series == latest_date].copy()
    if latest.empty:
        return _empty_agent_scores_frame()

    rows = []
    created_at = pd.Timestamp.utcnow().to_pydatetime()
    for profile in AGENT_PROFILES:
        candidates = latest[latest.apply(lambda r: _universe_ok(r, profile.universe_rule), axis=1)].copy()
        scored = []
        for _, row in candidates.iterrows():
            score, meta = score_agent_row(row, profile)
            action, strength, is_trade, is_watch, is_ignored = action_from_score(score)
            scored.append((score, row, meta, action, strength, is_trade, is_watch, is_ignored))
        scored.sort(key=lambda x: (x[0], nz(x[1].get("liquidity_score"), 0.0)), reverse=True)
        for rank, (score, row, meta, action, strength, is_trade, is_watch, is_ignored) in enumerate(scored, start=1):
            reason_text = f"{profile.name}: {meta['reason_code_1']} / {meta['reason_code_2']} / {meta['reason_code_3']}"
            rows.append({
                "date": str(latest_date.date()),
                "agent_id": profile.id,
                "agent_name": profile.name,
                "ticker": row.get("ticker"),
                "name": row.get("name") or row.get("ticker"),
                "universe_bucket": row.get("bucket") or "",
                "raw_score": round(float(score), 6),
                "normalized_score": round(float(score), 6),
                "rank": rank,
                "action": action,
                "signal_strength": strength,
                "entry_score": round(float(score), 6),
                "exit_score": None,
                "risk_penalty": meta["risk_penalty"],
                "liquidity_penalty": meta["liquidity_penalty"],
                "reason_code_1": meta["reason_code_1"],
                "reason_code_2": meta["reason_code_2"],
                "reason_code_3": meta["reason_code_3"],
                "reason_text": reason_text,
                "is_trade_candidate": is_trade,
                "is_watch_candidate": is_watch,
                "is_ignored": is_ignored,
                "created_at": created_at,
            })
    if not rows:
        return _empty_agent_scores_frame()
    return pd.DataFrame(rows, columns=_empty_agent_scores_frame().columns)
