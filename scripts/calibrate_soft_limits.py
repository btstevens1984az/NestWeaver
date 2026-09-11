#!/usr/bin/env python3
"""Interactive helper to draft soft-limit YAML from measured reach."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    print("NestWeaver soft-limit calibration helper")
    print("Enter measured values in meters / rad (blank = keep default).\n")
    defaults = {
        "z_min": 0.05,
        "z_max": 1.2,
        "max_linear_speed_mps": 0.6,
        "torque_limit_nm": 8.0,
    }
    out = {}
    for key, default in defaults.items():
        raw = input(f"{key} [{default}]: ").strip()
        out[key] = float(raw) if raw else default
    path = Path("configs/safety/calibrated_snippet.json")
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"Wrote {path} — merge into configs/safety/default.yaml as needed.")


if __name__ == "__main__":
    main()
