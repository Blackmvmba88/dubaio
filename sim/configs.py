"""Parameter sets for BMSC Physics v0.2.

All values are conceptual and intended for simulation only.
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
    "omega_min": 0.01,
    "gen_cutin_rpm": 1200.0,
    "I_intermediate": [8.0, 2.0, 0.5],
    "I_gen": 25.0,
    "b_friction": 0.0,
}


def _scaled(**overrides):
    cfg = dict(BASE)
    cfg.update(overrides)
    return cfg


CONFIG_10KW_PEAK = _scaled(
    name="10 kW peak validation",
    aperture_area=45.0,
    p_th_cycle_max=31.25e3,
    E_th_capacity=250e3 * 3600.0,
    E_th_initial=50e3 * 3600.0,
    E_th_min_reserve=10e3 * 3600.0,
    tau_max=70e3,
    p_electric_rated=10e3,
    I_master=500.0,
    I_flywheel=5.0,
    b_friction=150.0,
)

CONFIG_100KW_PEAK = _scaled(
    name="100 kW peak pilot",
    aperture_area=440.0,
    p_th_cycle_max=312.5e3,
    E_th_capacity=2.5e6 * 3600.0,
    E_th_initial=0.5e6 * 3600.0,
    E_th_min_reserve=0.1e6 * 3600.0,
    tau_max=650e3,
    p_electric_rated=100e3,
    I_master=8_000.0,
    I_flywheel=35.0,
    b_friction=800.0,
)

CONFIG_1MW_PEAK = _scaled(
    name="1 MW peak industrial concept",
    aperture_area=4_386.0,
    p_th_cycle_max=3.125e6,
    E_th_capacity=25e6 * 3600.0,
    E_th_initial=5e6 * 3600.0,
    E_th_min_reserve=1e6 * 3600.0,
    tau_max=6.5e6,
    p_electric_rated=1.0e6,
    I_master=150_000.0,
    I_flywheel=250.0,
    b_friction=5_000.0,
)

# Idealized daily-energy-closing case under the repository's simple
# 06:00–18:00 sinusoidal DNI profile. This is NOT a real site design.
CONFIG_1MW_CONTINUOUS_IDEAL = _scaled(
    name="1 MW continuous idealized energy-balance case",
    aperture_area=16_600.0,
    p_th_cycle_max=3.125e6,
    E_th_capacity=40e6 * 3600.0,
    E_th_initial=10e6 * 3600.0,
    E_th_min_reserve=2e6 * 3600.0,
    tau_max=6.5e6,
    p_electric_rated=1.0e6,
    I_master=150_000.0,
    I_flywheel=250.0,
    b_friction=5_000.0,
)

CONFIGS = {
    "10kw": CONFIG_10KW_PEAK,
    "100kw": CONFIG_100KW_PEAK,
    "1mw_peak": CONFIG_1MW_PEAK,
    "1mw_continuous_ideal": CONFIG_1MW_CONTINUOUS_IDEAL,
}
