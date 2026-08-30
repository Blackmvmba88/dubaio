# BlackMamba Solar Clock (BMSC)

> Mechanical solar-thermal engine, staged drivetrain, and mechanically sequenced control research.

The **BlackMamba Solar Clock** is an engineering research concept that explores a solar-thermal plant whose low-speed/high-torque prime motion is coupled to a staged drivetrain and a mechanically sequenced control layer.

## Current status

**Phase:** `BMSC Physics v0.2` — concept validation / analytical simulation.

The immediate goal is to validate conservation of energy, thermal buffering, rotational dynamics, hysteresis, drivetrain behavior, and mechanical state sequencing before any high-temperature or high-pressure prototype is considered.

## Core principle

> **The clock encodes sequence; physics authorizes transition.**

Cam geometry can request a drivetrain state, but engagement is gated by actual physical conditions such as thermal reserve and shaft speed.

## Architecture

```text
DNI(t)
  |
  v
Optical aperture
  |
  v
Receiver -> thermal storage
  |              |
  +--------------+
         |
         v
     prime mover
         |
         v
 low-RPM / high-torque master shaft
         |
         v
 mechanical PLC + staged drivetrain
         |
         v
      generator
         |
         v
      electric load
```

## What changed in v0.2

- Power is derived from solar/thermal energy first; torque and RPM are no longer independently scaled with irradiance.
- Master-shaft speed evolves from `I * domega/dt = sum(torque)`.
- Stage engagement uses hysteresis thresholds.
- The prime mover can spin up the master shaft before the downstream generator train is connected.
- Peak-power sizing is separated from 24-hour energy sizing.
- Overspeed philosophy favors unloading, bypass and controlled braking rather than an instantaneous rigid lock.
- CAD scripts are explicitly visualization-only.

## Reconciled 1 MW baseline

Using the current v0.2 assumptions (`DNI=950 W/m²`, `eta_opt=0.75`, effective receiver factor `0.83`, thermal cycle `0.35`, three drivetrain stages at `0.96`, generator `0.96`):

- **~5,688 m² aperture** closes the analytical **1 MW peak** equation.
- Under the toy 06:00–18:00 sinusoidal DNI profile, that field represents about **7.64 MWh_e/day** before storage/parasitic corrections.
- **~17,900 m² aperture** closes an idealized **24 MWh_e/day** energy budget with the same chain, before storage losses, parasitic loads, weather, soiling and reserve margins.

The `1mw_daily_energy` configuration is therefore an **energy-budget study**, not a claim of a finished 1 MW / 24 h dispatch design.

## Repository layout

```text
dubaio/
├── README.md
├── requirements.txt
├── docs/
│   ├── specification.md
│   └── state_machine.md
├── sim/
│   ├── configs.py
│   ├── engine.py
│   └── run_day_cycle.py
├── cad/
│   └── procedural_gears.py
├── tests/
│   └── test_physics.py
└── .github/workflows/
    └── tests.yml
```

## Run the simulation

```bash
python -m pip install -r requirements.txt
python sim/run_day_cycle.py --config 10kw
python sim/run_day_cycle.py --config 100kw
python sim/run_day_cycle.py --config 1mw_peak
python sim/run_day_cycle.py --config 1mw_daily_energy
```

Export a time-series CSV:

```bash
python sim/run_day_cycle.py --config 1mw_peak --csv outputs/1mw_peak.csv
```

Run the physics invariants:

```bash
python -m unittest discover -s tests -v
```

## Safety and engineering scope

This repository currently contains analytical models and conceptual visualization geometry only.

No geometry, material selection, pressure vessel, high-speed flywheel, thermal receiver, clutch, shaft, bearing or gearset in this repository should be considered manufacturing-ready without independent mechanical, thermal, fatigue, containment, controls and applicable-code review.

## Next gate — v0.3

Before industrial drivetrain sizing:

1. model clutch slip and synchronization energy;
2. account explicitly for prime-mover power rejected while torque-limited;
3. add rotational-energy accounting to generator dispatch;
4. add torsional compliance/backlash;
5. replace fractional receiver losses with a temperature-dependent thermal model;
6. run multi-day storage/dispatch simulations to periodic state-of-charge closure;
7. compare the staged mechanical architecture against a conventional variable-speed generator + power-electronics baseline;
8. define a low-energy hardware-in-the-loop bench test that emulates the master shaft without high-temperature or high-pressure working fluids.

---

**BLACKMAMBA — slow as a mountain, fast as lightning.**
