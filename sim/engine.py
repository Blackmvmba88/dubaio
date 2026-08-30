"""BMSC Physics v0.2 simulation core.

The model is intentionally conservative about what it claims:
- solar input creates available power;
- storage integrates energy;
- shaft torque is derived from available shaft power;
- rotational speed evolves from I*domega/dt = sum(torque);
- cams request stages, while physical gates authorize engagement.

It is a concept-validation model, not a component design tool.
"""

from __future__ import annotations

import math
from typing import Dict, Any

import numpy as np


class BMSCPhysicsEngine:
    def __init__(self, config: Dict[str, Any]):
        self.cfg = dict(config)
        self.E_thermal = float(self.cfg.get("E_th_initial", 0.0))
        self.omega_master = float(self.cfg.get("omega_initial", 0.001))
        self.current_stage = 0

    @staticmethod
    def rpm_to_rad_s(rpm: float) -> float:
        return rpm * 2.0 * math.pi / 60.0

    @staticmethod
    def rad_s_to_rpm(omega: float) -> float:
        return omega * 60.0 / (2.0 * math.pi)

    def cam_angle(self, hour_of_day: float) -> float:
        """One mechanical clock revolution per 24-hour conceptual cycle."""
        return (hour_of_day % 24.0) * 15.0

    def requested_stage(self, hour_of_day: float) -> int:
        angle = self.cam_angle(hour_of_day)
        requested = 0
        for stage, (on_deg, off_deg) in self.cfg["cam_windows"].items():
            if on_deg <= angle <= off_deg:
                requested = max(requested, int(stage))
        return requested

    def stage_ratio(self, stage: int) -> float:
        if stage <= 0:
            return 1.0
        return float(np.prod(self.cfg["stage_ratios"][:stage]))

    def drivetrain_efficiency(self, stage: int) -> float:
        if stage <= 0:
            return 1.0
        return float(self.cfg["eta_stage"] ** stage)

    def reflected_inertia(self, stage: int) -> float:
        """Reflect rotating downstream inertia to the master shaft.

        For a speed multiplier R = omega_out / omega_in, downstream inertia
        reflected to the input is I_out * R^2.
        """
        inertia = float(self.cfg["I_master"])
        if stage <= 0:
            return inertia

        cumulative = 1.0
        intermediate = self.cfg.get("I_intermediate", [])
        for index in range(stage):
            cumulative *= self.cfg["stage_ratios"][index]
            if index < len(intermediate):
                inertia += float(intermediate[index]) * cumulative**2

        final_ratio = self.stage_ratio(stage)
        inertia += (
            float(self.cfg["I_flywheel"]) + float(self.cfg["I_gen"])
        ) * final_ratio**2
        return inertia

    def _update_stage(self, requested: int, has_energy: bool) -> None:
        rpm_master = self.rad_s_to_rpm(self.omega_master)

        if self.current_stage == 0:
            if requested >= 1 and has_energy:
                engage = self.cfg["engage_rpm"].get(1, 0.0)
                if rpm_master >= engage:
                    self.current_stage = 1
            return

        # Progressive upshift: one stage per simulation step.
        if requested > self.current_stage and has_energy:
            next_stage = self.current_stage + 1
            engage = self.cfg["engage_rpm"].get(next_stage, math.inf)
            if rpm_master >= engage:
                self.current_stage = next_stage
            return

        # Progressive downshift with true speed hysteresis.
        if requested < self.current_stage or not has_energy:
            disengage = self.cfg["disengage_rpm"].get(self.current_stage, 0.0)
            if rpm_master <= disengage or not has_energy:
                self.current_stage = max(0, self.current_stage - 1)

    def step(self, dni: float, dt_sec: float, hour_of_day: float) -> Dict[str, float]:
        dt_sec = float(dt_sec)
        dni = max(0.0, float(dni))

        # 1) Solar -> receiver power.
        p_opt = dni * self.cfg["aperture_area"] * self.cfg["eta_opt"]
        p_rec = max(
            0.0,
            p_opt
            * (
                self.cfg["eta_rec"]
                - self.cfg.get("receiver_loss_fraction", 0.0)
            ),
        )

        # 2) Mechanical clock requests a stage; physical state may veto it.
        requested = self.requested_stage(hour_of_day)

        # First-order thermal-storage loss model.
        storage_loss_fraction_per_hour = self.cfg.get(
            "storage_loss_fraction_per_hour", 0.0
        )
        q_store_loss = (
            self.E_thermal * storage_loss_fraction_per_hour / 3600.0
        )

        # The prime mover can receive thermal power while the downstream train
        # is still disengaged, allowing the master shaft to spin up.
        wants_motion = requested > 0
        p_th_request = self.cfg["p_th_cycle_max"] if wants_motion else 0.0

        # Power available during this integration interval = current receiver
        # power plus energy that can be withdrawn from storage during dt.
        p_th_available = min(
            p_th_request,
            p_rec + max(0.0, self.E_thermal) / max(dt_sec, 1e-9),
        )

        dE = (p_rec - p_th_available - q_store_loss) * dt_sec
        self.E_thermal = float(
            np.clip(
                self.E_thermal + dE,
                0.0,
                self.cfg["E_th_capacity"],
            )
        )

        p_shaft_available = p_th_available * self.cfg["eta_thermal_cycle"]
        has_energy = (
            self.E_thermal >= self.cfg["E_th_min_reserve"]
            or p_rec >= 0.30 * self.cfg["p_th_cycle_max"]
        )

        self._update_stage(requested=requested, has_energy=has_energy)

        # 3) Drive torque is derived from available shaft power.
        if p_shaft_available > 0.0 and wants_motion:
            tau_drive = min(
                self.cfg["tau_max"],
                p_shaft_available
                / max(self.omega_master, self.cfg.get("omega_min", 0.01)),
            )
        else:
            tau_drive = 0.0

        # Actual mechanical power injected at the current shaft speed.
        p_drive_actual = tau_drive * self.omega_master

        # 4) Drivetrain + generator load.
        stage = self.current_stage
        ratio = self.stage_ratio(stage)
        eta_drive = self.drivetrain_efficiency(stage)
        i_eq = self.reflected_inertia(stage)

        if stage > 0:
            omega_gen = self.omega_master * ratio
            rpm_gen = self.rad_s_to_rpm(omega_gen)
        else:
            omega_gen = 0.0
            rpm_gen = 0.0

        p_electric = 0.0
        tau_gen = 0.0
        tau_load_eq = 0.0

        if stage > 0 and rpm_gen >= self.cfg["gen_cutin_rpm"]:
            # Generator load cannot demand more mechanical power than the
            # drivetrain can receive from the prime mover in this simple model.
            p_mech_gen_cap = p_shaft_available * eta_drive
            p_electric = min(
                self.cfg["p_electric_rated"],
                p_mech_gen_cap * self.cfg["eta_gen"],
            )
            p_mech_at_gen = p_electric / max(self.cfg["eta_gen"], 1e-9)
            tau_gen = p_mech_at_gen / max(omega_gen, 1e-9)
            tau_load_eq = tau_gen * ratio / max(eta_drive, 1e-9)

        tau_friction = self.cfg["b_friction"] * self.omega_master

        # 5) I*domega/dt = sum(torque), integrated with explicit Euler.
        domega_dt = (tau_drive - tau_load_eq - tau_friction) / max(i_eq, 1e-9)
        self.omega_master = max(
            0.0,
            self.omega_master + domega_dt * dt_sec,
        )

        return {
            "hour": float(hour_of_day),
            "dni_w_m2": dni,
            "cam_angle_deg": self.cam_angle(hour_of_day),
            "requested_stage": float(requested),
            "stage": float(self.current_stage),
            "p_opt_kw": p_opt / 1e3,
            "p_rec_kw": p_rec / 1e3,
            "p_th_cycle_kw": p_th_available / 1e3,
            "p_shaft_available_kw": p_shaft_available / 1e3,
            "p_drive_actual_kw": p_drive_actual / 1e3,
            "E_th_mwh": self.E_thermal / 3.6e9,
            "rpm_master": self.rad_s_to_rpm(self.omega_master),
            "rpm_gen": rpm_gen,
            "tau_drive_knm": tau_drive / 1e3,
            "tau_load_eq_knm": tau_load_eq / 1e3,
            "p_electric_kw": p_electric / 1e3,
            "I_eq_kgm2": i_eq,
        }


def idealized_dni(hour: float, dni_max: float) -> float:
    """Simple 12-hour sine profile used only for baseline comparisons."""
    if 6.0 <= hour <= 18.0:
        return float(dni_max * math.sin(math.pi * (hour - 6.0) / 12.0))
    return 0.0


def run_day_simulation(config: Dict[str, Any], dt_sec: float = 10.0):
    engine = BMSCPhysicsEngine(config)
    steps = int(24.0 * 3600.0 / dt_sec)
    records = []

    for i in range(steps + 1):
        hour = i * dt_sec / 3600.0
        dni = idealized_dni(hour, config["dni_max"])
        records.append(engine.step(dni=dni, dt_sec=dt_sec, hour_of_day=hour))

    return records
