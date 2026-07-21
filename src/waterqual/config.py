"""Configuration helpers for local synthetic water-quality runs."""

from __future__ import annotations

from pathlib import Path
import random
import numpy as np


def set_seed(seed: int) -> None:
    """Set deterministic seeds for reproducible synthetic experiments."""
    random.seed(seed)
    np.random.seed(seed)


def ensure_output_dirs(base: str | Path = "outputs") -> dict[str, Path]:
    """Create the standard output directory tree."""
    root = Path(base)
    paths = {
        "root": root,
        "results": root / "results",
        "figures": root / "figures",
        "reports": root / "reports",
        "audit": root / "audit",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
