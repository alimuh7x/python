#!/home/alimuh7x/myenv/bin/python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Add src/ folder to Python's module search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(CURRENT_DIR, "..", "..", "src")
sys.path.append(os.path.realpath(SRC_PATH))

OUTPUT_DIR = Path(__file__).parent


def main() -> None:
    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=12)

    # Domain setup
    Nx = 200
    Lx = 1.0e-7  # 100 nm domain
    dx = Lx / (Nx - 1)
    x = np.linspace(0, Lx, Nx)

    # Physical constants (Cui et al. 2022)
    epsilon0 = 8.854e-12  # vacuum permittivity (F/m)
    F = 96485  # Faraday constant (C/mol)
    R = 8.314  # gas constant (J/mol/K)
    T = 298  # temperature (K)

    # Diffusion coefficients (m^2/s)
    D_Fe = 5e-10
    D_Cl = 5e-10

    # Mobilities (Nernst–Einstein relation)
    mu_Fe = D_Fe * F / (R * T)
    mu_Cl = D_Cl * F / (R * T)

    # Atomic and saturation concentrations (mol/m³)
    c_solid = 1.43e5  # atomic density of Fe
    c_sat = 5.1e3  # solubility limit (Fe²⁺ in electrolyte)

    # Normalized mole fractions (dimensionless)
    X_Fe_sat = c_sat / c_solid  # = 0.036
    X_Cl_sat = X_Fe_sat  # same for neutrality

    # Time settings
    dt = 1e-3
    nsteps = 1

    # Initial mole fraction profiles (dimensionless)
    X_Fe = X_Fe_sat * np.exp(-((x - 0.3 * Lx)**2) / (0.002 * Lx**2))
    X_Cl = X_Cl_sat * np.exp(-((x - 0.7 * Lx)**2) / (0.002 * Lx**2))

    # Normalize (max = X_sat)
    X_Fe = X_Fe / np.max(X_Fe) * X_Fe_sat
    X_Cl = X_Cl / np.max(X_Cl) * X_Cl_sat

    # Convert to actual concentration (mol/m³)
    c_Fe = X_Fe * c_solid
    c_Cl = X_Cl * c_solid

    z_Fe = 2  # Fe²⁺
    z_Cl = -1  # Cl⁻

    # Time evolution (single iteration)
    for step in range(nsteps):
        # Charge density (C/m³)
        rho = F * (z_Fe * c_Fe + z_Cl * c_Cl)

        # Solve Poisson equation via FFT
        rho_hat = np.fft.fft(rho)
        k = (2 * np.pi / Lx) * np.concatenate([np.arange(0, Nx // 2), np.arange(-Nx // 2, 0)])
        k2 = k**2
        k2[0] = 1
        phi_hat = -rho_hat / (epsilon0 * k2)
        phi_hat[0] = 0
        phi = np.fft.ifft(phi_hat).real

        # Electric field
        E = -np.gradient(phi, dx)

        # Ionic fluxes (drift only)
        J_Fe = mu_Fe * z_Fe * F * c_Fe * E
        J_Cl = mu_Cl * z_Cl * F * c_Cl * E

        # Update concentrations (conservation)
        c_Fe = c_Fe - dt * np.gradient(J_Fe, dx) / (F * z_Fe)
        c_Cl = c_Cl - dt * np.gradient(J_Cl, dx) / (F * z_Cl)

        # Clamp to physical range
        c_Fe = np.maximum(c_Fe, 0)
        c_Cl = np.maximum(c_Cl, 0)

    # Plots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 10))

    ax1.plot(x * 1e9, c_Fe, 'r', linewidth=1.5, label='Fe²⁺')
    ax1.plot(x * 1e9, c_Cl, 'b', linewidth=1.5, label='Cl⁻')
    ax1.set_xlabel('x (nm)', fontproperties=font)
    ax1.set_ylabel('c_i (mol/m³)', fontproperties=font)
    ax1.set_title('Final Concentrations (Cui et al. 2022 values)', fontproperties=font)
    ax1.legend(prop=font)
    ax1.grid(True)

    ax2.plot(x * 1e9, phi, 'k', linewidth=1.5)
    ax2.set_xlabel('x (nm)', fontproperties=font)
    ax2.set_ylabel('φ (V)', fontproperties=font)
    ax2.set_title('Electric Potential', fontproperties=font)
    ax2.grid(True)

    ax3.plot(x * 1e9, E, 'm', linewidth=1.5)
    ax3.set_xlabel('x (nm)', fontproperties=font)
    ax3.set_ylabel('E (V/m)', fontproperties=font)
    ax3.set_title('Electric Field', fontproperties=font)
    ax3.grid(True)

    plt.tight_layout()
    filename = OUTPUT_DIR / "ElectricField_Vectors.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    # Density plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x * 1e9, rho, 'r', linewidth=1.5)
    ax.set_xlabel('x (nm)', fontproperties=font)
    ax.set_ylabel('ρ (C/m³)', fontproperties=font)
    ax.set_title('Charge Density', fontproperties=font)
    ax.grid(True)

    filename = OUTPUT_DIR / "Density.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    print('✅ Saved: ElectricField_Vectors.png, Density.png')
    print('Simulation completed using mole fractions from Cui et al. (2022).')


if __name__ == "__main__":
    main()
