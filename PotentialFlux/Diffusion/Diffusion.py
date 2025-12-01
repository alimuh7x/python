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
    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=14)

    # Parameters
    Nx = 256
    Lx = 1.0
    dx = Lx / Nx
    x = np.linspace(0, Lx - dx, Nx)
    D = 1e-4
    dt = 3e-2
    Nt = 5000
    plot_interval = 100

    # Initial condition (periodic sine)
    rho = np.sin(2 * np.pi * x)

    # FFT wavenumbers
    k = (2 * np.pi / Lx) * np.concatenate([np.arange(0, Nx // 2), np.arange(-Nx // 2, 0)])
    k2 = k**2

    rho_snapshots = []
    lap_snapshots = []
    time_labels = []

    for t in range(1, Nt + 1):
        # Compute Laplacian ∂²ρ/∂x²
        rho_hat = np.fft.fft(rho)
        lap_rho = np.fft.ifft(-k2 * rho_hat).real

        # Pure diffusion: ρ_t = D ∂²ρ/∂x²
        rho = rho + dt * D * lap_rho

        # Store and plot
        if t % plot_interval == 0 or t == 1:
            rho_snapshots.append(rho.copy())
            lap_snapshots.append(lap_rho.copy())
            time_labels.append(t * dt)

            diffCFL = D * dt / dx**2
            print(f'Step {t}, Time {t * dt:.3f}, DiffCFL = {diffCFL:.3f}')
            print('----------------------------------------------------------------')

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
    cmap = plt.cm.jet(np.linspace(0, 1, len(rho_snapshots)))

    # Plot ρ(x,t)
    for i, rho_data in enumerate(rho_snapshots):
        ax1.plot(x, rho_data, color=cmap[i], linewidth=1.2)
    ax1.set_xlabel('x', fontproperties=font)
    ax1.set_ylabel('ρ(x)', fontproperties=font)
    ax1.set_title('Diffusion of charge density ρ(x,t)', fontproperties=font)
    ax1.grid(True)

    # Plot ∂²ρ/∂x²
    for i, lap_data in enumerate(lap_snapshots):
        ax2.plot(x, lap_data, color=cmap[i], linewidth=1.2)
    ax2.set_xlabel('x', fontproperties=font)
    ax2.set_ylabel('∇²ρ(x)', fontproperties=font)
    ax2.set_title('Laplacian of charge density ∂²ρ/∂x²', fontproperties=font)
    ax2.grid(True)

    plt.tight_layout()
    filename = OUTPUT_DIR / "Diffusion_and_Laplacian.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    print(f'✅ Saved: Diffusion_and_Laplacian.png')


if __name__ == "__main__":
    main()
