"""Run a 24-hour BMSC simulation and print/export summary metrics."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from configs import CONFIGS
from engine import run_day_simulation


def integrate_kwh(records, key: str, dt_sec: float) -> float:
    values_kw = np.array([row[key] for row in records], dtype=float)
    return float(np.sum(values_kw) * dt_sec / 3600.0)


def summarize(records, dt_sec: float):
    p_e = np.array([row["p_electric_kw"] for row in records], dtype=float)
    rpm_master = np.array([row["rpm_master"] for row in records], dtype=float)
    rpm_gen = np.array([row["rpm_gen"] for row in records], dtype=float)

    return {
        "solar_optical_kwh": integrate_kwh(records, "p_opt_kw", dt_sec),
        "receiver_kwh_th": integrate_kwh(records, "p_rec_kw", dt_sec),
        "cycle_input_kwh_th": integrate_kwh(records, "p_th_cycle_kw", dt_sec),
        "electric_kwh": integrate_kwh(records, "p_electric_kw", dt_sec),
        "electric_peak_kw": float(np.max(p_e)),
        "master_peak_rpm": float(np.max(rpm_master)),
        "generator_peak_rpm": float(np.max(rpm_gen)),
        "storage_end_mwh_th": float(records[-1]["E_th_mwh"]),
    }


def write_csv(records, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="BlackMamba Solar Clock day-cycle simulator")
    parser.add_argument(
        "--config",
        choices=sorted(CONFIGS),
        default="10kw",
        help="Parameter set to simulate",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=1.0,
        help="Integration step in seconds (v0.2 baseline: 1 s)",
    )
    parser.add_argument("--csv", type=Path, default=None, help="Optional output CSV path")
    args = parser.parse_args()

    if args.dt <= 0:
        parser.error("--dt must be greater than zero")

    config = CONFIGS[args.config]
    records = run_day_simulation(config, dt_sec=args.dt)
    summary = summarize(records, dt_sec=args.dt)

    print(f"BMSC Physics v0.2 — {config['name']}")
    print("-" * 60)
    for key, value in summary.items():
        print(f"{key:28s}: {value:,.3f}")

    if args.csv is not None:
        write_csv(records, args.csv)
        print(f"CSV written to: {args.csv}")


if __name__ == "__main__":
    main()
