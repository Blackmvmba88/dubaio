import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from configs import CONFIG_10KW_PEAK, CONFIG_1MW_DAILY_ENERGY_IDEAL
from v03_dispatch import MultiDayDispatchModel, idealized_dni, run_multi_day
from torsional_bench import TorsionalBench, run_loss_of_grid_demo
from v03_configs import with_v03_dynamics


class TestV03Dispatch(unittest.TestCase):
    def test_dni_boundaries_are_exact_zero(self):
        self.assertEqual(idealized_dni(6.0, 950.0), 0.0)
        self.assertEqual(idealized_dni(18.0, 950.0), 0.0)

    def test_thermal_ledger_closes_each_step(self):
        cfg = dict(CONFIG_10KW_PEAK)
        model = MultiDayDispatchModel(cfg)
        for hour in (0.0, 6.0, 9.0, 12.0, 15.0, 18.0, 23.0):
            dni = idealized_dni(hour, cfg["dni_max"])
            out = model.step(dni=dni, dt_sec=60.0, demand_fraction=0.7)
            self.assertAlmostEqual(out["balance_error_j"], 0.0, delta=1e-4)

    def test_grid_loss_commands_zero_electrical_dispatch(self):
        cfg = dict(CONFIG_10KW_PEAK)
        model = MultiDayDispatchModel(cfg)
        out = model.step(dni=950.0, dt_sec=60.0, grid_available=False)
        self.assertEqual(out["p_electric_kw"], 0.0)

    def test_electric_power_never_exceeds_rated(self):
        cfg = dict(CONFIG_1MW_DAILY_ENERGY_IDEAL)
        records = run_multi_day(cfg, days=1, dt_sec=300.0)
        peak = max(row.electric_kw for row in records)
        self.assertLessEqual(peak, cfg["p_electric_rated"] / 1000.0 + 1e-9)

    def test_daily_energy_field_harvests_more_than_peak_field_scale(self):
        cfg = dict(CONFIG_1MW_DAILY_ENERGY_IDEAL)
        # The daily-energy aperture should be substantially larger than the
        # nominal peak aperture by construction.
        self.assertGreater(cfg["aperture_area"], 3.0 * 5_688.3)

    def test_multi_day_step_count_matches_requested_duration(self):
        records = run_multi_day(dict(CONFIG_10KW_PEAK), days=1, dt_sec=3600.0)
        self.assertEqual(len(records), 24)
        self.assertEqual(records[0].hour, 0.0)
        self.assertEqual(records[-1].hour, 23.0)


class TestV03TorsionalBench(unittest.TestCase):
    def test_generator_speed_matches_fixed_ratio_at_initial_state(self):
        cfg = with_v03_dynamics("10kw")
        bench = TorsionalBench(cfg)
        ratio = math.prod(cfg["stage_ratios"])
        rpm_load_eq = bench.rad_s_to_rpm(bench.state.omega_load_eq)
        self.assertAlmostEqual(rpm_load_eq * ratio, cfg["bench_initial_rpm"] * ratio, places=6)

    def test_grid_loss_ramps_load_down(self):
        cfg = with_v03_dynamics("10kw")
        cfg["clutch_load_ramp_per_s"] = 1.0
        bench = TorsionalBench(cfg)
        before = bench.state.load_fraction
        bench.step(
            drive_torque_nm=0.0,
            electric_target_w=cfg["p_electric_rated"],
            dt_sec=0.1,
            grid_available=False,
        )
        self.assertLess(bench.state.load_fraction, before)

    def test_backlash_deadband_has_no_elastic_torque_at_rest(self):
        cfg = with_v03_dynamics("10kw")
        bench = TorsionalBench(cfg)
        bench.state.omega_master = 0.0
        bench.state.omega_load_eq = 0.0
        bench.state.theta_master = 0.5 * cfg["backlash_rad"]
        bench.state.theta_load_eq = 0.0
        self.assertAlmostEqual(bench.spring_torque(), 0.0, places=9)

    def test_loss_of_grid_demo_does_not_integrate_past_duration(self):
        cfg = with_v03_dynamics("10kw")
        records = run_loss_of_grid_demo(cfg, duration_s=1.0, dt_sec=0.1)
        self.assertEqual(len(records), 10)
        self.assertAlmostEqual(records[-1]["time_s"], 0.9, places=9)


if __name__ == "__main__":
    unittest.main()
