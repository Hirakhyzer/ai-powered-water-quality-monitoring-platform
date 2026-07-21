# Synthetic lab

The synthetic lab is designed to run without any real sensor or public-health data.

Default scenario:

- 18 monitoring stations
- 4 treatment plants
- 168 hourly readings per station
- 8 water-quality parameters
- injected contamination episodes
- injected sensor drift
- probabilistic missing readings

Run:

```bash
python scripts/run_synthetic_water_lab.py --stations 18 --hours 168 --seed 42
```

The output tables and figures are written under `outputs/`.
