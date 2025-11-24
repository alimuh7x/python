#!/home/alimuh7x/myenv/bin/python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

# Add src/ folder to Python's module search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(CURRENT_DIR, "..", "..", "src")
sys.path.append(os.path.realpath(SRC_PATH))

from Plotter import Plotter

OUTPUT_DIR = Path(__file__).parent


def main() -> None:
    # Material & geometry parameters
    E = 210e9  # Young's modulus (Pa)
    sigma = 100e6  # Applied stress (Pa)
    delta = 0.001  # Applied displacement (m)
    B = 0.01  # Thickness (m)

    # Crack length range
    a = np.linspace(0.001, 0.05, 200)  # crack length (m)

    # Energy release rate formulas
    # Fixed load (stress-controlled): G ~ sigma^2 * pi * a / E
    G_load = (sigma**2 * np.pi * a) / E

    # Fixed displacement (strain-controlled): G ~ (delta^2 * E * pi) / (a)
    G_disp = (delta**2 * E * np.pi) / a

    # Critical fracture energy (material property)
    Gc = 1000  # J/m^2 (typical for brittle material)

    # Plot using Plotter
    plot = Plotter(fontsize=14)
    plot.plot2x1(
        Data=[a, G_load, a, G_disp],
        Labels=['a (m)', 'Fixed Load G (J/m²)', 'a (m)', 'Fixed Displacement G (J/m²)'],
        filename=str(OUTPUT_DIR / 'EnergyReleaseRate.png'),
        marker=True
    )

    # Text output
    print(f"At G = Gc = {Gc:.1f} J/m²:")
    print(f"Fixed load: crack length = {np.interp(Gc, G_load, a):.4f} m")
    print(f"Fixed displacement: crack length = {np.interp(Gc, G_disp, a):.4f} m")
    print(f"✅ Saved: EnergyReleaseRate.png")


if __name__ == "__main__":
    main()
