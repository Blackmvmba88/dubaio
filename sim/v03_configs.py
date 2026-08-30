"""Parameter overlays for BMSC Physics v0.3 transient studies."""

from __future__ import annotations

from configs import CONFIGS


def with_v03_dynamics(base_name: str):
    cfg = dict(CONFIGS[base_name])
    nominal_rpm = float(cfg.get("master_rpm_nominal", 1.8))

    # These are conceptual bench parameters, deliberately isolated from the
    # plant-sizing configuration so they cannot be mistaken for final hardware.
    scale = max(float(cfg["p_electric_rated"]) / 10_000.0, 1.0)
    cfg.update(
        {
            "bench_initial_rpm": nominal_rpm,
            "bench_initial_load_fraction": 1.0,
            "clutch_load_ramp_per_s": 0.35,
            "backlash_rad": 2.5e-5,
            "torsional_k_nm_rad": 2.0e6 * scale,
            "torsional_c_nms_rad": 2.0e4 * scale,
            "bench_b_master": 20.0 * scale,
            "bench_b_load_eq": 2.0 * scale,
            "overspeed_trip_rpm": nominal_rpm * 1.08,
            "overspeed_brake_nm_per_rpm": 1.5e5 * scale,
        }
    )
    return cfg


V03_CONFIGS = {name: with_v03_dynamics(name) for name in CONFIGS}
