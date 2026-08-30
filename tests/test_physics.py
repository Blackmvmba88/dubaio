import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from configs import CONFIG_1MW_PEAK, CONFIG_1MW_CONTINUOUS_IDEAL
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

    def test_peak_aperture_is_not_24h_energy_aperture(self):
        cfg = CONFIG_1MW_PEAK
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

        # 1 MW electric for 24 h at 32% receiver-thermal-to-electric
        # would require approximately 75 MWh_th/day.
        self.assertLess(receiver_kwh_day, 75_000.0)

    def test_ideal_continuous_aperture_closes_simplified_thermal_budget(self):
        cfg = CONFIG_1MW_CONTINUOUS_IDEAL
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

        self.assertGreater(receiver_kwh_day, 74_000.0)
        self.assertLess(receiver_kwh_day, 76_500.0)

    def test_electrical_power_never_exceeds_available_conversion_chain(self):
        cfg = dict(CONFIG_1MW_PEAK)
        cfg["E_th_initial"] = 5e6 * 3600.0
        engine = BMSCPhysicsEngine(cfg)

        # Give the master shaft a valid operating speed so stage gating can
        # be exercised without modeling a long start-up transient here.
        engine.omega_master = engine.rpm_to_rad_s(1.8)

        out = engine.step(dni=950.0, dt_sec=1.0, hour_of_day=12.0)
        stage = int(out["stage"])
        eta_chain = engine.drivetrain_efficiency(stage) * cfg["eta_gen"]
        upper_bound_kw = out["p_shaft_available_kw"] * eta_chain + 1e-9
        self.assertLessEqual(out["p_electric_kw"], upper_bound_kw)


if __name__ == "__main__":
    unittest.main()
