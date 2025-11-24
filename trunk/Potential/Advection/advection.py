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

    # Grid setup
    N = 200
    x = np.linspace(0, 10, N)
    dx = x[1] - x[0]
    dt = 0.001
    steps = 1000

    # Parameters
    D = 0.1  # diffusion coefficient
    f = np.sin(np.pi * x / 10)**2  # initial field, non-negative
    f = f / np.trapz(f, x)  # normalize mass

    # Parabolic potential
    V = 0.5 * (x - 5)**2
    dVdx = np.gradient(V, dx)  # numerical gradient

    # Storage for plotting
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.jet(np.linspace(0, 1, 6))
    ax.plot(x, f, color=colors[0], linewidth=2, label='Initial')

    plot_interval = steps // 5
    plot_id = 1

    for step in range(1, steps + 1):
        # Compute gradients
        df_dx = np.gradient(f, dx)
        d2f_dx2 = np.gradient(df_dx, dx)

        diffusion = D * d2f_dx2  # diffusion: D ∂²f/∂x²
        adv = np.gradient(f * dVdx, dx)  # advection: ∂(f ∂V/∂x)/∂x

        Totalrate = diffusion + adv  # net rate of change

        # Update
        f = f + dt * Totalrate
        f = np.maximum(f, 0)  # keep non-negative
        f = f / np.trapz(f, x)  # conserve total mass

        # Plot at intervals
        if step % plot_interval == 0:
            ax.plot(x, f, color=colors[plot_id], linewidth=1.5)
            plot_id += 1

    # Plot potential
    ax.plot(x, V / np.max(V), 'k--', linewidth=2, label='Normalized V(x)')
    ax.legend(prop=font, loc='best')
    ax.set_xlabel('x', fontproperties=font)
    ax.set_ylabel('f(x)', fontproperties=font)
    ax.tick_params(labelsize=14, width=1.5, length=6)

    # Apply font to tick labels
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontproperties(font)

    # Frame
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    filename = OUTPUT_DIR / "diffusion_advection.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Saved: diffusion_advection.png")


if __name__ == "__main__":
    main()
