# BMSC Low-Energy Hardware-in-the-Loop Bench

## Purpose

Validate the BlackMamba Solar Clock control and drivetrain ideas **without solar concentration, steam, molten salts, pressure vessels, or industrial stored energy**.

The bench emulates the slow/high-torque prime mover with an electrically controlled motor and measures whether the mechanical-clock logic behaves predictably under disturbances.

## Safety boundary

The first bench is intentionally low energy. It should be designed so that a failed clutch, software command, sensor, or linkage cannot create an industrial overspeed or pressure event.

No high-temperature or high-pressure subsystem is part of this validation gate.

## Functional architecture

```text
COMMAND / DISTURBANCE PROFILE
          |
          v
  low-energy drive motor
          |
    torque transducer
          |
        encoder A
          |
          v
   MASTER CLOCK SHAFT
      |           |
      |         cam disk
      |           |
      |        switches / followers
      |           |
      v           v
 compliant coupling ---- mechanical sequencing
          |
       encoder B
          |
          v
    load / brake emulator
          |
          v
    measured dissipation
```

## What the bench must measure

1. master-shaft RPM;
2. load-side RPM;
3. transmitted torque;
4. torsional angle or relative shaft phase;
5. clutch/load-command fraction;
6. cam state;
7. mechanical governor state;
8. brake command/state;
9. electrical input power to the drive emulator;
10. electrical/mechanical power absorbed by the load emulator.

## Required validation scenarios

### HIL-01 — cold start / spin-up

Goal: verify that the master side reaches its sequencing threshold without an abrupt load insertion.

Pass criteria:
- monotonic or bounded spin-up;
- no repeated clutch chatter;
- no commanded hard lock;
- load admission follows the declared ramp envelope.

### HIL-02 — cloud-equivalent torque dip

Emulate a temporary reduction in prime-mover torque.

Pass criteria:
- stage/load state does not chatter around a threshold;
- hysteresis behaves as modeled;
- recovery occurs without a torque impulse outside the bench limit.

### HIL-03 — sudden loss of electrical load

Drop the load command while the drivetrain is at nominal speed.

Pass criteria:
- load fraction ramps toward zero;
- prime-mover admission is reduced;
- overspeed remains below the declared bench trip envelope;
- any brake action is progressive and measurable.

### HIL-04 — sensor/control blackout

Disable the supervisory software while retaining the passive/mechanical layer.

Pass criteria:
- the mechanism returns to or remains in a bounded low-energy state;
- no software restart is required to prevent runaway;
- passive state can be inferred from physical positions.

### HIL-05 — mechanical sequencing fault

Prevent one cam follower or load-stage command from moving as expected.

Pass criteria:
- failure remains local;
- downstream load is not admitted into an invalid speed window;
- fault is mechanically/electrically observable.

## Data products

Every bench run should export a timestamped CSV containing at minimum:

```text
time_s
rpm_master
rpm_load
torque_nm
relative_angle_rad
load_fraction
cam_state
governor_state
brake_state
input_power_w
absorbed_power_w
```

## Acceptance philosophy

The bench is not intended to prove 1 MW operation. It proves whether the **control concept scales logically** before expensive thermal and structural engineering begins.

A failed low-energy bench test is a successful research result if it prevents a bad architecture from being scaled.

## Exit criteria for a thermal prototype discussion

Do not progress to a thermal prototype merely because the mechanism rotates. Progress only after:

1. repeatable energy accounting;
2. bounded loss-of-load response;
3. demonstrated hysteresis/no chatter;
4. measurable torsional behavior matching the simulation order of magnitude;
5. passive safe-state behavior during supervisory blackout;
6. documented failure modes and recovery sequence;
7. independent review of the next prototype's stored-energy hazards.
