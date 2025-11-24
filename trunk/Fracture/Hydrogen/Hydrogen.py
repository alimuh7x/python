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
    # Constants
    R = 8.314  # J/mol·K
    T = 300  # K
    delta_gb = 30e3  # J/mol
    chi = 0.41

    # Concentration range
    C = np.logspace(-8, -1, 600)

    # Langmuir–McLean isotherm
    theta = C / (C + np.exp(-delta_gb / (R * T)))

    # Degraded fracture/surface energy
    Gc_ratio = 1 - chi * theta

    # Plot
    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=12)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogx(C, Gc_ratio, 'k--', linewidth=2, label=r'$G_c(C)/G_c(0)$')
    ax.semilogx(C, theta, 'b-', linewidth=2, label=r'$\theta(C)$')
    ax.legend(loc='lower right', prop=font)
    ax.set_xlabel('Hydrogen concentration C (mole fraction)', fontproperties=font)
    ax.set_ylabel('Normalized value', fontproperties=font)
    ax.set_title('Hydrogen-induced degradation of fracture energy', fontproperties=font)
    ax.grid(True)
    ax.set_xlim([1e-8, 1e-1])
    ax.set_ylim([-0.02, 1.05])

    # Apply font to tick labels
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontproperties(font)

    # Border
    for spine in ax.spines.values():
        spine.set_linewidth(1.2)

    filename = OUTPUT_DIR / 'Hydrogen_FractureEnergy_vs_Concentration.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Saved: Hydrogen_FractureEnergy_vs_Concentration.png")


if __name__ == "__main__":
    main()
