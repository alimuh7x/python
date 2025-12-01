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
    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=30)

    N = 100  # number of points
    x = np.linspace(0, 10, N)
    dx = x[1] - x[0]
    f = np.sin(np.pi * x / 10)  # initial field

    k = 1  # spring constant
    M = 1  # mobility
    V = 0.5 * (x - 5)**4  # external potential
    dt = 0.001  # time step
    steps = 1000
    plot_interval = 200  # plot every 200 steps

    # Plot initial field
    fig, ax = plt.subplots(figsize=(10, 6))
    num_plots = steps // plot_interval + 1
    colors = plt.cm.jet(np.linspace(0, 1, num_plots))

    ax.plot(x, f, color=colors[0], linewidth=2, label='Initial f(x)')
    plot_count = 1

    for step in range(1, steps + 1):
        f_new = f.copy()
        for i in range(1, N - 1):
            lap = (f[i + 1] - 2 * f[i] + f[i - 1]) / dx**2
            f_new[i] = f[i] + dt * M * (k * lap - 2 * V[i] * f[i])
        f = f_new

        if step % plot_interval == 0:
            ax.plot(x, f, color=colors[plot_count], linewidth=1.5)
            plot_count += 1

    # Plot normalized potential
    ax.plot(x, V / np.max(V), 'k--', linewidth=2, label='Normalized V(x)')

    ax.set_xlabel('x', fontproperties=font)
    ax.set_ylabel('f(x)', fontproperties=font)
    ax.legend(prop=font, loc='best')
    ax.set_xlim([0, 10])
    ax.set_ylim([-0.2, 1.2])
    ax.tick_params(labelsize=30, width=1.5, length=6)

    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontproperties(font)

    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    filename = OUTPUT_DIR / "spring_chain_snapshots.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Saved: spring_chain_snapshots.png")


if __name__ == "__main__":
    main()
