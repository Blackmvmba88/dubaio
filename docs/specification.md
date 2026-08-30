# BMSC Physics v0.2 — Technical Specification

## Status

Concept validation model. This document defines the analytical baseline for the BlackMamba Solar Clock (BMSC). It is **not** a manufacturing specification and does not authorize construction of pressure vessels, high-speed flywheels, high-temperature receivers, or industrial gearing.

## 1. Energy architecture

```text
DNI(t)
  |
  v
Optical aperture --eta_opt--> receiver --losses--> thermal buffer
                                                |
                                                v
                                           prime mover
                                                |
                                                v
                                     low-RPM / high-torque shaft
                                                |
                                                v
                              staged drivetrain + mechanical PLC
                                                |
                                                v
                                      generator / electrical load
```

The model always computes available **power first**. Torque and angular velocity are then states of the rotating system; they are never both scaled independently with irradiance.

### 1.1 Optical capture

\[
P_{opt}(t)=DNI(t) A_{aperture}\eta_{opt}
\]

### 1.2 Receiver useful power

For v0.2 receiver losses are represented by a fractional design parameter:

\[
P_{rec}(t)=\max\left(0,P_{opt}(t)(\eta_{rec}-f_{rec,loss})\right)
\]

A later thermal model should replace this approximation with explicit radiative and convective terms.

### 1.3 Thermal storage

\[
\frac{dE_{th}}{dt}=P_{rec}-P_{th,cycle}-Q_{store,loss}
\]

with a first-order storage loss approximation:

\[
Q_{store,loss}=E_{th}\frac{f_{loss,h}}{3600}
\]

where `f_loss,h` is the fractional energy loss per hour.

### 1.4 Prime mover and shaft power

\[
P_{shaft}=P_{th,cycle}\eta_{cycle}
\]

The available drive torque is power-limited and design-limited:

\[
\tau_{drive}=\min\left(\tau_{max},\frac{P_{shaft}}{\max(\omega_m,\omega_{min})}\right)
\]

If the torque limit is active at low speed, not all available thermal power is converted to shaft power. That unused power must be rejected, bypassed, or retained thermally in a later plant model.

## 2. Rotational dynamics

The master shaft state is governed by:

\[
I_{eq}\dot{\omega}_m=\tau_{drive}-\tau_{load,eq}-\tau_{friction}
\]

For a speed-increasing transmission with cumulative ratio

\[
R_k=\frac{\omega_{out}}{\omega_m}=\prod_{i=1}^{k}r_i
\]

output inertia reflected to the master shaft scales as:

\[
I_{ref}=I_{out}R_k^2
\]

and a generator resisting torque reflected to the master shaft is approximated by:

\[
\tau_{load,eq}=\frac{\tau_{gen}R_k}{\eta_{drive,k}}
\]

## 3. Mechanical state machine

The core design rule is:

> **The clock encodes sequence; physics authorizes transition.**

A stage may be requested by its cam window, but engagement additionally requires sufficient thermal reserve and master-shaft speed.

A stage remains engaged until its lower disengagement threshold is crossed. This creates true hysteresis and prevents rapid clutch chatter under short irradiance disturbances.

## 4. Nominal drivetrain example

A 1.8 RPM master shaft coupled to an 1800 RPM generator requires a nominal speed multiplication of:

\[
R_T=1000:1
\]

A conceptual three-stage cascade may use `10 x 10 x 10`. This is a **kinematic placeholder**, not a final gearset design. Real planetary ratios, tooth counts, carrier/ring/sun constraints, bearing loads, contact stress, lubrication, torsional modes, and clutch synchronization must be solved independently.

At 96% efficiency per stage:

\[
\eta_{drive}=0.96^3=0.884736
\]

With a 96% generator efficiency, the master-shaft power required for 1 MW electrical at the generator terminals is approximately:

\[
P_{master}=\frac{1\,MW}{0.884736\times0.96}\approx1.177\,MW
\]

At 1.8 RPM (`0.18850 rad/s`) this corresponds to approximately:

\[
\tau_m\approx6.25\,MN\cdot m
\]

## 5. Peak power vs continuous power

A critical distinction:

- `1 MW peak` means the plant can reach 1 MW under design irradiance.
- `1 MW continuous` means the solar field must harvest enough daily energy to supply 24 MWh_e/day after all losses and storage requirements.

Using the repository's baseline toy profile:

- DNI peak: `950 W/m^2`
- daylight: 06:00–18:00
- sinusoidal irradiance
- optical efficiency: `0.75`
- receiver effective factor: `0.88 - 0.05 = 0.83`
- thermal-to-electrical target: approximately `0.32`

A `4386 m^2` aperture is a reasonable order-of-magnitude **peak-power** case, but it does not provide enough daily energy for a flat 1 MW output over 24 h.

Under the simplified sinusoidal profile, approximately `16,600 m^2` of aperture is required merely to close the idealized daily energy balance for 1 MW continuous output with the above receiver assumptions. Real deployment would require additional margin for weather, cosine losses, soiling, downtime, parasitic loads, thermal losses, dispatch reserve, and seasonal DNI variation.

## 6. Safety architecture principles

The simulation should prefer energy removal over hard locking:

1. unload electrical torque in a controlled manner;
2. disengage drivetrain stages progressively;
3. bypass or reduce prime-mover input;
4. reject or redirect thermal input;
5. use passive braking only within a characterized energy envelope.

A high-inertia or high-speed train should **not** be assumed safe merely because a mechanical pawl or trinchet exists.

## 7. CAD status

Procedural CAD in `cad/` is visualization-only. The current simplified tooth geometry is not involute and must not be manufactured. Any industrial drivetrain requires standards-based gear design, fatigue analysis, overspeed containment, lubrication design, bearing sizing, shaft critical-speed analysis, and independent engineering review.
