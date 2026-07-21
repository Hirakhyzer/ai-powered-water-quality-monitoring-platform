# Methodology

The lab follows a transparent synthetic-review workflow:

1. Generate fictional treatment plants, stations, and hourly sensor readings.
2. Inject synthetic contamination episodes and sensor drift.
3. Detect missing readings, outliers, operational-range violations, and drift flags.
4. Combine multi-parameter signals into contamination pattern scores.
5. Score station and treatment-plant risk using contamination burden, anomaly burden, treatment reliability, chlorine residual pressure, and vulnerability.
6. Generate internal alert-priority signals for human review.
7. Write reports, figures, and a hash-chained audit ledger.

The system uses transparent heuristics so researchers can inspect every decision. It is not a certified public-health system.
