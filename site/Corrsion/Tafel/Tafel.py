from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np


OUTPUT_DIR = Path(__file__).parent


def _save_figure(fig: Figure, filename: str) -> None:
    path = OUTPUT_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def main() -> None:
    F = 96485
    R = 8.314
    T = 298
    n = 1
    i0 = 1.0
    E_eq = 0.0

    E = np.linspace(E_eq - 0.1, E_eq + 0.1, 400)
    alpha_a = 0.5
    alpha_c = 0.5

    i_a = i0 * np.exp((alpha_a * n * F * (E - E_eq)) / (R * T))
    i_c = -i0 * np.exp((-alpha_c * n * F * (E - E_eq)) / (R * T))
    i_net = i_a + i_c

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.semilogy(E, np.abs(i_net), color="k", linewidth=2, label="Total current")
    ax.semilogy(E, np.abs(i_a), "--r", linewidth=1.5, label="Anodic")
    ax.semilogy(E, np.abs(i_c), "--b", linewidth=1.5, label="Cathodic")
    ax.set_xlabel("Potential E (V vs SHE)")
    ax.set_ylabel("log_{10}|Current density| (mA/cm^2)")
    ax.set_title("Theoretical Tafel Plot for Platinum Electrode")
    ax.grid(True, which="both")
    ax.legend()
    _save_figure(fig, "Tafel_plot.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(E, np.abs(i_net), color="k", linewidth=2, label="Total current")
    ax.plot(E, np.abs(i_a), "--r", linewidth=1.5, label="Anodic")
    ax.plot(E, np.abs(i_c), "--b", linewidth=1.5, label="Cathodic")
    ax.plot(E, np.zeros_like(E), "k--", linewidth=1, label="Zero line")
    ax.set_xlabel("Potential E (V vs SHE)")
    ax.set_ylabel("|Current density| (mA/cm^2)")
    ax.set_title("Current Density vs Potential for Platinum Electrode")
    ax.grid(True)
    ax.legend(loc="lower right")
    _save_figure(fig, "Potential_plot.png")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(E, i_net, color="k", linewidth=2, label="Total current")
    ax.plot(E, i_a, "--r", linewidth=1.5, label="Anodic")
    ax.plot(E, i_c, "--b", linewidth=1.5, label="Cathodic")
    ax.plot(E, np.zeros_like(E), "k--", linewidth=1, label="Zero line")
    ax.set_xlabel("Potential E (V vs SHE)")
    ax.set_ylabel("Current density (mA/cm^2)")
    ax.set_title("Current Density vs Potential for Platinum Electrode")
    ax.grid(True)
    ax.legend(loc="lower right")
    _save_figure(fig, "2Potential_plot.png")

    alpha_values = [0.3, 0.5, 0.7]
    fig, ax = plt.subplots(figsize=(7, 5))
    for alpha in alpha_values:
        alpha_a = alpha
        alpha_c = 1 - alpha
        i_a = i0 * np.exp((alpha_a * n * F * (E - E_eq)) / (R * T))
        i_c = -i0 * np.exp((-alpha_c * n * F * (E - E_eq)) / (R * T))
        i_net = i_a + i_c
        ax.plot(E, i_net, linewidth=2, label=f"alpha: {alpha:.1f}")
    ax.plot(E, np.zeros_like(E), "k--", linewidth=1)
    ax.set_xlabel("Potential E (V vs SHE)")
    ax.set_ylabel("Current density (mA/cm^2)")
    ax.set_title("Effect of alpha on Tafel Plot")
    ax.grid(True)
    ax.legend(loc="lower right", frameon=False)
    _save_figure(fig, "Tafel_alpha_plot.png")

    print("✅ Saved: Tafel_plot.png, Potential_plot.png, 2Potential_plot.png, Tafel_alpha_plot.png")


if __name__ == "__main__":
    main()
