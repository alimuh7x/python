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


def write_to_file(filename, x, y):
    """Write two-column data to text file"""
    data = np.column_stack((x, y))
    np.savetxt(OUTPUT_DIR / filename, data, fmt='%.6e', delimiter='\t')
    print(f"✅ Written: {filename}")


def main() -> None:
    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=14)

    Nx = 512
    dx = 1e-4
    Lx = Nx * dx  # adjust Lx to match dx
    x = np.linspace(0, Lx - dx, Nx)

    epsilon0 = 8.854e-12  # vacuum permittivity

    mu = 2e-10  # mobility
    D = 1e-6  # diffusion coefficient

    dt = 1e-4
    Nt = 10000  # total steps
    plot_interval = 100  # plot frequency
    Faraday = 96485.3329  # C/mol

    # Positive carrier densities (Fe2+ and Cl-)
    x0_Fe = 0.3 * Lx  # Fe2+ center
    x0_Cl = 0.7 * Lx  # Cl- center
    sigma = 0.05 * Lx  # width

    c_Fe = np.exp(-((x - x0_Fe)**2) / (2 * sigma**2))  # Fe2+ concentration (positive)
    c_Cl = np.exp(-((x - x0_Cl)**2) / (2 * sigma**2))  # Cl- concentration (positive)

    z_Fe = 2  # charge number for Fe2+
    z_Cl = -2  # charge number for Cl-

    # FFT wavenumbers
    k = (2 * np.pi / Lx) * np.concatenate([np.arange(0, Nx // 2), np.arange(-Nx // 2, 0)])
    k2 = k**2
    k2[0] = 1

    # Storage
    rho_snapshots = []
    phi_snapshots = []
    time_labels = []
    convergence = np.zeros(Nt)
    energy = np.zeros(Nt)

    dt_cfl = dx**2 / (2 * D)
    myprint("CFL : ", dt_cfl, " > then dt : ", dt)

    # Plot setup
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # TIME LOOP
    for t in range(1, Nt + 1):
        # Compute total charge density
        rho = Faraday * (z_Fe * c_Fe + z_Cl * c_Cl)
        rho = rho - np.mean(rho)  # enforce neutrality

        rho[0] = rho[-2]
        rho[-1] = rho[1]

        # Solve Poisson: φ_xx = -ρ/ε0
        rho_hat = np.fft.fft(rho)
        phi_hat = rho_hat / (epsilon0 * k2 * 1e7)
        phi_hat[0] = 0
        phi = np.fft.ifft(phi_hat).real

        # Electric field: E = -φ_x
        E_hat = 1j * k * phi_hat
        E = -np.fft.ifft(E_hat).real

        # Drift + diffusion for each species
        grad_Fe = np.fft.ifft(1j * k * np.fft.fft(c_Fe)).real
        grad_Cl = np.fft.ifft(1j * k * np.fft.fft(c_Cl)).real

        J_Fe = -D * grad_Fe + z_Fe * mu * c_Fe * E
        J_Cl = -D * grad_Cl + z_Cl * mu * c_Cl * E

        # Continuity: c_t = -dJ/dx
        c_Fe_dot = -np.fft.ifft(1j * k * np.fft.fft(J_Fe)).real
        c_Cl_dot = -np.fft.ifft(1j * k * np.fft.fft(J_Cl)).real

        # Update concentrations
        c_Fe = c_Fe + dt * c_Fe_dot
        c_Cl = c_Cl + dt * c_Cl_dot

        # Keep densities positive
        c_Fe = np.maximum(c_Fe, 0)
        c_Cl = np.maximum(c_Cl, 0)

        # Periodic boundary wrapping (ghost cells)
        c_Fe[0] = c_Fe[-2]
        c_Fe[-1] = c_Fe[1]
        c_Cl[0] = c_Cl[-2]
        c_Cl[-1] = c_Cl[1]

        # Diagnostics
        convergence[t - 1] = np.sqrt(np.sum(rho**2) / Nx)
        energy[t - 1] = 0.5 * epsilon0 * np.sum(E**2) * dx

        if t % plot_interval == 0:
            print(f"Step {t}:  <rho>={np.mean(rho):.3e}  Energy={energy[t - 1]:.3e}")

            J_diff = -D * grad_Fe
            J_mig = z_Fe * mu * c_Fe * E

            R = np.abs(J_mig) / np.abs(J_diff + 1e-20)
            maxR = np.max(R)
            myprint("Max |J_mig|/|J_diff| = ", maxR)
            print("------------------------------------------------------------")

            rho_snapshots.append(rho.copy())
            phi_snapshots.append(phi.copy())

            # Update plot
            ax1.clear()
            ax2.clear()

            cmap = plt.cm.jet(np.linspace(0, 1, len(rho_snapshots)))

            for i, rho_data in enumerate(rho_snapshots):
                ax1.plot(x, rho_data, color=cmap[i], linewidth=1.3)
            ax1.set_xlabel('x', fontproperties=font)
            ax1.set_ylabel('ρ(x)', fontproperties=font)
            ax1.grid(True)
            ax1.tick_params(labelsize=14, width=2)

            for i, phi_data in enumerate(phi_snapshots):
                ax2.plot(x, phi_data, color=cmap[i], linewidth=1.3)
            ax2.set_xlabel('x', fontproperties=font)
            ax2.set_ylabel('φ(x)', fontproperties=font)
            ax2.grid(True)
            ax2.tick_params(labelsize=14, width=2)

            plt.tight_layout()
            plt.savefig(OUTPUT_DIR / 'Charge_Evolution.png', dpi=150, bbox_inches='tight')

        # Stop if steady
        if convergence[t - 1] < 1e-10:
            print(f'Equilibrium reached at step {t} (t={t * dt:.3g} s)')
            break

    plt.close()

    write_to_file('Density_M_High.txt', x, rho)
    print('✓ Simulation complete. Final plots saved.')
    print(f"✅ Saved: Charge_Evolution.png, Density_M_High.txt")


if __name__ == "__main__":
    main()
