"""Contamination pattern detection from synthetic water-quality readings."""

from __future__ import annotations

import numpy as np
import pandas as pd


def detect_contamination_events(readings: pd.DataFrame, anomalies: pd.DataFrame | None = None) -> pd.DataFrame:
    """Detect station-time contamination patterns from multiple parameter signals."""
    pivot = readings.pivot_table(index=["station_id", "region", "plant_id", "timestamp"], columns="parameter", values="value", aggfunc="mean").reset_index()
    if pivot.empty:
        return pd.DataFrame(columns=_columns())
    for col in ["turbidity_ntu", "chlorine_mg_l", "nitrate_mg_l", "ecoli_proxy_cfu", "dissolved_oxygen_mg_l", "conductivity_us_cm"]:
        if col not in pivot.columns:
            pivot[col] = np.nan
    pivot["turbidity_signal"] = _clip01((pivot["turbidity_ntu"].fillna(0) - 2.0) / 6.0)
    pivot["chlorine_drop_signal"] = _clip01((0.45 - pivot["chlorine_mg_l"].fillna(0.85)) / 0.45)
    pivot["nitrate_signal"] = _clip01((pivot["nitrate_mg_l"].fillna(0) - 4.0) / 8.0)
    pivot["microbial_proxy_signal"] = _clip01((pivot["ecoli_proxy_cfu"].fillna(0) - 1.0) / 20.0)
    pivot["oxygen_stress_signal"] = _clip01((5.0 - pivot["dissolved_oxygen_mg_l"].fillna(7.0)) / 3.0)
    pivot["conductivity_signal"] = _clip01((pivot["conductivity_us_cm"].fillna(500) - 800) / 450.0)
    pivot["contamination_score"] = _clip01(
        0.25 * pivot["turbidity_signal"]
        + 0.23 * pivot["chlorine_drop_signal"]
        + 0.20 * pivot["nitrate_signal"]
        + 0.22 * pivot["microbial_proxy_signal"]
        + 0.06 * pivot["oxygen_stress_signal"]
        + 0.04 * pivot["conductivity_signal"]
    )
    pivot["contamination_pattern"] = pivot.apply(_pattern, axis=1)
    pivot["contamination_risk_band"] = pivot["contamination_score"].apply(_band)
    events = pivot.loc[pivot["contamination_score"] >= 0.35].copy()
    if events.empty:
        return pd.DataFrame(columns=_columns())
    cols = _columns()
    return events.assign(contamination_score=events["contamination_score"].round(4))[cols].sort_values(
        ["contamination_score", "station_id", "timestamp"], ascending=[False, True, True]
    ).reset_index(drop=True)


def contamination_station_summary(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize contamination pattern burden by station."""
    if events.empty:
        return pd.DataFrame(columns=["station_id", "event_count", "max_contamination_score", "dominant_pattern"])
    return events.groupby("station_id", as_index=False).agg(
        event_count=("timestamp", "count"),
        max_contamination_score=("contamination_score", "max"),
        dominant_pattern=("contamination_pattern", lambda s: s.value_counts().index[0]),
    ).sort_values(["max_contamination_score", "event_count"], ascending=[False, False]).reset_index(drop=True)


def _clip01(values):
    return np.clip(values, 0, 1)


def _pattern(row) -> str:
    signals = []
    if row.turbidity_signal >= 0.45:
        signals.append("turbidity_surge")
    if row.chlorine_drop_signal >= 0.45:
        signals.append("chlorine_residual_drop")
    if row.nitrate_signal >= 0.45:
        signals.append("nitrate_spike")
    if row.microbial_proxy_signal >= 0.45:
        signals.append("microbial_proxy_increase")
    if row.oxygen_stress_signal >= 0.45:
        signals.append("oxygen_stress")
    return "|".join(signals) if signals else "multi_parameter_watch"


def _band(score: float) -> str:
    if score >= 0.70:
        return "critical_review"
    if score >= 0.52:
        return "elevated_review"
    return "watch"


def _columns() -> list[str]:
    return [
        "station_id", "region", "plant_id", "timestamp", "contamination_score", "contamination_risk_band",
        "contamination_pattern", "turbidity_signal", "chlorine_drop_signal", "nitrate_signal",
        "microbial_proxy_signal", "oxygen_stress_signal", "conductivity_signal",
    ]
