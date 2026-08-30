# BlackMamba Solar Clock (BMSC)

> Mechanical solar-thermal engine, fixed-ratio drivetrain, mechanically sequenced load control, and energy-conserving simulation research.

The **BlackMamba Solar Clock** is an engineering research concept that explores a solar-thermal plant whose low-speed/high-torque prime motion is coupled to a continuously meshed speed-increasing drivetrain and a mechanically sequenced control layer.

## Current status

**Phase:** `BMSC Physics v0.3` — analytical validation / split-timescale simulation.

The project is deliberately proving energy accounting and dynamic behavior before treating any receiver, pressure system, clutch, shaft, gear or flywheel as build-ready.

## Core principle

> **The clock encodes sequence; physics authorizes transition; the ledger proves whether the energy existed.**

## Architecture

```text
                        SLOW PHYSICS
DNI(t) -> optics -> receiver -> thermal buffer -> cycle -> shaft power
                              |                         |
                              +------ energy ledger ----+
                                                        |
                                                        v
                        FAST PHYSICS              MASTER SHAFT
                                                  low RPM / high torque
                                                        |
                                                        v
                                              fixed drivetrain 1000:1
                                                        |
                                             compliant torsional path
                                                        |
                                               staged LOAD admission
                                                        |
                                                        v
                                                    generator
                                                        |
                                                        v
                                                      grid
```

## What v0.2 established

- Solar/thermal **power is computed first**; torque and RPM are not independently scaled with irradiance.
- Master-shaft motion follows rotational dynamics rather than a direct solar-to-RPM mapping.
- Peak-power aperture sizing is separated from daily-energy sizing.
- A continuously meshed drivetrain replaces the unphysical idea of instantaneously inserting huge reflected inertias as gear stages appear.
- Mechanical stages are interpreted as **load-admission states**, not magical RPM creation.

## Reconciled 1 MW baseline

With the current toy assumptions (`DNI=950 W/m²`, optical efficiency `0.75`, effective receiver factor `0.83`, thermal cycle `0.35`, drivetrain `0.96³`, generator `0.96`):

- **~5,688 m² aperture** closes the analytical **1 MW peak** equation.
- Under the repeatable 06:00–18:00 sinusoidal DNI profile, that aperture represents about **7.64 MWh_e/day** before storage/parasitic corrections.
- **~17,900 m² aperture** closes an idealized **24 MWh_e/day** incoming-energy budget before storage losses, weather, soiling, parasitics and reserve margin.

The daily-energy case is therefore a **budget study**, not a claim of proven 1 MW 24/7 dispatch.

## What v0.3 adds

### Slow clock — energy / storage / dispatch

`sim/v03_dispatch.py` closes the thermal ledger every step:

```text
E_old + E_receiver
    = E_new + E_cycle + E_storage_loss + E_rejected
```

It supports:

- multi-day simulations;
- storage state-of-charge tracking;
- thermal overflow/rejection;
- cloud attenuation;
- grid availability;
- flat or variable electrical demand;
- direct numerical balance-error reporting.

### Fast clock — shaft / torsion / load loss

`sim/torsional_bench.py` models:

- master inertia;
- generator/flywheel inertia reflected through the fixed ratio;
- shaft torsional stiffness;
- torsional damping;
- backlash deadband;
- progressive clutch/load admission;
- grid loss;
- prime-mover unloading;
- overspeed braking envelope.

The fast and slow models are intentionally separate. Multi-day solar dispatch should not require a millisecond timestep, and torsional transients should not be hidden inside a one-minute timestep.

## Default v0.3 disturbance sequence

The scenario runner injects repeatable faults rather than ideal sunshine only:

```text
DAY 1   nominal cycle
DAY 2   10:00-13:00 cloud factor = 0.25
        14:00-14:30 grid unavailable
DAY 3   recovery / storage-closure observation
```

## Repository layout

```text
dubaio/
├── README.md
├── requirements.txt
├── docs/
│   ├── specification.md
│   ├── state_machine.md
│   └── v03_design.md
├── sim/
│   ├── configs.py
│   ├── engine.py
│   ├── run_day_cycle.py
│   ├── v03_configs.py
│   ├── v03_dispatch.py
│   ├── torsional_bench.py
│   └── run_v03_scenarios.py
├── cad/
│   └── procedural_gears.py
├── tests/
│   ├── test_physics.py
│   └── test_v03.py
└── .github/workflows/
    └── tests.yml
```

## Run v0.2 baseline

```bash
python -m pip install -r requirements.txt
python sim/run_day_cycle.py --config 1mw_peak
python sim/run_day_cycle.py --config 1mw_daily_energy
```

## Run v0.3 multi-day dispatch

```bash
python sim/run_v03_scenarios.py \
  --config 1mw_daily_energy \
  --mode dispatch \
  --days 3
```

## Run v0.3 loss-of-grid torsional bench

```bash
python sim/run_v03_scenarios.py \
  --config 10kw \
  --mode torsion \
  --dt 0.01
```

## Run physics invariants

```bash
python -m unittest discover -s tests -v
```

The new v0.3 tests require, among other things:

- per-step thermal energy balance;
- no electrical dispatch during a grid-loss command;
- output power bounded by rating;
- fixed drivetrain ratio consistency;
- progressive load removal;
- zero elastic torque inside a stationary backlash deadband.

## Current CI note

The GitHub Actions workflow is valid YAML and is being triggered, but current GitHub runs are terminating before any job step is reported (`runner_id=0`, empty steps). Until GitHub provides an executable runner, CI status must **not** be interpreted as a physics-test result.

## Safety / engineering scope

Everything here is analytical or conceptual.

No gear geometry, pressure boundary, high-speed flywheel, receiver, clutch, shaft, bearing, brake, thermal-storage vessel or material selection in this repository is manufacturing-ready. Real hardware requires standards-based design, fatigue/overspeed containment, thermal analysis, controls validation and independent engineering review.

## Next gate — v0.4

1. temperature-dependent receiver radiation/convection losses;
2. explicit clutch slip-energy and thermal-capacity model;
3. shaft modal-frequency / resonance sweep;
4. periodic multi-day SOC solver instead of fixed initial storage;
5. parasitic electrical loads and cooling/pumping consumption;
6. site-DNI input from weather data;
7. comparison against a variable-speed generator + power-electronics reference architecture;
8. low-energy HIL bench specification with measurable pass/fail criteria.

---

# BLACKMAMBA SOLAR CLOCK
### **Slow as a mountain. Fast as lightning. Accounted to the joule.**
