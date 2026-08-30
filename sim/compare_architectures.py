"""Print the current analytical BMSC vs conventional reference comparison."""

from __future__ import annotations

import argparse

from configs import CONFIGS
from reference_baseline import compare_architectures


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare BMSC against a conventional reference path")
    parser.add_argument("--config", choices=sorted(CONFIGS), default="1mw_peak")
    args = parser.parse_args()

    result = compare_architectures(CONFIGS[args.config])
    bmsc = result["bmsc"]
    ref = result["reference"]

    print("BMSC architecture comparison")
    print("-" * 68)
    print(f"case                           : {args.config}")
    print(f"BMSC shaft->grid efficiency    : {100*bmsc.drivetrain_path_efficiency:8.3f} %")
    print(f"REF shaft->grid efficiency     : {100*ref.drivetrain_path_efficiency:8.3f} %")
    print(f"BMSC DNI->grid efficiency      : {100*bmsc.eta_receiver_to_grid:8.3f} %")
    print(f"REF DNI->grid efficiency       : {100*ref.eta_receiver_to_grid:8.3f} %")
    print(f"BMSC aperture @ 1 MW peak      : {bmsc.aperture_for_1mw_peak_m2:8.1f} m^2")
    print(f"REF aperture @ 1 MW peak       : {ref.aperture_for_1mw_peak_m2:8.1f} m^2")
    print(f"BMSC aperture penalty          : {result['aperture_penalty_percent']:8.3f} %")
    print(f"path-efficiency delta          : {result['path_efficiency_delta_points']:8.3f} points")


if __name__ == "__main__":
    main()
