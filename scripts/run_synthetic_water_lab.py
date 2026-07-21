"""Run the complete synthetic AI-powered water quality monitoring lab.

The command uses only fictional stations, treatment plants, sensors, readings,
and alert signals. It demonstrates anomaly detection, contamination pattern
analysis, treatment-risk scoring, public-health alert signal review, reporting,
figures, and a hash-chained audit log without real public-health data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from waterqual.alerts import public_health_alert_signals
from waterqual.anomalies import anomaly_summary, detect_sensor_anomalies
from waterqual.audit import append_record, verify_log
from waterqual.config import ensure_output_dirs, set_seed
from waterqual.contamination import contamination_station_summary, detect_contamination_events
from waterqual.reporting import write_report
from waterqual.risk import station_risk_summary, summarize_risk, treatment_risk_table
from waterqual.synthetic import SyntheticWaterConfig, generate_synthetic_water_data
from waterqual.visualization import (
    plot_alert_priority,
    plot_anomaly_counts,
    plot_contamination_risk,
    plot_parameter_trends,
    plot_treatment_risk,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a synthetic water quality monitoring platform lab.")
    parser.add_argument("--stations", type=int, default=18)
    parser.add_argument("--hours", type=int, default=168)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    set_seed(args.seed)
    outputs = ensure_output_dirs(args.output_dir)
    data = generate_synthetic_water_data(SyntheticWaterConfig(stations=args.stations, hours=args.hours, seed=args.seed))
    plants = data["plants"]
    stations = data["stations"]
    readings = data["readings"]

    anomalies = detect_sensor_anomalies(readings)
    anomaly_stats = anomaly_summary(anomalies)
    events = detect_contamination_events(readings, anomalies)
    event_stats = contamination_station_summary(events)
    risk = treatment_risk_table(stations, plants, readings, anomalies, events)
    alerts = public_health_alert_signals(stations, risk, events)
    station_summary = station_risk_summary(risk)

    summary = summarize_risk(risk, alerts)
    summary.update({
        "seed": args.seed,
        "plant_count": int(len(plants)),
        "reading_count": int(len(readings)),
        "anomaly_count": int(len(anomalies)),
        "contamination_event_count": int(len(events)),
        "alert_signal_count": int(len(alerts)),
    })

    plants.to_csv(outputs["results"] / "synthetic_treatment_plants.csv", index=False)
    stations.to_csv(outputs["results"] / "synthetic_stations.csv", index=False)
    readings.to_csv(outputs["results"] / "synthetic_sensor_readings.csv", index=False)
    anomalies.to_csv(outputs["results"] / "synthetic_sensor_anomalies.csv", index=False)
    anomaly_stats.to_csv(outputs["results"] / "synthetic_anomaly_summary.csv", index=False)
    events.to_csv(outputs["results"] / "synthetic_contamination_events.csv", index=False)
    event_stats.to_csv(outputs["results"] / "synthetic_contamination_station_summary.csv", index=False)
    risk.to_csv(outputs["results"] / "synthetic_treatment_risk.csv", index=False)
    alerts.to_csv(outputs["results"] / "synthetic_alert_signals.csv", index=False)
    station_summary.to_csv(outputs["results"] / "synthetic_station_risk_summary.csv", index=False)

    audit_path = outputs["audit"] / "water_quality_audit_log.jsonl"
    append_record(audit_path, {**summary, "boundary": "synthetic environmental safety review support only"})
    summary["audit_log"] = verify_log(audit_path)
    (outputs["results"] / "synthetic_water_quality_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    write_report(outputs["reports"] / "synthetic_water_quality_report.md", summary, risk, alerts, anomalies, events, station_summary)
    plot_anomaly_counts(anomalies, outputs["figures"] / "synthetic_anomaly_counts.png")
    plot_contamination_risk(events, outputs["figures"] / "synthetic_contamination_risk.png")
    plot_treatment_risk(risk, outputs["figures"] / "synthetic_treatment_risk.png")
    plot_alert_priority(alerts, outputs["figures"] / "synthetic_alert_priority.png")
    plot_parameter_trends(readings, outputs["figures"] / "synthetic_parameter_trends.png")

    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
