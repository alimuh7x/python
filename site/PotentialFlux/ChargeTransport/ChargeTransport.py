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
    # Parameters
    Nx = 200
    Lx = 1.0
    dx = Lx / (Nx - 1)
    epsilon0 = 8.854e-12

    # Grid
    x = np.linspace(0, Lx, Nx)

    # Charge density
    rho = np.sin(2 * np.pi * x)

    # Initialize potential (Dirichlet BC: φ=0 at both ends)
    phi = np.zeros(Nx)

    # Iteration parameters (using SOR)
    max_iter = 10000
    tol = 1e-9
    omega = 1.9  # relaxation factor

    for iter in range(max_iter):
        maxdiff = 0
        for i in range(1, Nx - 1):
            phi_new = 0.5 * (phi[i + 1] + phi[i - 1] + dx**2 * rho[i] / epsilon0)
            phi[i] = (1 - omega) * phi[i] + omega * phi_new
            maxdiff = max(maxdiff, abs(phi_new - phi[i]))

        if iter % 500 == 0:
            print(f"Iteration {iter}: max change = {maxdiff:.6e}")

        if maxdiff < tol:
            print(f"Converged in {iter} iterations")
            break

    # Plot results using Plotter
    plot = Plotter(fontsize=14)
    plot.plot2x1(
        Data=[x, rho, x, phi],
        Labels=['x', 'ρ(x)', 'x', 'φ(x)'],
        filename=str(OUTPUT_DIR / 'Numerical_SOR.png'),
        marker=False
    )

    print(f"✅ Saved: Numerical_SOR.png")


if __name__ == "__main__":
    main()
