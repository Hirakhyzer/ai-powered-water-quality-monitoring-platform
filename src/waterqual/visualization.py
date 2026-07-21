"""Matplotlib visualizations for synthetic water-quality monitoring."""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def _save(fig, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_anomaly_counts(anomalies: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    if anomalies.empty:
        ax.text(0.5, 0.5, "No anomalies detected", ha="center", va="center")
    else:
        anomalies["anomaly_type"].value_counts().sort_values().plot(kind="barh", ax=ax)
    ax.set_title("Synthetic sensor anomaly counts")
    ax.set_xlabel("count")
    _save(fig, path)


def plot_contamination_risk(events: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    if events.empty:
        ax.text(0.5, 0.5, "No contamination events detected", ha="center", va="center")
    else:
        top = events.groupby("station_id")["contamination_score"].max().sort_values(ascending=False).head(12).sort_values()
        top.plot(kind="barh", ax=ax)
    ax.set_title("Maximum contamination score by station")
    ax.set_xlabel("score")
    _save(fig, path)


def plot_treatment_risk(risk: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    if risk.empty:
        ax.text(0.5, 0.5, "No risk rows", ha="center", va="center")
    else:
        risk.sort_values("treatment_risk_score").tail(12).plot(x="station_id", y="treatment_risk_score", kind="barh", ax=ax, legend=False)
    ax.set_title("Treatment risk score by station")
    ax.set_xlabel("risk score")
    _save(fig, path)


def plot_alert_priority(alerts: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    if alerts.empty:
        ax.text(0.5, 0.5, "No alert signals", ha="center", va="center")
    else:
        alerts["alert_priority"].value_counts().sort_index().plot(kind="bar", ax=ax)
    ax.set_title("Synthetic alert priority distribution")
    ax.set_ylabel("station count")
    _save(fig, path)


def plot_parameter_trends(readings: pd.DataFrame, path: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    subset = readings.loc[readings["parameter"].isin(["turbidity_ntu", "chlorine_mg_l", "nitrate_mg_l"])].copy()
    if subset.empty:
        ax.text(0.5, 0.5, "No trend data", ha="center", va="center")
    else:
        subset["timestamp"] = pd.to_datetime(subset["timestamp"])
        trend = subset.groupby(["timestamp", "parameter"], as_index=False)["value"].mean()
        for parameter, group in trend.groupby("parameter"):
            ax.plot(group["timestamp"], group["value"], label=parameter)
        ax.legend()
    ax.set_title("Mean parameter trends across synthetic stations")
    ax.set_xlabel("timestamp")
    ax.set_ylabel("mean value")
    _save(fig, path)
