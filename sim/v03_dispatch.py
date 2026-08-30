"""BMSC Physics v0.3 — multi-day thermal dispatch model.

This model intentionally operates on the slow plant timescale (seconds to minutes).
Fast clutch/torsional transients live in ``torsional_bench.py`` so the solar/storage
energy model is not forced to resolve millisecond mechanical modes.

Concept-validation only. Not a plant controller or manufacturing model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional


@dataclass
class DispatchState:
    thermal_j: float
    electric_j: float = 0.0
    receiver_j: float = 0.0
    cycle_j: float = 0.0
    storage_loss_j: float = 0.0
    rejected_j: float = 0.0


@dataclass
class DispatchResult:
    hour: float
    dni_w_m2: float
    cloud_factor: float
    storage_mwh_th: float
    storage_soc: float
    thermal_cycle_kw: float
    electric_kw: float
    rejected_kw_th: float
    grid_available: bool


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def idealized_dni(hour_of_day: float, dni_max: float) -> float:
    """12 h sine-wave DNI profile, used only for repeatable baseline studies."""
    h = hour_of_day % 24.0
    if 6.0 <= h <= 18.0:
        return dni_max * math.sin(math.pi * (h - 6.0) / 12.0)
    return 0.0


class MultiDayDispatchModel:
    """Energy-conserving thermal buffer + electrical dispatch model.

    The thermal ledger is closed explicitly each step:

        E_old + E_receiver = E_new + E_cycle + E_storage_loss + E_rejected

    This makes energy-accounting regressions directly testable.
    """

    def __init__(self, config: Dict[str, float]):
        self.cfg = dict(config)
        self.capacity_j = float(self.cfg["E_th_capacity"])
        self.state = DispatchState(
            thermal_j=clamp(float(self.cfg.get("E_th_initial", 0.0)), 0.0, self.capacity_j)
        )
        self.last_balance_error_j = 0.0

    @property
    def eta_drive(self) -> float:
        ratios = self.cfg.get("stage_ratios", [1.0])
        return float(self.cfg["eta_stage"] ** len(ratios))

    @property
    def eta_receiver_to_electric(self) -> float:
        return (
            float(self.cfg["eta_thermal_cycle"])
            * self.eta_drive
            * float(self.cfg["eta_gen"])
        )

    def receiver_power(self, dni: float, cloud_factor: float = 1.0) -> float:
        effective_receiver = max(
            0.0,
            float(self.cfg["eta_rec"]) - float(self.cfg.get("receiver_loss_fraction", 0.0)),
        )
        return (
            max(0.0, dni)
            * clamp(cloud_factor, 0.0, 1.0)
            * float(self.cfg["aperture_area"])
            * float(self.cfg["eta_opt"])
            * effective_receiver
        )

    def dispatch_target_electric(self, demand_fraction: float, grid_available: bool) -> float:
        if not grid_available:
            return 0.0
        return clamp(demand_fraction, 0.0, 1.0) * float(self.cfg["p_electric_rated"])

    def step(
        self,
        *,
        dni: float,
        dt_sec: float,
        demand_fraction: float = 1.0,
        cloud_factor: float = 1.0,
        grid_available: bool = True,
        reserve_fraction: float = 0.08,
    ) -> Dict[str, float]:
        dt = max(float(dt_sec), 1e-9)
        e0 = self.state.thermal_j

        p_rec = self.receiver_power(dni, cloud_factor)
        e_rec = p_rec * dt
        self.state.receiver_j += e_rec

        # First-order storage loss, removed from stored energy before dispatch.
        loss_fraction = max(0.0, float(self.cfg.get("storage_loss_fraction_per_hour", 0.0)))
        e_loss = min(e0, e0 * loss_fraction * dt / 3600.0)
        e_after_loss = e0 - e_loss
        self.state.storage_loss_j += e_loss

        p_e_target = self.dispatch_target_electric(demand_fraction, grid_available)
        eta_chain = max(self.eta_receiver_to_electric, 1e-12)
        p_th_needed = p_e_target / eta_chain
        p_th_request = min(float(self.cfg["p_th_cycle_max"]), p_th_needed)

        # Preserve a configurable reserve unless receiver power alone can cover dispatch.
        reserve_j = clamp(reserve_fraction, 0.0, 0.95) * self.capacity_j
        receiver_step_j = e_rec
        storage_above_reserve_j = max(0.0, e_after_loss - reserve_j)
        dispatchable_j = receiver_step_j + storage_above_reserve_j
        e_cycle = min(p_th_request * dt, dispatchable_j)

        # Thermal energy remaining after cycle extraction. Receiver energy not used by
        # the cycle charges storage; overflow is explicitly counted as rejected heat.
        e_candidate = e_after_loss + e_rec - e_cycle
        e_new = min(self.capacity_j, max(0.0, e_candidate))
        e_rejected = max(0.0, e_candidate - self.capacity_j)

        self.state.thermal_j = e_new
        self.state.cycle_j += e_cycle
        self.state.rejected_j += e_rejected

        p_cycle = e_cycle / dt
        p_electric = p_cycle * eta_chain
        self.state.electric_j += p_electric * dt

        # Exact per-step thermal ledger residual, useful as a regression invariant.
        lhs = e0 + e_rec
        rhs = e_new + e_cycle + e_loss + e_rejected
        self.last_balance_error_j = lhs - rhs

        return {
            "p_rec_kw": p_rec / 1e3,
            "p_cycle_kw_th": p_cycle / 1e3,
            "p_electric_kw": p_electric / 1e3,
            "storage_mwh_th": e_new / 3.6e9,
            "storage_soc": e_new / self.capacity_j if self.capacity_j else 0.0,
            "storage_loss_kw_th": e_loss / dt / 1e3,
            "rejected_kw_th": e_rejected / dt / 1e3,
            "balance_error_j": self.last_balance_error_j,
        }


def run_multi_day(
    config: Dict[str, float],
    *,
    days: int = 3,
    dt_sec: float = 60.0,
    cloud_profile: Optional[Callable[[float], float]] = None,
    demand_profile: Optional[Callable[[float], float]] = None,
    grid_profile: Optional[Callable[[float], bool]] = None,
) -> List[DispatchResult]:
    model = MultiDayDispatchModel(config)
    records: List[DispatchResult] = []
    steps = int(days * 24.0 * 3600.0 / dt_sec)

    for i in range(steps):
        hour = i * dt_sec / 3600.0
        hday = hour % 24.0
        dni = idealized_dni(hday, float(config["dni_max"]))
        cloud = 1.0 if cloud_profile is None else clamp(float(cloud_profile(hour)), 0.0, 1.0)
        demand = 1.0 if demand_profile is None else clamp(float(demand_profile(hour)), 0.0, 1.0)
        grid_ok = True if grid_profile is None else bool(grid_profile(hour))

        out = model.step(
            dni=dni,
            dt_sec=dt_sec,
            demand_fraction=demand,
            cloud_factor=cloud,
            grid_available=grid_ok,
        )
        records.append(
            DispatchResult(
                hour=hour,
                dni_w_m2=dni,
                cloud_factor=cloud,
                storage_mwh_th=out["storage_mwh_th"],
                storage_soc=out["storage_soc"],
                thermal_cycle_kw=out["p_cycle_kw_th"],
                electric_kw=out["p_electric_kw"],
                rejected_kw_th=out["rejected_kw_th"],
                grid_available=grid_ok,
            )
        )

    return records
