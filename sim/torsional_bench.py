"""BMSC Physics v0.3 — fast torsional / clutch bench model.

This model resolves the mechanical timescale separately from the multi-day solar
energy model. All generator-side inertia is reflected to the master-shaft side
so the two inertias can be integrated in one coordinate system.

Concept-validation only. Parameters are placeholders, not component sizing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TorsionalState:
    theta_master: float = 0.0
    theta_load_eq: float = 0.0
    omega_master: float = 0.0
    omega_load_eq: float = 0.0
    load_fraction: float = 0.0


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


class TorsionalBench:
    """Two-inertia drivetrain with backlash, compliance and load ramping."""

    def __init__(self, config: Dict[str, float]):
        self.cfg = dict(config)
        self.ratio = math.prod(self.cfg.get("stage_ratios", [1.0]))
        self.eta_drive = self.cfg["eta_stage"] ** len(self.cfg.get("stage_ratios", [1.0]))
        self.i_master = float(self.cfg["I_master"])
        self.i_load_eq = (
            float(self.cfg.get("I_flywheel", 0.0)) + float(self.cfg.get("I_gen", 0.0))
        ) * self.ratio**2
        self.state = TorsionalState(
            omega_master=self.rpm_to_rad_s(float(self.cfg.get("bench_initial_rpm", 1.8))),
            omega_load_eq=self.rpm_to_rad_s(float(self.cfg.get("bench_initial_rpm", 1.8))),
            load_fraction=float(self.cfg.get("bench_initial_load_fraction", 0.0)),
        )

    @staticmethod
    def rpm_to_rad_s(rpm: float) -> float:
        return rpm * 2.0 * math.pi / 60.0

    @staticmethod
    def rad_s_to_rpm(omega: float) -> float:
        return omega * 60.0 / (2.0 * math.pi)

    def spring_torque(self) -> float:
        twist = self.state.theta_master - self.state.theta_load_eq
        backlash = abs(float(self.cfg.get("backlash_rad", 0.0)))
        if abs(twist) <= backlash:
            elastic_twist = 0.0
        else:
            elastic_twist = math.copysign(abs(twist) - backlash, twist)

        relative_speed = self.state.omega_master - self.state.omega_load_eq
        return (
            float(self.cfg.get("torsional_k_nm_rad", 0.0)) * elastic_twist
            + float(self.cfg.get("torsional_c_nms_rad", 0.0)) * relative_speed
        )

    def step(
        self,
        *,
        drive_torque_nm: float,
        electric_target_w: float,
        dt_sec: float,
        grid_available: bool = True,
    ) -> Dict[str, float]:
        dt = max(float(dt_sec), 1e-9)
        s = self.state

        omega_gen = s.omega_load_eq * self.ratio
        rpm_gen = self.rad_s_to_rpm(omega_gen)

        desired_load = 1.0 if grid_available and rpm_gen >= self.cfg["gen_cutin_rpm"] else 0.0
        ramp_per_s = max(1e-9, float(self.cfg.get("clutch_load_ramp_per_s", 0.5)))
        max_delta = ramp_per_s * dt
        s.load_fraction += clamp(desired_load - s.load_fraction, -max_delta, max_delta)
        s.load_fraction = clamp(s.load_fraction, 0.0, 1.0)

        p_e_target = max(0.0, float(electric_target_w)) * s.load_fraction if grid_available else 0.0
        p_mech_gen = p_e_target / max(float(self.cfg["eta_gen"]), 1e-9)
        tau_gen = p_mech_gen / max(abs(omega_gen), 1.0)
        tau_load_eq = tau_gen * self.ratio / max(self.eta_drive, 1e-9)

        tau_s = self.spring_torque()
        tau_friction_master = float(self.cfg.get("bench_b_master", 0.0)) * s.omega_master
        tau_friction_load = float(self.cfg.get("bench_b_load_eq", 0.0)) * s.omega_load_eq

        rpm_master = self.rad_s_to_rpm(s.omega_master)
        overspeed_trip = float(self.cfg.get("overspeed_trip_rpm", self.cfg.get("master_rpm_nominal", 1.8) * 1.15))
        brake_gain = float(self.cfg.get("overspeed_brake_nm_per_rpm", 0.0))
        tau_brake = max(0.0, rpm_master - overspeed_trip) * brake_gain

        alpha_master = (
            float(drive_torque_nm) - tau_s - tau_friction_master - tau_brake
        ) / max(self.i_master, 1e-9)
        alpha_load = (
            tau_s - tau_load_eq - tau_friction_load
        ) / max(self.i_load_eq, 1e-9)

        # Semi-implicit Euler is more stable than explicit Euler for spring systems.
        s.omega_master += alpha_master * dt
        s.omega_load_eq += alpha_load * dt
        s.theta_master += s.omega_master * dt
        s.theta_load_eq += s.omega_load_eq * dt

        omega_gen_new = s.omega_load_eq * self.ratio
        p_electric = tau_gen * abs(omega_gen_new) * float(self.cfg["eta_gen"])

        return {
            "rpm_master": self.rad_s_to_rpm(s.omega_master),
            "rpm_gen": self.rad_s_to_rpm(omega_gen_new),
            "twist_mrad": (s.theta_master - s.theta_load_eq) * 1e3,
            "spring_torque_knm": tau_s / 1e3,
            "load_fraction": s.load_fraction,
            "p_electric_kw": p_electric / 1e3,
            "tau_brake_knm": tau_brake / 1e3,
        }


def run_loss_of_grid_demo(config: Dict[str, float], duration_s: float = 30.0, dt_sec: float = 0.01) -> List[Dict[str, float]]:
    """Bench transient: nominal load, grid loss at 10 s, restoration at 20 s."""
    bench = TorsionalBench(config)
    records: List[Dict[str, float]] = []
    steps = int(duration_s / dt_sec)
    rated_electric = float(config["p_electric_rated"])
    nominal_omega = bench.rpm_to_rad_s(float(config.get("master_rpm_nominal", 1.8)))
    nominal_drive_torque = (
        rated_electric
        / max(float(config["eta_gen"]) * bench.eta_drive, 1e-9)
        / max(nominal_omega, 1e-9)
    )

    for i in range(steps):
        t = i * dt_sec
        grid_ok = not (10.0 <= t < 20.0)
        # During grid loss, a simple governor closes prime-mover admission rapidly.
        drive = nominal_drive_torque if grid_ok else 0.05 * nominal_drive_torque
        out = bench.step(
            drive_torque_nm=drive,
            electric_target_w=rated_electric,
            dt_sec=dt_sec,
            grid_available=grid_ok,
        )
        out["time_s"] = t
        out["grid_available"] = 1.0 if grid_ok else 0.0
        records.append(out)

    return records
