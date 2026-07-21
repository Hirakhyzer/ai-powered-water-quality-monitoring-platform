"""Synthetic public-health alert signal generation.

These are review signals only, not official public-health warnings.
"""

from __future__ import annotations

import pandas as pd


def public_health_alert_signals(stations: pd.DataFrame, risk: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Create station-level alert-priority signals for human review."""
    recent_events = events.groupby("station_id").agg(
        recent_event_count=("timestamp", "count"),
        max_event_score=("contamination_score", "max"),
        latest_pattern=("contamination_pattern", lambda s: s.iloc[0] if len(s) else "none"),
    ).reset_index() if not events.empty else pd.DataFrame(columns=["station_id", "recent_event_count", "max_event_score", "latest_pattern"])
    frame = risk.merge(stations[["station_id", "supply_zone", "sensor_reliability"]], on="station_id", how="left").merge(recent_events, on="station_id", how="left")
    frame["recent_event_count"] = frame["recent_event_count"].fillna(0).astype(int)
    frame["max_event_score"] = frame["max_event_score"].fillna(0.0)
    frame["latest_pattern"] = frame["latest_pattern"].fillna("none")
    frame["alert_score"] = (
        0.48 * frame["treatment_risk_score"].astype(float)
        + 0.22 * frame["max_event_score"].astype(float)
        + 0.14 * (frame["recent_event_count"].clip(upper=12) / 12.0)
        + 0.10 * frame["vulnerability_index"].astype(float)
        + 0.06 * (1 - frame["sensor_reliability"].astype(float))
    ).clip(0, 1)
    frame["alert_priority"] = frame["alert_score"].apply(_priority)
    frame["alert_signal"] = frame.apply(_signal, axis=1)
    frame["public_message_boundary"] = "internal synthetic review signal only; not a public warning"
    cols = [
        "station_id", "station_name", "region", "supply_zone", "plant_id", "population_served",
        "alert_score", "alert_priority", "alert_signal", "risk_drivers", "latest_pattern", "public_message_boundary",
    ]
    return frame.assign(alert_score=frame["alert_score"].round(4)).loc[:, cols].sort_values("alert_score", ascending=False).reset_index(drop=True)


def _priority(score: float) -> str:
    if score >= 0.68:
        return "critical_review"
    if score >= 0.50:
        return "elevated_review"
    if score >= 0.30:
        return "watch"
    return "routine"


def _signal(row) -> str:
    if row.alert_priority == "critical_review":
        return "Immediate expert review, confirmatory sampling, and utility procedure check recommended."
    if row.alert_priority == "elevated_review":
        return "Prioritize operational review and verify sensor calibration before public communication."
    if row.alert_priority == "watch":
        return "Monitor trend and compare with nearby stations and laboratory confirmation workflow."
    return "Routine monitoring signal."
