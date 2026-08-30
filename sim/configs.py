"""Parameter sets for BMSC Physics v0.2.

All values are conceptual and intended for simulation only.
The gear train is treated as continuously meshed; the mechanical PLC stages
load admission rather than instantaneously changing the drivetrain ratio.
"""

BASE = {
    "dni_max": 950.0,
    "eta_opt": 0.75,
    "eta_rec": 0.88,
    "receiver_loss_fraction": 0.05,
    "eta_thermal_cycle": 0.35,
    "storage_loss_fraction_per_hour": 0.002,
    "eta_stage": 0.96,
    "eta_gen": 0.96,
    "stage_ratios": [10.0, 10.0, 10.0],
    "cam_windows": {1: (90.0, 300.0), 2: (120.0, 270.0), 3: (150.0, 240.0)},
    "engage_rpm": {1: 0.15, 2: 0.60, 3: 1.00},
    "disengage_rpm": {1: 0.08, 2: 0.45, 3: 0.80},
    "stage_load_fraction": {0: 0.0, 1: 0.10, 2: 0.40, 3: 1.0},
    "omega_min": 0.01,
    "master_rpm_nominal": 1.8,
    "governor_band_rpm": 0.10,
    "gen_cutin_rpm": 1200.0,
    "gen_nominal_rpm": 1800.0,
    "I_intermediate": [8.0, 2.0, 0.5],
    "I_gen": 25.0,
    "b_friction": 0.0,
    "max_master_accel_rpm_s": 0.03,
    "max_master_decel_rpm_s": 0.06,
}


def _scaled(**overrides):
    cfg = dict(BASE)
    cfg.update(overrides)
    return cfg


# With the baseline chain:
# eta_receiver_effective = 0.88 - 0.05 = 0.83
# eta_receiver_to_electric = 0.35 * 0.96^3 * 0.96 ~= 0.29727
# These aperture areas therefore close the NOMINAL PEAK power equation.
CONFIG_10KW_PEAK = _scaled(
    name="10 kW peak validation",
    aperture_area=56.9,
    p_th_cycle_max=33.64e3,
    E_th_capacity=269.1e3 * 3600.0,
    E_th_initial=50e3 * 3600.0,
    E_th_min_reserve=10e3 * 3600.0,
    tau_max=70e3,
    p_electric_rated=10e3,
    I_master=500.0,
    I_flywheel=5.0,
    b_friction=150.0,
    max_master_accel_rpm_s=0.03,
    max_master_decel_rpm_s=0.08,
)

CONFIG_100KW_PEAK = _scaled(
    name="100 kW peak pilot",
    aperture_area=568.9,
    p_th_cycle_max=336.4e3,
    E_th_capacity=2.691e6 * 3600.0,
    E_th_initial=0.5e6 * 3600.0,
    E_th_min_reserve=0.1e6 * 3600.0,
    tau_max=650e3,
    p_electric_rated=100e3,
    I_master=8_000.0,
    I_flywheel=35.0,
    b_friction=800.0,
    max_master_accel_rpm_s=0.02,
    max_master_decel_rpm_s=0.06,
)

CONFIG_1MW_PEAK = _scaled(
    name="1 MW peak industrial concept",
    aperture_area=5_688.3,
    p_th_cycle_max=3.36393e6,
    E_th_capacity=26.911e6 * 3600.0,
    E_th_initial=5e6 * 3600.0,
    E_th_min_reserve=1e6 * 3600.0,
    tau_max=6.5e6,
    p_electric_rated=1.0e6,
    I_master=150_000.0,
    I_flywheel=250.0,
    b_friction=5_000.0,
    max_master_accel_rpm_s=0.01,
    max_master_decel_rpm_s=0.04,
)

# Idealized APERTURE-ENERGY study under the repository's simple 06:00–18:00
# sinusoidal DNI profile. It closes ~24 MWh_e/day before storage/parasitic
# losses. It does NOT by itself implement a 24-hour dispatch schedule.
CONFIG_1MW_DAILY_ENERGY_IDEAL = _scaled(
    name="1 MW average daily-energy aperture study",
    aperture_area=17_900.0,
    p_th_cycle_max=3.36393e6,
    E_th_capacity=42e6 * 3600.0,
    E_th_initial=10e6 * 3600.0,
    E_th_min_reserve=2e6 * 3600.0,
    tau_max=6.5e6,
    p_electric_rated=1.0e6,
    I_master=150_000.0,
    I_flywheel=250.0,
    b_friction=5_000.0,
    max_master_accel_rpm_s=0.01,
    max_master_decel_rpm_s=0.04,
)

CONFIGS = {
    "10kw": CONFIG_10KW_PEAK,
    "100kw": CONFIG_100KW_PEAK,
    "1mw_peak": CONFIG_1MW_PEAK,
    "1mw_daily_energy": CONFIG_1MW_DAILY_ENERGY_IDEAL,
}
