"""Deterministic synthetic water-quality sensor data.

All stations, treatment plants, sensors, readings, contamination episodes, and
alert signals are fictional. The data exists to test anomaly detection,
contamination pattern recognition, treatment-risk scoring, and reporting without
real public-health records.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

PARAMETERS = [
    "ph",
    "turbidity_ntu",
    "chlorine_mg_l",
    "dissolved_oxygen_mg_l",
    "conductivity_us_cm",
    "nitrate_mg_l",
    "temperature_c",
    "ecoli_proxy_cfu",
]
REGIONS = ["North Basin", "East Valley", "South Delta", "West Hills"]
PLANT_TYPES = ["surface_water", "groundwater", "blended_supply"]


@dataclass(frozen=True)
class SyntheticWaterConfig:
    stations: int = 18
    hours: int = 168
    seed: int = 42

    def __post_init__(self) -> None:
        if self.stations < 6:
            raise ValueError("Use at least 6 stations for regional risk analysis.")
        if self.hours < 48:
            raise ValueError("Use at least 48 hours for trend and anomaly analysis.")


def generate_synthetic_water_data(config: SyntheticWaterConfig | None = None) -> dict[str, pd.DataFrame]:
    """Generate fictional treatment plants, stations, and water-quality readings."""
    cfg = config or SyntheticWaterConfig()
    rng = np.random.default_rng(cfg.seed)
    plants = _treatment_plants(rng)
    stations = _stations(cfg, plants, rng)
    readings = _readings(stations, cfg, rng)
    return {"plants": plants, "stations": stations, "readings": readings}


def _treatment_plants(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for idx, region in enumerate(REGIONS):
        rows.append({
            "plant_id": f"P-{idx+1:02d}",
            "plant_name": f"{region} Treatment Plant",
            "region": region,
            "plant_type": PLANT_TYPES[idx % len(PLANT_TYPES)],
            "design_capacity_mgd": round(float(rng.uniform(4.5, 18.0)), 2),
            "treatment_reliability": round(float(np.clip(rng.normal(0.86, 0.07), 0.62, 0.98)), 3),
            "chlorine_control_quality": round(float(np.clip(rng.normal(0.82, 0.09), 0.55, 0.98)), 3),
        })
    return pd.DataFrame(rows)


def _stations(cfg: SyntheticWaterConfig, plants: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for idx in range(cfg.stations):
        plant = plants.iloc[idx % len(plants)]
        vulnerability = float(np.clip(rng.normal(0.42 + 0.08 * (idx % 3), 0.16), 0.05, 0.95))
        rows.append({
            "station_id": f"S-{idx+1:03d}",
            "station_name": f"{plant.region} Monitoring Station {idx+1:02d}",
            "region": plant.region,
            "plant_id": plant.plant_id,
            "supply_zone": f"Zone-{idx % 5 + 1}",
            "population_served": int(rng.integers(4_000, 65_000)),
            "vulnerability_index": round(vulnerability, 3),
            "sensor_reliability": round(float(np.clip(rng.normal(0.88, 0.08), 0.58, 0.99)), 3),
            "latitude": round(24.0 + idx * 0.18 + float(rng.normal(0, 0.04)), 4),
            "longitude": round(66.0 + (idx % 8) * 0.22 + float(rng.normal(0, 0.04)), 4),
        })
    return pd.DataFrame(rows)


def _readings(stations: pd.DataFrame, cfg: SyntheticWaterConfig, rng: np.random.Generator) -> pd.DataFrame:
    start = datetime(2026, 1, 1, 0, 0, 0)
    contamination_station_ids = set(stations.sample(n=max(2, len(stations) // 5), random_state=cfg.seed)["station_id"].tolist())
    drift_station_ids = set(stations.sample(n=max(1, len(stations) // 6), random_state=cfg.seed + 7)["station_id"].tolist())
    rows = []
    for station in stations.itertuples(index=False):
        plant_factor = 1.0 - float(station.sensor_reliability)
        event_start = int(rng.integers(max(8, cfg.hours // 5), max(10, cfg.hours - 18)))
        event_length = int(rng.integers(6, 18))
        drift_direction = float(rng.choice([-1, 1]))
        for hour in range(cfg.hours):
            timestamp = start + timedelta(hours=hour)
            daily = np.sin(2 * np.pi * (hour % 24) / 24)
            seasonal = np.sin(2 * np.pi * hour / max(cfg.hours, 1))
            event_active = station.station_id in contamination_station_ids and event_start <= hour < event_start + event_length
            drift_active = station.station_id in drift_station_ids and hour > cfg.hours * 0.45
            event_strength = float(np.clip((hour - event_start + 1) / max(event_length, 1), 0, 1)) if event_active else 0.0
            drift_strength = float((hour - cfg.hours * 0.45) / max(cfg.hours * 0.55, 1)) if drift_active else 0.0

            values = {
                "ph": 7.25 + rng.normal(0, 0.09) - 0.25 * event_strength + drift_direction * 0.35 * drift_strength,
                "turbidity_ntu": 0.9 + 0.20 * daily + rng.normal(0, 0.18) + 5.2 * event_strength,
                "chlorine_mg_l": 0.85 + rng.normal(0, 0.07) - 0.72 * event_strength - 0.12 * plant_factor,
                "dissolved_oxygen_mg_l": 7.2 + 0.30 * seasonal + rng.normal(0, 0.28) - 2.0 * event_strength,
                "conductivity_us_cm": 520 + rng.normal(0, 35) + 140 * event_strength + 180 * drift_strength,
                "nitrate_mg_l": 2.4 + rng.normal(0, 0.42) + 9.0 * event_strength,
                "temperature_c": 18.5 + 2.4 * daily + 1.2 * seasonal + rng.normal(0, 0.45),
                "ecoli_proxy_cfu": max(0.0, rng.normal(0.25, 0.35) + 22.0 * event_strength),
            }
            for parameter, value in values.items():
                missing = rng.random() > float(station.sensor_reliability) and rng.random() < 0.18
                rows.append({
                    "timestamp": timestamp.isoformat(),
                    "station_id": station.station_id,
                    "region": station.region,
                    "plant_id": station.plant_id,
                    "parameter": parameter,
                    "value": np.nan if missing else round(float(max(value, 0.0)), 4),
                    "unit": _unit(parameter),
                    "synthetic_event_active": int(event_active),
                    "synthetic_sensor_drift_active": int(drift_active and parameter in {"ph", "conductivity_us_cm"}),
                })
    return pd.DataFrame(rows)


def _unit(parameter: str) -> str:
    return {
        "ph": "pH units",
        "turbidity_ntu": "NTU",
        "chlorine_mg_l": "mg/L",
        "dissolved_oxygen_mg_l": "mg/L",
        "conductivity_us_cm": "uS/cm",
        "nitrate_mg_l": "mg/L",
        "temperature_c": "C",
        "ecoli_proxy_cfu": "synthetic CFU/100mL proxy",
    }[parameter]
