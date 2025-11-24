# Cooling Curve Simulation

## Overview

This module simulates the cooling behavior of a material over time using a non-linear cooling rate equation.

## Theory

The simulation implements the differential equation:

$$
\frac{dT}{dt} = -k \sin(T)
$$

where:

- $T$ is the temperature (°C)
- $t$ is time (s)
- $k$ is the cooling rate constant

## Parameters

- `T_initial = 100.0` - Initial temperature (°C)
- `T_ambient = 25.0` - Ambient temperature (°C)
- `k = 0.05` - Cooling rate constant
- `dt = 0.05` - Time step (s)
- `t_end = 200.0` - End time (s)

## Output

![Cooling Curve](cooling_curve.png){ align=right width=45% }

The simulation generates `cooling_curve.png` showing:

- Temperature vs. time (blue, left axis)
- Temperature increment vs. time (red dashed, right axis)

## Usage

```bash
python3 CoolingCurve.py
```

## Results

The dual y-axis plot shows both the temperature decay and the rate of cooling over time. The non-linear sine function creates interesting cooling dynamics compared to Newton's law of cooling.
