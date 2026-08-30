"""BMSC Physics v0.2 simulation core.

Model rules:
- solar input creates available power;
- storage integrates energy;
- torque is derived from available shaft power;
- rotational speed evolves from I*domega/dt = sum(torque);
- the full gear train remains kinematically meshed;
- mechanical PLC stages admit LOAD rather than instantaneously creating new
  gear ratios and reflected inertias;
- a simple governor/rate envelope prevents the day-scale solver from treating
  sub-second drivetrain transients as instantaneous.

This is a concept-validation model, not a component design tool.
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
        return (hour_of_day % 24.0) * 15.0

    def requested_stage(self, hour_of_day: float) -> int:
        angle = self.cam_angle(hour_of_day)
        requested = 0
        for stage, (on_deg, off_deg) in self.cfg["cam_windows"].items():
            if on_deg <= angle <= off_deg:
                requested = max(requested, int(stage))
        return requested

    def stage_ratio(self, stage: int) -> float:
        """Cumulative ratio through the first `stage` physical gear stages."""
        if stage <= 0:
            return 1.0
        return float(np.prod(self.cfg["stage_ratios"][:stage]))

    def full_ratio(self) -> float:
        return self.stage_ratio(len(self.cfg["stage_ratios"]))

    def drivetrain_efficiency(self, stage: int) -> float:
        if stage <= 0:
            return 1.0
        return float(self.cfg["eta_stage"] ** stage)

    def full_drivetrain_efficiency(self) -> float:
        return self.drivetrain_efficiency(len(self.cfg["stage_ratios"]))

    def reflected_inertia_full_train(self) -> float:
        """Reflect the continuously meshed drivetrain to the master shaft."""
        inertia = float(self.cfg["I_master"])
        cumulative = 1.0
        intermediate = self.cfg.get("I_intermediate", [])

        for index, ratio in enumerate(self.cfg["stage_ratios"]):
            cumulative *= ratio
            if index < len(intermediate):
                inertia += float(intermediate[index]) * cumulative**2

        inertia += (
            float(self.cfg["I_flywheel"]) + float(self.cfg["I_gen"])
        ) * cumulative**2
        return inertia

    def _update_stage(self, requested: int, has_energy: bool) -> None:
        """Update load-admission stage with speed-gated upshift and safe unload."""
        rpm_master = self.rad_s_to_rpm(self.omega_master)

        # When the cam withdraws a request, unload progressively. Do not force
        # the rotating train to remain electrically loaded until it slows.
        if requested < self.current_stage:
            self.current_stage = max(requested, self.current_stage - 1)
            return

        if not has_energy:
            if self.current_stage > 0:
                disengage = self.cfg["disengage_rpm"].get(self.current_stage, 0.0)
                if rpm_master <= disengage:
                    self.current_stage -= 1
            return

        if requested > self.current_stage:
            next_stage = self.current_stage + 1
            engage = self.cfg["engage_rpm"].get(next_stage, math.inf)
            if rpm_master >= engage:
                self.current_stage = next_stage

    def _governor_factor(self, rpm_master: float) -> float:
        nominal = self.cfg["master_rpm_nominal"]
        band = max(self.cfg.get("governor_band_rpm", 0.1), 1e-9)
        if rpm_master <= nominal:
            return 1.0
        return float(np.clip(1.0 - (rpm_master - nominal) / band, 0.0, 1.0))

    def step(self, dni: float, dt_sec: float, hour_of_day: float) -> Dict[str, float]:
        dt_sec = float(dt_sec)
        dni = max(0.0, float(dni))
        omega_old = self.omega_master
        rpm_master_old = self.rad_s_to_rpm(omega_old)

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

        # 2) Passive storage loss for this interval.
        storage_loss_fraction_per_hour = self.cfg.get(
            "storage_loss_fraction_per_hour", 0.0
        )
        q_store_loss = (
            self.E_thermal * storage_loss_fraction_per_hour / 3600.0
        )
        E_after_passive_loss = max(0.0, self.E_thermal - q_store_loss * dt_sec)

        # 3) Cam requests a load stage; physics authorizes it.
        requested = self.requested_stage(hour_of_day)
        thermal_energy_available = E_after_passive_loss + p_rec * dt_sec
        has_energy = (
            thermal_energy_available >= self.cfg["E_th_min_reserve"]
            or p_rec >= 0.30 * self.cfg["p_th_cycle_max"]
        )
        self._update_stage(requested=requested, has_energy=has_energy)

        # 4) Thermal -> shaft power envelope. The prime mover is driven only
        # while the cam requests motion. Excess receiver power remains in the
        # thermal buffer (subject to capacity clipping below).
        wants_drive = requested > 0
        if wants_drive:
            p_th_cap = min(
                self.cfg["p_th_cycle_max"],
                thermal_energy_available / max(dt_sec, 1e-9),
            )
        else:
            p_th_cap = 0.0

        p_shaft_cap = p_th_cap * self.cfg["eta_thermal_cycle"]

        if p_shaft_cap > 0.0:
            tau_drive = min(
                self.cfg["tau_max"],
                p_shaft_cap / max(omega_old, self.cfg.get("omega_min", 0.01)),
            )
            tau_drive *= self._governor_factor(rpm_master_old)
        else:
            tau_drive = 0.0

        # 5) Full drivetrain remains meshed. PLC stages only load admission.
        ratio = self.full_ratio()
        eta_drive = self.full_drivetrain_efficiency()
        i_eq = self.reflected_inertia_full_train()

        omega_gen_old = omega_old * ratio
        rpm_gen_old = self.rad_s_to_rpm(omega_gen_old)

        load_fraction = self.cfg.get("stage_load_fraction", {}).get(
            self.current_stage, 0.0
        )
        cutin = self.cfg["gen_cutin_rpm"]
        nominal_gen = self.cfg["gen_nominal_rpm"]
        speed_fraction = float(
            np.clip(
                (rpm_gen_old - cutin) / max(nominal_gen - cutin, 1e-9),
                0.0,
                1.0,
            )
        )

        p_electric_demand = (
            self.cfg["p_electric_rated"] * load_fraction * speed_fraction
        )

        if p_electric_demand > 0.0 and omega_gen_old > 0.0:
            p_mech_gen = p_electric_demand / max(self.cfg["eta_gen"], 1e-9)
            tau_gen = p_mech_gen / omega_gen_old
            tau_load_eq = tau_gen * ratio / max(eta_drive, 1e-9)
        else:
            tau_gen = 0.0
            tau_load_eq = 0.0

        tau_friction = self.cfg["b_friction"] * omega_old

        # 6) Rotational dynamics.
        domega_dt_raw = (
            tau_drive - tau_load_eq - tau_friction
        ) / max(i_eq, 1e-9)

        max_accel = self.rpm_to_rad_s(
            self.cfg.get("max_master_accel_rpm_s", math.inf)
        )
        max_decel = self.rpm_to_rad_s(
            self.cfg.get("max_master_decel_rpm_s", math.inf)
        )
        domega_dt = float(np.clip(domega_dt_raw, -max_decel, max_accel))

        omega_new = max(0.0, omega_old + domega_dt * dt_sec)
        omega_avg = 0.5 * (omega_old + omega_new)
        omega_gen_avg = omega_avg * ratio

        # Mechanical power actually admitted by the governor during this step.
        p_drive_actual = min(p_shaft_cap, tau_drive * max(omega_avg, 0.0))
        thermal_used = (
            p_drive_actual / max(self.cfg["eta_thermal_cycle"], 1e-9)
        )

        # Electrical power follows actual average generator speed and cannot
        # exceed the requested load for this state.
        p_electric_actual = min(
            p_electric_demand,
            tau_gen * max(omega_gen_avg, 0.0) * self.cfg["eta_gen"],
        )

        # 7) Close thermal energy balance after actual prime-mover admission.
        E_new = E_after_passive_loss + p_rec * dt_sec - thermal_used * dt_sec
        self.E_thermal = float(
            np.clip(E_new, 0.0, self.cfg["E_th_capacity"])
        )
        self.omega_master = omega_new

        rpm_master = self.rad_s_to_rpm(omega_new)
        rpm_gen = self.rad_s_to_rpm(omega_new * ratio)
        E_rot = 0.5 * i_eq * omega_new**2

        return {
            "hour": float(hour_of_day),
            "dni_w_m2": dni,
            "cam_angle_deg": self.cam_angle(hour_of_day),
            "requested_stage": float(requested),
            "stage": float(self.current_stage),
            "load_fraction": float(load_fraction),
            "p_opt_kw": p_opt / 1e3,
            "p_rec_kw": p_rec / 1e3,
            "p_th_cycle_kw": thermal_used / 1e3,
            "p_shaft_available_kw": p_shaft_cap / 1e3,
            "p_drive_actual_kw": p_drive_actual / 1e3,
            "E_th_mwh": self.E_thermal / 3.6e9,
            "E_rot_kwh": E_rot / 3.6e6,
            "rpm_master": rpm_master,
            "rpm_gen": rpm_gen,
            "tau_drive_knm": tau_drive / 1e3,
            "tau_load_eq_knm": tau_load_eq / 1e3,
            "p_electric_kw": p_electric_actual / 1e3,
            "I_eq_kgm2": i_eq,
            "domega_dt_raw": domega_dt_raw,
            "domega_dt_used": domega_dt,
        }


def idealized_dni(hour: float, dni_max: float) -> float:
    """Simple 12-hour sine profile used only for baseline comparisons."""
    if 6.0 <= hour <= 18.0:
        return float(dni_max * math.sin(math.pi * (hour - 6.0) / 12.0))
    return 0.0


def run_day_simulation(config: Dict[str, Any], dt_sec: float = 1.0):
    engine = BMSCPhysicsEngine(config)
    steps = int(24.0 * 3600.0 / dt_sec)
    records = []

    for i in range(steps):
        hour = i * dt_sec / 3600.0
        dni = idealized_dni(hour, config["dni_max"])
        records.append(engine.step(dni=dni, dt_sec=dt_sec, hour_of_day=hour))

    return records
