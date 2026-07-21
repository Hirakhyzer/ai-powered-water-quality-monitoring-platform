"""Treatment and station risk scoring."""

from __future__ import annotations

import numpy as np
import pandas as pd


def treatment_risk_table(stations: pd.DataFrame, plants: pd.DataFrame, readings: pd.DataFrame, anomalies: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Compute station-level treatment-risk scores from anomalies and contamination events."""
    station_base = stations.merge(plants[["plant_id", "treatment_reliability", "chlorine_control_quality", "plant_type"]], on="plant_id", how="left")
    anomaly_counts = anomalies.groupby("station_id").agg(
        anomaly_count=("anomaly_type", "count"),
        mean_anomaly_severity=("severity_score", "mean"),
        max_anomaly_severity=("severity_score", "max"),
    ).reset_index() if not anomalies.empty else pd.DataFrame(columns=["station_id", "anomaly_count", "mean_anomaly_severity", "max_anomaly_severity"])
    event_counts = events.groupby("station_id").agg(
        contamination_event_count=("timestamp", "count"),
        max_contamination_score=("contamination_score", "max"),
        mean_contamination_score=("contamination_score", "mean"),
    ).reset_index() if not events.empty else pd.DataFrame(columns=["station_id", "contamination_event_count", "max_contamination_score", "mean_contamination_score"])
    pivot = readings.pivot_table(index="station_id", columns="parameter", values="value", aggfunc="mean").reset_index()
    frame = station_base.merge(anomaly_counts, on="station_id", how="left").merge(event_counts, on="station_id", how="left").merge(pivot, on="station_id", how="left")
    for col in ["anomaly_count", "mean_anomaly_severity", "max_anomaly_severity", "contamination_event_count", "max_contamination_score", "mean_contamination_score"]:
        frame[col] = frame[col].fillna(0.0)
    station_count_scale = max(float(frame["anomaly_count"].max()), 1.0)
    event_count_scale = max(float(frame["contamination_event_count"].max()), 1.0)
    frame["anomaly_burden"] = np.clip(frame["anomaly_count"] / station_count_scale, 0, 1)
    frame["event_burden"] = np.clip(frame["contamination_event_count"] / event_count_scale, 0, 1)
    frame["treatment_weakness"] = np.clip(1 - 0.55 * frame["treatment_reliability"].fillna(0.8) - 0.45 * frame["chlorine_control_quality"].fillna(0.8), 0, 1)
    frame["chlorine_residual_pressure"] = np.clip((0.55 - frame.get("chlorine_mg_l", 0.8).fillna(0.8)) / 0.55, 0, 1)
    frame["treatment_risk_score"] = np.clip(
        0.34 * frame["max_contamination_score"].astype(float)
        + 0.20 * frame["event_burden"].astype(float)
        + 0.18 * frame["anomaly_burden"].astype(float)
        + 0.14 * frame["treatment_weakness"].astype(float)
        + 0.08 * frame["chlorine_residual_pressure"].astype(float)
        + 0.06 * frame["vulnerability_index"].astype(float),
        0,
        1,
    )
    frame["treatment_risk_band"] = frame["treatment_risk_score"].apply(_risk_band)
    frame["risk_drivers"] = frame.apply(_risk_drivers, axis=1)
    cols = [
        "station_id", "station_name", "region", "plant_id", "plant_type", "population_served", "vulnerability_index",
        "anomaly_count", "contamination_event_count", "max_contamination_score", "treatment_weakness",
        "chlorine_residual_pressure", "treatment_risk_score", "treatment_risk_band", "risk_drivers",
    ]
    return frame.assign(treatment_risk_score=frame["treatment_risk_score"].round(4)).loc[:, cols].sort_values("treatment_risk_score", ascending=False).reset_index(drop=True)


def station_risk_summary(risk: pd.DataFrame) -> pd.DataFrame:
    """Aggregate station risk by region and plant."""
    if risk.empty:
        return pd.DataFrame(columns=["region", "plant_id", "station_count", "mean_treatment_risk_score", "high_or_critical_count"])
    return risk.groupby(["region", "plant_id"], as_index=False).agg(
        station_count=("station_id", "count"),
        mean_treatment_risk_score=("treatment_risk_score", "mean"),
        max_treatment_risk_score=("treatment_risk_score", "max"),
        high_or_critical_count=("treatment_risk_band", lambda s: int(s.isin(["high", "critical"]).sum())),
    ).sort_values("max_treatment_risk_score", ascending=False).reset_index(drop=True)


def summarize_risk(risk: pd.DataFrame, alerts: pd.DataFrame | None = None) -> dict[str, float | int | str]:
    """Compact summary for JSON and reports."""
    return {
        "station_count": int(len(risk)),
        "mean_treatment_risk_score": float(risk["treatment_risk_score"].mean()) if len(risk) else 0.0,
        "high_or_critical_station_count": int(risk["treatment_risk_band"].isin(["high", "critical"]).sum()) if len(risk) else 0,
        "critical_alert_signal_count": int((alerts["alert_priority"] == "critical_review").sum()) if alerts is not None and len(alerts) else 0,
        "data_origin": "synthetic fictional water-quality monitoring records",
        "decision_boundary": "research review support only; not official water safety certification or public-health alerting",
    }


def _risk_band(score: float) -> str:
    if score >= 0.72:
        return "critical"
    if score >= 0.54:
        return "high"
    if score >= 0.34:
        return "medium"
    return "low"


def _risk_drivers(row) -> str:
    drivers = []
    if float(row.max_contamination_score) >= 0.50:
        drivers.append("contamination_pattern")
    if float(row.anomaly_burden) >= 0.45:
        drivers.append("sensor_anomaly_burden")
    if float(row.treatment_weakness) >= 0.30:
        drivers.append("treatment_reliability")
    if float(row.chlorine_residual_pressure) >= 0.30:
        drivers.append("chlorine_residual_pressure")
    if float(row.vulnerability_index) >= 0.60:
        drivers.append("population_vulnerability")
    return "|".join(drivers) if drivers else "routine_monitoring"
