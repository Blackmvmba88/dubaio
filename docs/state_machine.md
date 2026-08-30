# Mechanical PLC / State Sequencing

## Design rule

**Cam geometry requests a transition. Physical state authorizes it.**

The master cam is therefore not treated as a blind clock that forces a clutch at a particular wall-clock time. It is a deterministic sequencer whose request is gated by thermal reserve, shaft speed, and eventually pressure/temperature limits.

## Conceptual states

| State | Meaning | Primary condition | Action |
|---|---|---|---|
| 0 | Rest / storage | no authorized drive | drivetrain released |
| 1 | Spin-up | cam requests motion + thermal availability | master shaft accelerates; stage 1 may engage |
| 2 | Intermediate | stage-2 speed threshold crossed | stage 2 engages |
| 3 | Generation | stage-3 threshold + generator cut-in | electrical load admitted |
| 4 | Controlled unload | request or energy falls | progressive downshift / load removal |
| 5 | Protective state | overspeed, overtemperature, abnormal load | input diversion + controlled braking |

## Hysteresis

For stage `k`:

```text
rpm >= engage_rpm[k]       -> engagement may occur

rpm between thresholds     -> retain previous state

rpm <= disengage_rpm[k]    -> disengagement may occur
```

with:

```text
disengage_rpm[k] < engage_rpm[k]
```

This avoids repeated clutch chatter when shaft speed oscillates around a single threshold.

## Conceptual signal chain

```text
CAM TRACK
   |
   v
REQUEST STAGE k
   |
   +---- thermal reserve switch ----+
   |                                |
   +---- speed governor ------------+----> mechanical AND gate
   |                                |
   +---- safety permissive ---------+
                                        |
                                        v
                                  CLUTCH COMMAND
```

The physical implementation may use cams, followers, springs, hydraulic pilots, centrifugal governors, overrunning clutches, or other passive/semi-passive mechanisms. The repository does not yet prescribe a manufacturing mechanism.

## Overspeed philosophy

Do not rely on an instantaneous rigid lock for a high-energy rotating train.

Preferred conceptual sequence:

1. remove or reduce generator/load transition shocks;
2. command progressive drivetrain disengagement where safe;
3. reduce or bypass prime-mover power;
4. redirect/reject thermal input;
5. apply characterized dissipative braking;
6. use containment as the final independent protection layer.

## Known v0.2 simplification

The simulator changes stage ratio discretely and does not yet model clutch slip, torsional compliance, shaft twist, backlash, tooth contact dynamics, or synchronization energy. Those belong in v0.3 before drivetrain sizing is considered meaningful.
