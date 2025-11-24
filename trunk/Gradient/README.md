# Gradient Field Visualization

## Overview

This module visualizes 2D gradient fields and 3D surface plots for understanding spatial derivatives and field distributions.

## Simulations

### 1. 2D Gradient Field

![2D Gradient Field](gradient_plot.png){ align=right width=45% }

Visualizes the temperature field:

$$
T(x,y) = e^{-0.1(x^2 + y^2)}
$$

with gradient vectors $(\nabla T)$ overlaid as arrows.

### 2. 3D Surface Plot

![3D Surface](Surf.png){ align=right width=45% }

Creates a smooth 3D surface using:

$$
z(x,y) = \frac{\sin(r)}{r + \epsilon}
$$

where $r = \sqrt{x^2 + y^2}$

## Output

- `gradient_plot.png` - 2D contour plot with gradient arrows
- `Surf.png` - 3D surface plot

## Usage

```bash
python3 Gradient.py
```

## Applications

- Understanding heat flow and diffusion
- Visualizing potential energy landscapes
- Demonstrating field gradients in physics
