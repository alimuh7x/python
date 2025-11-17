from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.plot_utils import save_dual_plot, save_single_plot



OUTPUT_DIR = Path(__file__).parent


def main() -> None:
    K1 = 1.625e-4
    K2 = 1.0e-8
    C_tot = 5.55e4

    kb1 = 2.78e7 * 1e-5
    kb2 = 2.78e8 * 1e-5

    xM = np.linspace(0, 0.2, 200)
    xSolid = np.ones_like(xM)
    xH = np.full_like(xM, 1e-7)
    xOH = K2 / xH
    xMOH = np.full_like(xM, 1e-9)

    R_M = kb1 * (-K1 * xM * xSolid + xH * xMOH)
    R_MOH = kb1 * (K1 * xM * xSolid - xH * xMOH)
    R_H = kb1 * (K1 * xM * xSolid - xH * xMOH) + kb2 * (K2 - xH * xOH)
    R_OH = kb2 * (K2 - xH * xOH)

    save_dual_plot(
        xM,
        R_M,
        R_MOH,
        x_label="Fe mole fraction, x_M",
        y_label="Mole-fraction reaction rate",
        y1_label="R_M",
        y2_label="R_{MOH}",
        filename=OUTPUT_DIR / "Metal_Oxide.png",
        title="Fe & FeOH reaction rates",
    )
    save_dual_plot(
        xM,
        R_H,
        R_OH,
        x_label="Fe mole fraction, x_M",
        y_label="Mole-fraction reaction rate",
        y1_label="R_H",
        y2_label="R_{OH}",
        filename=OUTPUT_DIR / "Hydrogen_Oxide.png",
        title="H / OH production rates",
    )

    conc_H = xH * C_tot / 1000
    PH = -np.log10(conc_H)
    save_single_plot(
        xM,
        PH,
        x_label="Fe mole fraction, x_M",
        y_label="pH",
        filename=OUTPUT_DIR / "PH_vs_xM.png",
        title="pH vs Fe mole fraction",
    )
    print("✅ Saved: Metal_Oxide.png, Hydrogen_Oxide.png, PH_vs_xM.png")

    xH_range = np.linspace(0, 5e-3, 300)
    xH_range = np.clip(xH_range, 1e-12, None)
    conc_H = xH_range * C_tot / 1000
    pH = -np.log10(conc_H)

    save_single_plot(
        xH_range,
        pH,
        x_label="H^+ mole fraction, x_H",
        y_label="pH",
        filename=OUTPUT_DIR / "PH.png",
        title="pH vs H+ mole fraction (linear)",
    )
    save_single_plot(
        xH_range,
        pH,
        x_label="H^+ mole fraction, x_H",
        y_label="pH",
        filename=OUTPUT_DIR / "log_PH.png",
        title="pH vs H+ mole fraction (log scale)",
        logx=True,
    )
    print("✅ Saved: PH.png, log_PH.png")


if __name__ == "__main__":
    main()
