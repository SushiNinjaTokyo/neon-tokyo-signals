from __future__ import annotations

import math
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
    r5 = nz(row.get("return_5d_pct"), 0.0)
    r20 = nz(row.get("return_20d_pct"), 0.0)
    r60 = nz(row.get("return_60d_pct"), 0.0)
    vs20 = nz(row.get("price_vs_ma20_pct"), 0.0)
    vs50 = nz(row.get("price_vs_ma50_pct"), 0.0)
    dd60 = nz(row.get("max_drawdown_60d_pct"), -50.0)
    dist52 = nz(row.get("distance_from_52w_high_pct"), -100.0)
    range60 = nz(row.get("range_position_60d_0_1"), 0.0)
    vol60 = nz(row.get("volatility_60d_annualized_pct"), 80.0)
    dryup = nz(row.get("volume_dryup_10d"), 1.0)
    value_rerate = scale(r60, -10, 25) * 0.35 + scale(row.get("distance_from_52w_low_pct"), 5, 80) * 0.25 + scale(liq, 0.2, 0.9) * 0.20 + scale(-dist52, 10, 65) * 0.20

    if profile.id == "daily_striker":
        raw = mom * 0.46 + trend_d * 0.22 + liq * 0.18 + scale(-dist52, 0, 22) * 0.06 + scale(r5, 0, 15) * 0.08
        reasons = ["short_momentum", "volume_pressure", "liquid_tape"]
    elif profile.id == "weekly_sage":
        raw = trend_w * 0.52 + scale(r60, 0, 35) * 0.18 + scale(vs50, -3, 14) * 0.12 + liq * 0.10 + (1 - scale(vol60, 35, 100)) * 0.08
        reasons = ["weekly_flow", "trend_structure", "relative_strength"]
    elif profile.id == "risk_sentinel":
        raw = risk * 0.55 + liq * 0.20 + trend_w * 0.10 + (1 - scale(abs(vs20), 0, 18)) * 0.08 + scale(dd60, -30, -4) * 0.07
        reasons = ["liquidity_guard", "drawdown_control", "survivable_setup"]
    elif profile.id == "discovery_scout":
        small_bonus = 1.0 if bool(row.get("is_small_discovery")) else 0.35
        early = scale(r20, -5, 20) * 0.24 + scale(row.get("volume_ratio_20d"), 0.9, 4.0) * 0.26 + scale(range60, 0.25, 0.85) * 0.14
        raw = early + small_bonus * 0.16 + vol_re * 0.12 + liq * 0.08
        reasons = ["small_cap_discovery", "early_volume_shift", "hidden_alpha"]
    elif profile.id == "contrarian_monk":
        pullback = scale(-r5, 0.5, 9.0) * 0.24 + (1 - scale(abs(vs20), 0, 14)) * 0.14 + (1 - scale(dryup, 0.45, 1.4)) * 0.12
        raw = trend_w * 0.32 + pullback + liq * 0.12 + scale(range60, 0.35, 0.85) * 0.06
        reasons = ["patient_pullback", "trend_still_alive", "cooled_entry"]
    elif profile.id == "reversal_snapback":
        raw = rev * 0.54 + scale(-r5, 2, 16) * 0.16 + vol_re * 0.12 + scale(row.get("distance_from_20d_low_pct"), 0, 14) * 0.08 + liq * 0.10
        reasons = ["oversold_exhaustion", "snapback_pressure", "reaccumulation"]
    elif profile.id == "value_mispricing":
        # Fundamentals are optional in Step 1.  Until fundamentals_latest is populated,
        # HIZUMI uses a conservative price-based re-rating proxy rather than low-PBR/PER claims.
        raw = value_rerate * 0.36 + risk * 0.18 + liq * 0.16 + scale(-dist52, 12, 70) * 0.14 + scale(r20, -3, 16) * 0.10 + (1 - scale(abs(vs50), 0, 35)) * 0.06
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


def build_agent_scores(features_with_universe: pd.DataFrame, as_of_date: str | None = None) -> pd.DataFrame:
    if features_with_universe.empty:
        return pd.DataFrame()
    df = features_with_universe.copy()
    if as_of_date:
        df = df[pd.to_datetime(df["date"]).dt.date.astype(str) <= as_of_date]
    latest_date = pd.to_datetime(df["date"]).max()
    latest = df[pd.to_datetime(df["date"]) == latest_date].copy()
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
    return pd.DataFrame(rows)
