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
    L0 = 1e-10
    aa = 0.5
    nM = 2
    F = 96485
    Rg = 8.314
    T = 298
    phi_m = 0.2

    phi_l = np.linspace(0.0, 0.2, 200)
    eta = phi_m - phi_l

    La = L0 * np.exp((aa * nM * F * eta) / (Rg * T))

    exponential_term = np.exp((aa * nM * F * phi_m) / (Rg * T))
    print(f"exp((aa * nM * F * phi_m) / (Rg * T)) = {exponential_term:.6e}")

    plot = Plotter(fontsize=12)
    plot.plot1D(phi_l, La, xlabel=r'$\phi_\ell$ Liquid potential', ylabel=r'mobility ($L_\alpha$)', filename='Mobility.png', marker=True)
    plot.plot1D(phi_l, eta, xlabel=r'$\phi_\ell$ Liquid potential', ylabel=r'Overpotential $\eta$', filename='Overpotential.png', marker=True)
    print("✅ Saved: Anodic_Mobility_vs_Liquid_Potential.png")


if __name__ == "__main__":
    main()
