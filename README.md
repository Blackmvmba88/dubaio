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
- Stage engagement uses true hysteresis thresholds.
- The prime mover can spin up the master shaft before the downstream generator train is connected.
- Peak-power sizing is separated from 24-hour energy sizing.
- Overspeed philosophy favors unloading, bypass and controlled braking rather than an instantaneous rigid lock.
- CAD scripts are explicitly visualization-only.

## Important energy distinction

The `4386 m^2` case is an **approximately 1 MW peak** aperture under the simplified design-point assumptions. It is not a 1 MW / 24 h field.

With the repository's toy 06:00–18:00 sinusoidal DNI profile and current optical/receiver assumptions, an aperture around `16,600 m^2` is required merely to close the idealized daily thermal-energy budget associated with a flat 1 MW electrical target. Real site sizing would require additional margin for weather, seasonal DNI, soiling, parasitic loads, storage losses, downtime and reserve.

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
python sim/run_day_cycle.py --config 1mw_continuous_ideal
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
2. add torsional compliance/backlash;
3. replace fractional receiver losses with a temperature-dependent thermal model;
4. run multi-day storage/dispatch simulations;
5. compare the staged mechanical architecture against a conventional variable-speed generator + power-electronics baseline;
6. define a low-energy hardware-in-the-loop bench test that emulates the master shaft without high-temperature or high-pressure working fluids.

---

**BLACKMAMBA — slow as a mountain, fast as lightning.**
