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

    print("✅ Code Runner is working")

    x = np.linspace(0, 10, 1000)
    V = 0.5 * (x - 5)**4
    f = np.sin(2 * np.pi * x / 10)

    dt = 0.005
    nSteps = 2000
    nPlots = 5
    plot_every = nSteps // nPlots

    # Plot V * f
    fig, ax = plt.subplots(figsize=(8, 5))
    m = -0.001 * V * f
    ax.plot(x, m, 'r', linewidth=1.5, label='-V * f')
    ax.plot(x, V / np.max(V), 'k--', linewidth=2, label='Normalized V(x)')
    ax.set_xlabel('x', fontproperties=font)
    ax.set_ylabel('- V * f', fontproperties=font)
    ax.tick_params(labelsize=14, width=1.5, length=6)
    ax.legend(prop=font)

    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontproperties(font)

    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    filename = OUTPUT_DIR / "V_f.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ Plotting f(x) under parabolic potential")

    # Evolution plot
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = plt.cm.jet(np.linspace(0, 1, nPlots))

    ax.plot(x, f, 'k', linewidth=1.5, label='Initial')
    plot_count = 0

    for step in range(1, nSteps + 1):
        f = f - dt * V * f

        if step % plot_every == 0:
            ax.plot(x, f, color=colors[plot_count], linewidth=1.5)
            plot_count += 1

    ax.set_title('Evolution of f(x) under parabolic potential', fontproperties=font)
    ax.set_xlabel('x', fontproperties=font)
    ax.set_ylabel('f(x)', fontproperties=font)
    ax.set_xlim([0, 10])
    ax.set_ylim([-1.2, 1.2])
    ax.tick_params(labelsize=14, width=1.5, length=6)

    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontproperties(font)

    for spine in ax.spines.values():
        spine.set_linewidth(1.5)

    filename = OUTPUT_DIR / "f_evolution_snapshots.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()

    print("✅ Finished")
    print(f"✅ Saved: V_f.png, f_evolution_snapshots.png")


if __name__ == "__main__":
    main()
