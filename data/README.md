# Data policy

This repository is synthetic-first. The default pipeline generates fictional water stations, treatment plants, sensor readings, contamination episodes, sensor anomalies, and review signals.

Do not commit real drinking-water, laboratory, infrastructure, or public-health incident data to this repository unless the data has been approved for release by the responsible organization and reviewed for privacy, security, and regulatory risk.

Recommended local-only structure for real experiments:

```text
data/private/raw/
data/private/processed/
```

These paths should remain outside version control.
