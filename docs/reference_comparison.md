# BMSC vs. Conventional Reference Architecture

## Purpose

The BlackMamba Solar Clock must be compared against a credible alternative, not only against itself. This document introduces an intentionally simple reference path using the same optical field, receiver and thermal cycle, followed by a variable-speed generator path and power electronics.

The comparison is not a vendor benchmark and does not prove cost or reliability. Its job is to expose the efficiency price BMSC must justify through other system-level advantages.

## Shared assumptions

- DNI design point: `950 W/m²`
- optical efficiency: `0.75`
- effective receiver factor: `0.83`
- thermal-cycle efficiency: `0.35`

## BMSC path

Current conceptual drivetrain assumptions:

```text
three mechanical stages: 0.96³
 generator efficiency:    0.96
```

Therefore:

\[
\eta_{shaft\rightarrow grid,BMSC}=0.96^3\times0.96\approx0.84935
\]

Including optics, receiver and thermal cycle:

\[
\eta_{DNI\rightarrow grid,BMSC}\approx0.18505
\]

The corresponding analytical aperture for 1 MW at the design DNI point is:

\[
A_{BMSC}\approx5688.3\ m^2
\]

## Conventional reference path

Illustrative assumptions:

```text
mechanical coupling:  0.98
 generator:            0.97
 power electronics:    0.97
```

Thus:

\[
\eta_{shaft\rightarrow grid,ref}=0.98\times0.97\times0.97\approx0.92208
\]

and:

\[
\eta_{DNI\rightarrow grid,ref}\approx0.20090
\]

The corresponding analytical aperture is:

\[
A_{ref}\approx5239.6\ m^2
\]

## Present efficiency penalty

Under these assumptions:

\[
\frac{A_{BMSC}}{A_{ref}}-1\approx8.56\%
\]

So the current BMSC concept requires roughly **8.6% more optical aperture** to reach the same 1 MW design-point electrical output.

That is not a failure of the project. It defines the research question more honestly.

## What BMSC must prove to earn that penalty

The mechanical-clock architecture only becomes compelling if the efficiency penalty is outweighed by one or more verified advantages such as:

1. passive or mechanically guaranteed fail-safe sequencing;
2. graceful operation during electronics/control faults;
3. reduced dependence on high-power switching electronics;
4. long-life maintainability with locally serviceable mechanical modules;
5. predictable degradation rather than abrupt controller failure;
6. useful direct mechanical outputs before electrical conversion;
7. resilience in harsh thermal/dust environments;
8. modular drivetrain isolation that limits fault propagation.

None of these benefits is assumed true merely because the mechanism is mechanical. They must be measured.

## Decision rule

A future architecture decision should compare at least:

- annual net MWh;
- parasitic consumption;
- capex per kW;
- maintenance labor and parts;
- mean time between critical failures;
- restart behavior after loss of grid/control;
- component replacement time;
- aperture/land penalty;
- lifetime drivetrain losses;
- safety envelope and fault containment.

If BMSC cannot demonstrate a meaningful system-level advantage after accounting for its extra mechanical losses and complexity, the conventional reference should win.

That is the point of keeping the reference model inside the repository.
