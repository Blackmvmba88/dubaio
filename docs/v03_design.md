# BMSC Physics v0.3 — Split-Timescale Validation Architecture

## Status

`v0.3` extends the BlackMamba Solar Clock analytical baseline without claiming a manufacturable machine. Its purpose is to expose failure modes earlier by separating slow energy dynamics from fast drivetrain transients.

> **The clock encodes sequence; physics authorizes transition; the ledger decides whether the transition was energetically possible.**

## 1. Why two simulation clocks

A solar/storage plant evolves over minutes, hours and days. Shaft torsion, clutch slip, backlash and loss-of-load events can evolve over milliseconds to seconds. Integrating both on one timestep either makes the multi-day study unnecessarily expensive or hides fast mechanical modes.

Therefore v0.3 uses two coupled conceptual models:

```text
SLOW MODEL (seconds -> days)
DNI -> receiver -> thermal buffer -> dispatch -> electrical energy ledger

FAST MODEL (milliseconds -> seconds)
prime-mover torque -> master inertia -> compliant shaft -> reflected load inertia
                                      -> clutch/load ramp -> generator/grid
```

The models exchange design envelopes rather than pretending to be a single high-fidelity plant simulation.

## 2. Slow model: exact thermal ledger

For every integration step:

\[
E_{old}+E_{receiver}=E_{new}+E_{cycle}+E_{storage\ loss}+E_{rejected}
\]

The simulator exposes the residual of this equation as `balance_error_j`. A regression test requires that residual to remain approximately zero.

Electrical power is derived from thermal-cycle energy through the declared conversion chain:

\[
\eta_{th\rightarrow e}=\eta_{cycle}\eta_{drive}\eta_{gen}
\]

The model also tracks:

- state of charge;
- thermal overflow/rejection;
- storage loss;
- cloud attenuation;
- electrical-demand fraction;
- grid availability.

### Synthetic disturbance scenario

The default v0.3 scenario runner injects:

1. normal day 1;
2. day-2 cloud attenuation to 25% from 10:00–13:00;
3. day-2 grid outage from 14:00–14:30;
4. recovery and a third day to observe state-of-charge closure.

These events are not site forecasts. They are repeatable regression disturbances.

## 3. Fast model: two-inertia torsional bench

The drivetrain is represented in master-shaft coordinates.

Generator-side rotating inertia is reflected through the fixed speed ratio:

\[
I_{load,eq}=I_{load}R^2
\]

The shaft coupling is represented as a torsional spring-damper with backlash deadband:

\[
\tau_s=k_t\theta_{eff}+c_t(\omega_m-\omega_l)
\]

where `theta_eff = 0` inside the backlash window.

The two equations of motion are:

\[
I_m\dot{\omega}_m=\tau_{drive}-\tau_s-\tau_{fr,m}-\tau_{brake}
\]

\[
I_{load,eq}\dot{\omega}_l=\tau_s-\tau_{load,eq}-\tau_{fr,l}
\]

The fixed gear ratio remains continuously meshed. The mechanical PLC ramps **load admission**, avoiding the unphysical instantaneous creation/removal of reflected inertia that occurred when ratio stages themselves were treated as appearing discontinuously.

## 4. Loss-of-grid philosophy

Loss of electrical load is modeled as an energy-removal problem, not a rigid-lock problem.

Conceptual sequence:

```text
GRID LOSS
   |
   +--> electrical load target -> 0
   +--> clutch/load admission ramps down
   +--> prime-mover admission closes rapidly
   +--> overspeed governor becomes active
   +--> passive brake only dissipates energy above a characterized trip speed
```

No pawl, ratchet or instantaneous hard stop is treated as a safe solution for a high-inertia train.

## 5. New repository modules

- `sim/v03_dispatch.py` — multi-day energy/storage dispatch with exact thermal ledger.
- `sim/torsional_bench.py` — fast two-inertia torsional and grid-loss model.
- `sim/v03_configs.py` — transient-only conceptual parameter overlays.
- `sim/run_v03_scenarios.py` — reproducible cloud, grid-loss and torsional scenarios.
- `tests/test_v03.py` — energy-ledger and mechanical-state invariants.

## 6. Validation gates before v0.4

v0.3 is considered analytically useful only when:

1. thermal ledger residual remains near numerical zero;
2. electrical power never exceeds the declared conversion chain or rated generator power;
3. grid loss commands zero electrical dispatch immediately in the slow model;
4. fast-model load admission ramps instead of discontinuously switching torque;
5. backlash deadband produces no elastic torque while relative speed is zero;
6. loss-of-load overspeed remains bounded under a declared governor/brake envelope;
7. multi-day storage state does not drift upward from numerical energy creation;
8. any continuous-output claim is supported by periodic or bounded state-of-charge behavior, not merely by one-day aperture arithmetic.

## 7. What v0.3 still does not prove

It does not establish:

- manufacturable gear geometry;
- clutch thermal capacity;
- real shaft stiffness or fatigue life;
- pressure-vessel safety;
- receiver temperature field;
- real molten-salt chemistry;
- site-specific DNI yield;
- generator electromagnetic design;
- grid-code compliance;
- economic competitiveness.

Those remain future engineering layers and require domain-specific tools, validated material data and independent review.
