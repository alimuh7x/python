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


def myprint(*args):
    """Print formatted key-value pairs"""
    output = []
    for i in range(0, len(args), 2):
        if i + 1 >= len(args):
            break
        name = args[i]
        val = args[i + 1]
        if isinstance(val, (int, float)):
            if abs(val) < 1e4 and abs(val) > 1e-3:
                output.append(f"{name} = {val:.4f}")
            else:
                output.append(f"{name} = {val:.3e}")
        else:
            output.append(f"{name} = {val}")
    print("  ".join(output))


def main() -> None:
    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=14)

    # Poisson equation in 1D using FFT: d²φ/dx² = -ρ(x)/ε₀
    # Parameters
    Nx = 200
    dx = 0.01
    epsilon0 = 8.854e-12

    i = np.arange(Nx)
    x = i * dx
    Lx = (Nx - 1) * dx

    myprint("dx", dx)
    myprint("Nx", Nx)
    myprint("Lx", Lx)

    # Charge density
    rho = np.sin(2 * np.pi * x / Lx)

    Totalrho = np.trapz(np.abs(rho), x)
    myprint("Total charge density C / m^3", Totalrho)

    # Solve using FFT
    rho_hat = np.fft.fft(rho)
    k = (2 * np.pi / Lx) * np.concatenate([np.arange(0, Nx // 2), np.arange(-Nx // 2, 0)])
    k2 = k**2
    k2[0] = 1  # avoid division by zero
    phi_hat = rho_hat / (epsilon0 * k2)
    phi_hat[0] = 0  # set mean potential to zero
    phi = np.fft.ifft(phi_hat).real

    # Plot results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

    ax1.plot(x, rho, 'r', linewidth=1.5)
    ax1.set_xlabel('x', fontproperties=font)
    ax1.set_ylabel('ρ(x)', fontproperties=font)
    ax1.set_title('Charge density ρ(x) = cos(2πx)', fontproperties=font)
    ax1.tick_params(labelsize=14, width=1.5)
    ax1.grid(True)

    ax2.plot(x, phi, 'b', linewidth=1.5)
    ax2.set_xlabel('x', fontproperties=font)
    ax2.set_ylabel('φ(x)', fontproperties=font)
    ax2.set_title('Potential φ(x)', fontproperties=font)
    ax2.tick_params(labelsize=14, width=1.5)
    ax2.grid(True)

    plt.tight_layout()
    filename = OUTPUT_DIR / "Numerical_SOR.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    TotalPotentialEnergy = 0.5 * np.trapz(rho * phi, x)
    myprint("Total Potential Energy J/m^2", TotalPotentialEnergy)

    # Compute electric field and movement from potential
    E = -np.gradient(phi, dx)
    mu = 5e-10  # Mobility (m^2/V·s)
    J = mu * rho * E

    # Plot field, velocity, and flux
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

    ax1.plot(x, E, 'm', linewidth=1.5)
    ax1.set_xlabel('x', fontproperties=font)
    ax1.set_ylabel('E(x)', fontproperties=font)
    ax1.set_title('Electric Field E(x) = -dφ/dx', fontproperties=font)
    ax1.tick_params(labelsize=14, width=1.5)
    ax1.grid(True)

    ax2.plot(x, J, 'k', linewidth=1.5)
    ax2.set_xlabel('x', fontproperties=font)
    ax2.set_ylabel('J(x)', fontproperties=font)
    ax2.set_title('Charge Flux J(x) = M ρ·E', fontproperties=font)
    ax2.tick_params(labelsize=14, width=1.5)
    ax2.grid(True)

    plt.tight_layout()
    filename = OUTPUT_DIR / "Charge_Movement_from_Potential.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    # Compute rho_dot (charge accumulation rate)
    rho_dot = -np.gradient(J, dx)
    rho_dot = rho_dot - np.mean(rho_dot)  # remove drift
    new_rho = rho + 0.01 * rho_dot  # smaller time step

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

    ax1.plot(x, rho_dot, 'k', linewidth=1.5)
    ax1.set_title('Rate of Change ρ̇(x) = -dJ/dx', fontproperties=font)
    ax1.set_xlabel('x', fontproperties=font)
    ax1.set_ylabel('ρ̇(x)', fontproperties=font)
    ax1.tick_params(labelsize=14, width=1.5)
    ax1.grid(True)

    ax2.plot(x, rho, 'r', linewidth=1.5, label='Old ρ')
    ax2.plot(x, new_rho, 'b--', linewidth=1.5, label='New ρ')
    ax2.set_title('Old vs New Charge Density ρ(x)', fontproperties=font)
    ax2.tick_params(labelsize=14, width=1.5)
    ax2.set_xlabel('x', fontproperties=font)
    ax2.set_ylabel('ρ(x)', fontproperties=font)
    ax2.legend(prop=font)
    ax2.grid(True)

    plt.tight_layout()
    filename = OUTPUT_DIR / "Charge_Rho_Comparison.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ All computations and plots completed.")
    print(f"✅ Saved: Numerical_SOR.png, Charge_Movement_from_Potential.png, Charge_Rho_Comparison.png")


if __name__ == "__main__":
    main()
