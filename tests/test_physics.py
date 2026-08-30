import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from configs import CONFIG_1MW_PEAK, CONFIG_1MW_DAILY_ENERGY_IDEAL
from engine import BMSCPhysicsEngine, idealized_dni


class TestBMSCPhysics(unittest.TestCase):
    def test_dni_profile(self):
        self.assertEqual(idealized_dni(0.0, 950.0), 0.0)
        self.assertEqual(idealized_dni(6.0, 950.0), 0.0)
        self.assertAlmostEqual(idealized_dni(12.0, 950.0), 950.0, places=6)
        self.assertEqual(idealized_dni(18.0, 950.0), 0.0)

    def test_drivetrain_ratio(self):
        engine = BMSCPhysicsEngine(CONFIG_1MW_PEAK)
        self.assertEqual(engine.stage_ratio(1), 10.0)
        self.assertEqual(engine.stage_ratio(2), 100.0)
        self.assertEqual(engine.stage_ratio(3), 1000.0)

    def test_efficiency_is_below_unity(self):
        engine = BMSCPhysicsEngine(CONFIG_1MW_PEAK)
        self.assertAlmostEqual(engine.drivetrain_efficiency(3), 0.96**3)
        self.assertLess(engine.drivetrain_efficiency(3), 1.0)

    @staticmethod
    def ideal_daily_electric_kwh(cfg):
        equivalent_full_sun_hours = 24.0 / math.pi
        effective_receiver = cfg["eta_rec"] - cfg["receiver_loss_fraction"]
        receiver_kwh_day = (
            cfg["dni_max"]
            * cfg["aperture_area"]
            * cfg["eta_opt"]
            * effective_receiver
            * equivalent_full_sun_hours
            / 1000.0
        )
        downstream_eta = (
            cfg["eta_thermal_cycle"]
            * (cfg["eta_stage"] ** 3)
            * cfg["eta_gen"]
        )
        return receiver_kwh_day * downstream_eta

    def test_peak_aperture_is_not_24h_energy_aperture(self):
        ideal_kwh = self.ideal_daily_electric_kwh(CONFIG_1MW_PEAK)
        self.assertGreater(ideal_kwh, 7_000.0)
        self.assertLess(ideal_kwh, 8_500.0)
        self.assertLess(ideal_kwh, 24_000.0)

    def test_daily_energy_aperture_closes_24mwh_ideal_budget(self):
        ideal_kwh = self.ideal_daily_electric_kwh(CONFIG_1MW_DAILY_ENERGY_IDEAL)
        self.assertGreater(ideal_kwh, 23_500.0)
        self.assertLess(ideal_kwh, 24_500.0)

    def test_nominal_peak_chain_is_close_to_one_megawatt(self):
        cfg = CONFIG_1MW_PEAK
        p_opt = cfg["dni_max"] * cfg["aperture_area"] * cfg["eta_opt"]
        p_rec = p_opt * (cfg["eta_rec"] - cfg["receiver_loss_fraction"])
        p_e = (
            p_rec
            * cfg["eta_thermal_cycle"]
            * (cfg["eta_stage"] ** 3)
            * cfg["eta_gen"]
        )
        self.assertGreater(p_e, 995_000.0)
        self.assertLess(p_e, 1_005_000.0)

    def test_electrical_power_never_exceeds_available_conversion_chain(self):
        cfg = dict(CONFIG_1MW_PEAK)
        cfg["E_th_initial"] = 5e6 * 3600.0
        engine = BMSCPhysicsEngine(cfg)
        engine.omega_master = engine.rpm_to_rad_s(1.8)

        # Three steps allow the conceptual sequential stage gate to advance
        # from 0 -> 1 -> 2 -> 3 while retaining the same physical state.
        out = None
        for _ in range(3):
            out = engine.step(dni=950.0, dt_sec=0.01, hour_of_day=12.0)

        self.assertIsNotNone(out)
        stage = int(out["stage"])
        eta_chain = engine.drivetrain_efficiency(stage) * cfg["eta_gen"]
        upper_bound_kw = out["p_shaft_available_kw"] * eta_chain + 1e-9
        self.assertLessEqual(out["p_electric_kw"], upper_bound_kw)


if __name__ == "__main__":
    unittest.main()
