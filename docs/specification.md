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
P_{opt}(t)=DNI(t)A_{aperture}\eta_{opt}
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

## 5. Reconciled 1 MW sizing

The v0.2 baseline uses:

- `DNI_peak = 950 W/m²`
- `eta_opt = 0.75`
- effective receiver factor `eta_rec - f_loss = 0.88 - 0.05 = 0.83`
- `eta_cycle = 0.35`
- `eta_drive = 0.96^3 = 0.884736`
- `eta_gen = 0.96`

The complete aperture-to-electric peak efficiency is therefore:

\[
\eta_{aperture\rightarrow e}=0.75\times0.83\times0.35\times0.884736\times0.96\approx0.2221
\]

The aperture required for approximately 1 MW electric at the design point is:

\[
A_{1MW,peak}=\frac{1,000,000}{950\eta_{aperture\rightarrow e}}\approx5,688\,m^2
\]

The corresponding thermal-cycle input is approximately:

\[
P_{th,cycle}=\frac{1\,MW}{0.35\times0.884736\times0.96}\approx3.364\,MW_{th}
\]

### 5.1 Peak power is not 24-hour energy

The idealized DNI profile used by the simulator is a sine wave from 06:00 to 18:00. Its equivalent full-sun duration at peak DNI is:

\[
t_{eq}=\frac{24}{\pi}\approx7.639\,h
\]

Therefore the `5,688 m²` peak case yields only about `7.64 MWh_e/day` before storage/parasitic corrections. It is correctly a **1 MW peak** case, not a 1 MW continuous case.

To close an idealized `24 MWh_e/day` budget with the same efficiency chain requires approximately:

\[
A_{24MWh}\approx17,870\,m^2
\]

The repository rounds this exploratory case to `17,900 m²`.

This is only a daily-energy closure. A true 1 MW continuous plant additionally requires a dispatch policy, sufficient thermal storage power and capacity, start/end state-of-charge closure across multiple days, weather/seasonal margins, parasitic loads, soiling, downtime, cosine losses and storage losses.

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

## 8. Next physics gate (v0.3)

Before sizing industrial hardware:

1. model clutch slip and synchronization energy;
2. account explicitly for unused prime-mover power when torque-limited;
3. add rotational-energy accounting to the electrical dispatch balance;
4. add torsional compliance, backlash and shaft modes;
5. replace fractional receiver losses with temperature-dependent radiation/convection;
6. run multi-day simulations until storage state of charge reaches a periodic steady cycle;
7. compare BMSC against a conventional variable-speed generator + power-electronics architecture.
