"""Sensor anomaly and data-quality checks."""

from __future__ import annotations

import numpy as np
import pandas as pd

LIMITS = {
    "ph": (6.5, 8.5),
    "turbidity_ntu": (0.0, 5.0),
    "chlorine_mg_l": (0.2, 4.0),
    "dissolved_oxygen_mg_l": (4.0, 14.0),
    "conductivity_us_cm": (0.0, 1000.0),
    "nitrate_mg_l": (0.0, 10.0),
    "temperature_c": (0.0, 35.0),
    "ecoli_proxy_cfu": (0.0, 1.0),
}


def detect_sensor_anomalies(readings: pd.DataFrame) -> pd.DataFrame:
    """Detect missing data, robust outliers, range violations, and drift flags."""
    rows = []
    stats = _robust_stats(readings)
    for row in readings.itertuples(index=False):
        value = getattr(row, "value")
        parameter = row.parameter
        if pd.isna(value):
            rows.append(_row(row, parameter, np.nan, "missing_reading", 0.55, "Sensor reading is missing and should be reviewed."))
            continue
        low, high = LIMITS.get(parameter, (-np.inf, np.inf))
        if float(value) < low or float(value) > high:
            severity = min(1.0, abs(float(value) - np.clip(float(value), low, high)) / max(high - low, 1.0) + 0.62)
            rows.append(_row(row, parameter, value, "operational_range_violation", severity, "Reading is outside the transparent review range."))
        z = _robust_z(float(value), stats.get(parameter, (0.0, 1.0)))
        if abs(z) >= 3.5:
            rows.append(_row(row, parameter, value, "statistical_outlier", min(1.0, abs(z) / 6.0), "Reading is a robust statistical outlier for this parameter."))
        if int(getattr(row, "synthetic_sensor_drift_active", 0)) == 1 and parameter in {"ph", "conductivity_us_cm"}:
            rows.append(_row(row, parameter, value, "sensor_drift_signal", 0.60, "Synthetic drift flag indicates gradual sensor deviation."))
    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["station_id", "timestamp", "region", "plant_id", "parameter", "value", "anomaly_type", "severity_score", "review_note"])
    return out.sort_values(["severity_score", "station_id", "timestamp"], ascending=[False, True, True]).reset_index(drop=True)


def anomaly_summary(anomalies: pd.DataFrame) -> pd.DataFrame:
    """Aggregate anomaly burden by station and parameter."""
    if anomalies.empty:
        return pd.DataFrame(columns=["station_id", "parameter", "anomaly_count", "mean_severity_score", "max_severity_score"])
    return anomalies.groupby(["station_id", "parameter"], as_index=False).agg(
        anomaly_count=("anomaly_type", "count"),
        mean_severity_score=("severity_score", "mean"),
        max_severity_score=("severity_score", "max"),
    ).sort_values(["anomaly_count", "max_severity_score"], ascending=[False, False]).reset_index(drop=True)


def _robust_stats(readings: pd.DataFrame) -> dict[str, tuple[float, float]]:
    stats: dict[str, tuple[float, float]] = {}
    for parameter, group in readings.dropna(subset=["value"]).groupby("parameter"):
        values = group["value"].astype(float)
        median = float(values.median())
        mad = float((values - median).abs().median())
        stats[str(parameter)] = (median, max(mad, 1e-6))
    return stats


def _robust_z(value: float, stat: tuple[float, float]) -> float:
    median, mad = stat
    return 0.6745 * (value - median) / max(mad, 1e-6)


def _row(row, parameter: str, value: float, anomaly_type: str, severity: float, note: str) -> dict:
    return {
        "station_id": row.station_id,
        "timestamp": row.timestamp,
        "region": row.region,
        "plant_id": row.plant_id,
        "parameter": parameter,
        "value": value,
        "anomaly_type": anomaly_type,
        "severity_score": round(float(np.clip(severity, 0, 1)), 4),
        "review_note": note,
    }
