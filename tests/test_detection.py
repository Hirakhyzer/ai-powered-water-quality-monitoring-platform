from waterqual.alerts import public_health_alert_signals
from waterqual.anomalies import detect_sensor_anomalies
from waterqual.contamination import detect_contamination_events
from waterqual.risk import treatment_risk_table
from waterqual.synthetic import SyntheticWaterConfig, generate_synthetic_water_data


def _sample():
    data = generate_synthetic_water_data(SyntheticWaterConfig(stations=10, hours=72, seed=5))
    anomalies = detect_sensor_anomalies(data["readings"])
    events = detect_contamination_events(data["readings"], anomalies)
    risk = treatment_risk_table(data["stations"], data["plants"], data["readings"], anomalies, events)
    alerts = public_health_alert_signals(data["stations"], risk, events)
    return data, anomalies, events, risk, alerts


def test_anomaly_and_event_tables_have_expected_columns():
    _, anomalies, events, risk, alerts = _sample()
    assert {"station_id", "parameter", "anomaly_type", "severity_score"}.issubset(anomalies.columns)
    assert {"station_id", "contamination_score", "contamination_risk_band"}.issubset(events.columns)
    assert {"station_id", "treatment_risk_score", "treatment_risk_band"}.issubset(risk.columns)
    assert {"station_id", "alert_score", "alert_priority"}.issubset(alerts.columns)


def test_risk_scores_are_bounded():
    _, _, _, risk, alerts = _sample()
    assert ((risk["treatment_risk_score"] >= 0) & (risk["treatment_risk_score"] <= 1)).all()
    assert ((alerts["alert_score"] >= 0) & (alerts["alert_score"] <= 1)).all()
