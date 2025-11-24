#!/home/alimuh7x/myenv/bin/python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

# Add src/ folder to Python's module search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(CURRENT_DIR, "..", "src")
sys.path.append(os.path.realpath(SRC_PATH))

from Plotter import Plotter

OUTPUT_DIR = Path(__file__).parent


def main() -> None:
    # Parameters
    T_initial = 100.0
    T_ambient = 25.0
    k = 0.05
    dt = 0.05
    t_end = 200.0

    # Time and temperature arrays
    t = np.arange(0, t_end + dt, dt)
    T = np.zeros_like(t)
    dT = np.zeros_like(t)
    T[0] = T_initial

    # Euler integration
    for i in range(len(t) - 1):
        # dTdt = -k * (T[i] - T_ambient)
        dTdt = -k * np.sin(T[i])
        dT[i + 1] = dTdt * dt
        T[i + 1] = T[i] + dTdt * dt

    # Remove first element to match length
    t = t[1:]
    T = T[1:]
    dT = dT[1:]

    # Plot using double y-axis
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=14)

    fig, ax1 = plt.subplots(figsize=(8, 6))

    # Plot T on left axis
    color = 'b'
    ax1.set_xlabel('Time (s)', fontproperties=font)
    ax1.set_ylabel('Temperature (°C)', color=color, fontproperties=font)
    ax1.plot(t, T, 'b-', linewidth=2, label='Temperature')
    ax1.tick_params(axis='y', labelcolor=color, which='major', direction='in', length=7, width=1.2)
    ax1.tick_params(which='minor', direction='in', length=4, width=0.8)
    ax1.minorticks_on()

    # Plot dT on right axis
    ax2 = ax1.twinx()
    color = 'r'
    ax2.set_ylabel('Temperature Increment (°C)', color=color, fontproperties=font)
    ax2.plot(t, dT, 'r--', linewidth=2, label='Increment')
    ax2.tick_params(axis='y', labelcolor=color, which='major', direction='in', length=7, width=1.2)
    ax2.tick_params(which='minor', direction='in', length=4, width=0.8)
    ax2.minorticks_on()

    # Apply font to tick labels
    for lbl in ax1.get_xticklabels() + ax1.get_yticklabels():
        lbl.set_fontproperties(font)
    for lbl in ax2.get_yticklabels():
        lbl.set_fontproperties(font)

    # Frame
    for spine in ax1.spines.values():
        spine.set_linewidth(1.5)

    fig.tight_layout()
    filename = OUTPUT_DIR / "cooling_curve.png"
    plt.savefig(filename, dpi=150)
    plt.close()

    print(f"✅ Saved: cooling_curve.png")


if __name__ == "__main__":
    main()
