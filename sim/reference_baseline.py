"""Reference architecture for BMSC comparison studies.

The baseline is intentionally simple: the same optical receiver and thermal cycle
feed a variable-speed generator path with a high-efficiency mechanical coupling
and power electronics. It is not a vendor model; it exists to keep BMSC honest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ArchitectureMetrics:
    name: str
    eta_receiver_to_grid: float
    aperture_for_1mw_peak_m2: float
    drivetrain_path_efficiency: float
    notes: str


def effective_receiver_factor(config: Dict[str, float]) -> float:
    return max(
        0.0,
        float(config["eta_rec"]) - float(config.get("receiver_loss_fraction", 0.0)),
    )


def bmsc_metrics(config: Dict[str, float]) -> ArchitectureMetrics:
    eta_drive = float(config["eta_stage"]) ** len(config.get("stage_ratios", [1.0]))
    eta_gen = float(config["eta_gen"])
    eta_path = eta_drive * eta_gen
    eta_total = (
        float(config["eta_opt"])
        * effective_receiver_factor(config)
        * float(config["eta_thermal_cycle"])
        * eta_path
    )
    area = 1.0e6 / (float(config["dni_max"]) * eta_total)
    return ArchitectureMetrics(
        name="BMSC fixed-ratio mechanical clock",
        eta_receiver_to_grid=eta_total,
        aperture_for_1mw_peak_m2=area,
        drivetrain_path_efficiency=eta_path,
        notes="Three conceptual mechanical stages plus generator; passive/mechanical sequencing is the research differentiator.",
    )


def conventional_metrics(
    config: Dict[str, float],
    *,
    eta_mechanical_coupling: float = 0.98,
    eta_generator: float = 0.97,
    eta_power_electronics: float = 0.97,
) -> ArchitectureMetrics:
    eta_path = eta_mechanical_coupling * eta_generator * eta_power_electronics
    eta_total = (
        float(config["eta_opt"])
        * effective_receiver_factor(config)
        * float(config["eta_thermal_cycle"])
        * eta_path
    )
    area = 1.0e6 / (float(config["dni_max"]) * eta_total)
    return ArchitectureMetrics(
        name="Reference variable-speed generator + power electronics",
        eta_receiver_to_grid=eta_total,
        aperture_for_1mw_peak_m2=area,
        drivetrain_path_efficiency=eta_path,
        notes="Idealized reference only; adds active electronics but avoids the assumed three-stage mechanical efficiency penalty.",
    )


def compare_architectures(config: Dict[str, float]):
    bmsc = bmsc_metrics(config)
    ref = conventional_metrics(config)
    return {
        "bmsc": bmsc,
        "reference": ref,
        "aperture_penalty_percent": 100.0
        * (bmsc.aperture_for_1mw_peak_m2 / ref.aperture_for_1mw_peak_m2 - 1.0),
        "path_efficiency_delta_points": 100.0
        * (bmsc.drivetrain_path_efficiency - ref.drivetrain_path_efficiency),
    }
