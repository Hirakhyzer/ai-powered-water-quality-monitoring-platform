"""Markdown reporting for synthetic water-quality monitoring outputs."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def _table(frame: pd.DataFrame, limit: int = 10) -> str:
    if frame is None or frame.empty:
        return "No rows."
    return frame.head(limit).to_markdown(index=False)


def write_report(
    path: str | Path,
    summary: dict,
    risk: pd.DataFrame,
    alerts: pd.DataFrame,
    anomalies: pd.DataFrame,
    events: pd.DataFrame,
    station_summary: pd.DataFrame,
) -> None:
    """Write a reproducible Markdown report."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = f"""# Synthetic Water Quality Monitoring Report

## Boundary

This report is generated from fictional synthetic water-quality data. It is for research and decision-support review only. It is not an official public-health warning, water-safety certification, treatment directive, or regulatory finding.

## Summary

| Metric | Value |
| --- | ---: |
| Station count | {summary.get('station_count', 0)} |
| Treatment plant count | {summary.get('plant_count', 0)} |
| Reading count | {summary.get('reading_count', 0)} |
| Sensor anomaly count | {summary.get('anomaly_count', 0)} |
| Contamination event count | {summary.get('contamination_event_count', 0)} |
| Mean treatment risk score | {summary.get('mean_treatment_risk_score', 0):.3f} |
| High or critical station count | {summary.get('high_or_critical_station_count', 0)} |
| Critical alert signal count | {summary.get('critical_alert_signal_count', 0)} |

## Highest treatment-risk stations

{_table(risk[["station_id", "region", "plant_id", "treatment_risk_score", "treatment_risk_band", "risk_drivers"]] if not risk.empty else risk)}

## Alert-priority signals

{_table(alerts[["station_id", "region", "alert_score", "alert_priority", "alert_signal"]] if not alerts.empty else alerts)}

## Sensor anomaly examples

{_table(anomalies[["station_id", "timestamp", "parameter", "anomaly_type", "severity_score"]] if not anomalies.empty else anomalies)}

## Contamination pattern examples

{_table(events[["station_id", "timestamp", "contamination_score", "contamination_risk_band", "contamination_pattern"]] if not events.empty else events)}

## Regional station-risk summary

{_table(station_summary)}

## Governance notes

- Confirm any high-risk signal with calibrated sensors and certified laboratory testing.
- Treat alert-priority rows as internal review prompts only.
- Validate thresholds and response protocols with utilities, environmental specialists, public-health authorities, and regulators before real deployment.
- Preserve audit logs for reproducibility and post-review accountability.
"""
    path.write_text(report, encoding="utf-8")
