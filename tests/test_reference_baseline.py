import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "sim"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from configs import CONFIG_1MW_PEAK
from reference_baseline import bmsc_metrics, conventional_metrics, compare_architectures


class TestReferenceBaseline(unittest.TestCase):
    def test_bmsc_reconciles_existing_peak_aperture(self):
        metrics = bmsc_metrics(CONFIG_1MW_PEAK)
        self.assertAlmostEqual(metrics.aperture_for_1mw_peak_m2, 5688.3, delta=2.0)

    def test_reference_path_is_not_assumed_worse_than_bmsc(self):
        bmsc = bmsc_metrics(CONFIG_1MW_PEAK)
        reference = conventional_metrics(CONFIG_1MW_PEAK)
        self.assertGreater(reference.drivetrain_path_efficiency, bmsc.drivetrain_path_efficiency)

    def test_comparison_reports_positive_aperture_penalty_for_current_bmsc_assumptions(self):
        result = compare_architectures(CONFIG_1MW_PEAK)
        self.assertGreater(result["aperture_penalty_percent"], 0.0)


if __name__ == "__main__":
    unittest.main()
