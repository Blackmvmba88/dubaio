"""Run BMSC Physics v0.3 slow/fast validation scenarios."""

from __future__ import annotations

import argparse

from v03_configs import V03_CONFIGS
from v03_dispatch import run_multi_day
from torsional_bench import run_loss_of_grid_demo


def cloudy_second_day(hour: float) -> float:
    """Synthetic cloud event: strong attenuation on day 2 from 10:00 to 13:00."""
    day = int(hour // 24.0)
    h = hour % 24.0
    if day == 1 and 10.0 <= h < 13.0:
        return 0.25
    return 1.0


def grid_event(hour: float) -> bool:
    """Synthetic 30-minute grid outage on day 2 at 14:00."""
    day = int(hour // 24.0)
    h = hour % 24.0
    return not (day == 1 and 14.0 <= h < 14.5)


def run_dispatch(config_name: str, days: int, dt_sec: float) -> None:
    cfg = V03_CONFIGS[config_name]
    records = run_multi_day(
        cfg,
        days=days,
        dt_sec=dt_sec,
        cloud_profile=cloudy_second_day,
        grid_profile=grid_event,
    )

    dt_h = dt_sec / 3600.0
    electric_kwh = sum(r.electric_kw * dt_h for r in records)
    peak_kw = max(r.electric_kw for r in records)
    min_soc = min(r.storage_soc for r in records)
    max_soc = max(r.storage_soc for r in records)
    end_soc = records[-1].storage_soc
    rejected_kwh_th = sum(r.rejected_kw_th * dt_h for r in records)

    print(f"BMSC Physics v0.3 dispatch — {config_name}")
    print("-" * 64)
    print(f"days                    : {days}")
    print(f"electric energy         : {electric_kwh:,.2f} kWh_e")
    print(f"peak electrical power   : {peak_kw:,.2f} kW_e")
    print(f"storage SOC min/max     : {min_soc:.3f} / {max_soc:.3f}")
    print(f"storage SOC final       : {end_soc:.3f}")
    print(f"rejected thermal energy : {rejected_kwh_th:,.2f} kWh_th")


def run_torsion(config_name: str, dt_sec: float) -> None:
    cfg = V03_CONFIGS[config_name]
    records = run_loss_of_grid_demo(cfg, duration_s=30.0, dt_sec=dt_sec)
    max_rpm = max(r["rpm_master"] for r in records)
    min_rpm = min(r["rpm_master"] for r in records)
    max_twist = max(abs(r["twist_mrad"]) for r in records)
    max_brake = max(r["tau_brake_knm"] for r in records)

    print(f"BMSC Physics v0.3 torsional bench — {config_name}")
    print("-" * 64)
    print(f"master RPM min/max      : {min_rpm:.4f} / {max_rpm:.4f}")
    print(f"max shaft twist         : {max_twist:.4f} mrad")
    print(f"max passive brake torque: {max_brake:,.3f} kN*m")


def main() -> None:
    parser = argparse.ArgumentParser(description="BMSC Physics v0.3 scenario runner")
    parser.add_argument("--config", choices=sorted(V03_CONFIGS), default="10kw")
    parser.add_argument("--mode", choices=("dispatch", "torsion"), default="dispatch")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--dt", type=float, default=None)
    args = parser.parse_args()

    if args.mode == "dispatch":
        run_dispatch(args.config, days=args.days, dt_sec=args.dt or 60.0)
    else:
        run_torsion(args.config, dt_sec=args.dt or 0.01)


if __name__ == "__main__":
    main()
