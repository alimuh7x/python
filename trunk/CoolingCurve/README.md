# Cooling Curve Simulation

This script simulates a cooling process using a custom, non-physical model to demonstrate how different rate equations affect the cooling curve.

## The Model

This script uses a custom, non-linear differential equation:

$$
\frac{dT}{dt} = -k \sin(T)
$$

This model is for illustrative purposes. It differs from the standard **Newton's Law of Cooling**, which describes physical cooling as:

$$ 
\frac{dT}{dt} = -k (T - T_{\text{ambient}}) 
$$

Newton's Law predicts an exponential decay, often with a plateau during phase changes. Our script's sine-based model results in an oscillating cooling rate, not dependent on ambient temperature difference.

## Curve Behavior

![Cooling Curve](cooling_curve.png){ align=right width=45% }

- **Oscillating Cooling Rate:** The `sin(T)` term causes the cooling rate (red dashed line) to oscillate, which is not physically realistic.
- **Wavy Temperature Decay:** As a result, the temperature (blue line) decreases in a wave-like pattern, not an exponential decay.
- **No Phase-Change Plateau:** The curve lacks a flat plateau, which would be present in a real-world cooling curve during solidification.

## Parameters

- `T_initial`: Starting temperature (°C).
- `T_ambient`: Ambient temperature (°C) - **Note: This parameter is not used in the current model.**
- `k`: Cooling rate constant.
- `dt`: Time step for the simulation.
- `t_end`: Total simulation time.

## Algorithm Pseudocode

<pre class="algorithm">
Algorithm 1: Cooling Curve Simulation

Input:  T_initial = 100, k = 0.01, dt = 0.1, t_end = 100
Output: Temperature vs Time plot (cooling_curve.png)
Result: Simulated cooling curve using custom differential equation

 1  T ← T_initial
 2  t ← 0
 3  T_list ← []
 4  t_list ← []
 5  <b>while</b> t < t_end <b>do</b>
 6  │   dT ← -k · sin(T) · dt
 7  │   T ← T + dT
 8  │   <b>if</b> record_data <b>then</b>
 9  │   │   T_list.append(T)
10  │   │   t_list.append(t)
11  │   <b>end</b>
12  │   t ← t + dt
13  <b>end</b>
14  plot(t_list, T_list)
15  savefig("cooling_curve.png")
</pre>

## Usage

```bash
python3 CoolingCurve.py
```
