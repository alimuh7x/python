from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.plot_utils import save_four_subplot


OUTPUT_DIR = Path(__file__).parent


def main() -> None:
    K1 = 1.0e-4
    K2 = 1.0e-14
    Ctot = 5.55e4
    kb1 = 2.78e3
    kb2 = 2.78e3

    xM = 0.1
    xMOH = 0.0
    xH = 1e-12
    xOH = K2 / xH
    dt = 1e-5
    Nt = int(2e5)

    time = np.zeros(Nt)
    xM_arr = np.zeros(Nt)
    xMOH_arr = np.zeros(Nt)
    xH_arr = np.zeros(Nt)
    xOH_arr = np.zeros(Nt)
    pH_arr = np.zeros(Nt)

    RM_arr = np.zeros(Nt)
    RMOH_arr = np.zeros(Nt)
    RH_arr = np.zeros(Nt)
    ROH_arr = np.zeros(Nt)

    for n in range(Nt):
        RM = kb1 * (-K1 * xM + xH * xMOH)
        RMOH = kb1 * (K1 * xM - xH * xMOH)
        RH = kb1 * (K1 * xM - xH * xMOH) + kb2 * (K2 - xH * xOH)
        ROH = kb2 * (K2 - xH * xOH)

        RM_arr[n] = RM
        RMOH_arr[n] = RMOH
        RH_arr[n] = RH
        ROH_arr[n] = ROH

        xM += RM * dt
        xMOH += RMOH * dt
        xH += RH * dt
        xOH += ROH * dt

        xM = max(xM, 0.0)
        xMOH = max(xMOH, 0.0)
        xH = max(xH, 1e-14)
        xOH = max(xOH, 1e-14)

        time[n] = (n + 1) * dt
        xM_arr[n] = xM
        xMOH_arr[n] = xMOH
        xH_arr[n] = xH
        xOH_arr[n] = xOH
        pH_arr[n] = -np.log10(xH * Ctot / 1000)

        if (n + 1) % int(1e4) == 0:
            print(
                f"⏳ Time step: {n + 1}/{Nt}, "
                f"K1*xM={K1*xM:.2e}, xH*xMOH={xH*xMOH:.2e}, xH={xH:.2e}, xOH={xOH:.2e}"
            )

    rates = np.column_stack([time, RM_arr, RMOH_arr, RH_arr, ROH_arr])
    concentrations = np.column_stack([time, xM_arr, xMOH_arr, xH_arr, xOH_arr])

    save_four_subplot(
        rates,
        ["time", "R_M", "R_{MOH}", "R_H", "R_{OH}"],
        OUTPUT_DIR / "ReactionTime_Evolution_Rates.png",
    )
    save_four_subplot(
        concentrations,
        ["time", "c_M", "c_{MOH}", "c_H", "c_{OH}"],
        OUTPUT_DIR / "ReactionTime_Evolution_Concentrations.png",
    )
    print("✅ Saved: ReactionTime_Evolution_Rates.png and ReactionTime_Evolution_Concentrations.png")


if __name__ == "__main__":
    main()
