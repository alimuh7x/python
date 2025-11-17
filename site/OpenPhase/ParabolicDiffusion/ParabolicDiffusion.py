#!/home/alimuh7x/myenv/bin/python3
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import laplace

# Add src/ folder to Python's module search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(CURRENT_DIR, "..", "..", "src")
sys.path.append(os.path.realpath(SRC_PATH))

from Plotter import Plotter

# -------------------------------------------------------
# Diffusion and timestep estimator
# -------------------------------------------------------
D = 1e-18
dx = 0.5e-9
M = 5e-18
dt = 0.01
c_increment = 1e-6

c_dot_est = D / dx**2
dt_recommended = dx**2 / (10 * D)

print("==========================================================")
print(" c_dot * dt < 0.1")
print(" D * dt < dx^2 / 6")
print("==========================================================")
print("Given parameters:")
print(f"D  = {D:.1e}")
print(f"dx = {dx:.1e}")
print("==========================================================")
print("Calculated:")
print(f"Recommended c_dot = {c_dot_est:.3f}")
print(f"Recommended dt    = {dt_recommended:.3f}")
print(f"c_dot * dt        = {c_dot_est * dt_recommended:.3f}")
print("==========================================================\n")

# -------------------------------------------------------
# Spatial discretization
# -------------------------------------------------------
Nx = 100
dx = 0.5e-9
x = np.arange(Nx) * dx
i = np.arange(Nx)

dt = 0.0001
nsteps = 10000

# Phase-field parameters
w = 8 * dx
A = 4e8
L_phi = 1e-15
sigma = 0.5

R = 8.3145
D_alpha = 5e-16
D_beta = 5e-16
Vm = 7.4e-6

# -------------------------------------------------------
# Initial phase-field
# -------------------------------------------------------
ProfilePosition = x - np.mean(x)
phi = 0.5 * (1 - np.tanh(3 * ProfilePosition / w))

phi_alpha = phi.copy()
phi_beta = 1 - phi

C_alpha = 1.0
C_beta = 0.0

Ceq_alpha = 1.0
Ceq_beta = 0.2

c = phi_alpha * C_alpha + phi_beta * C_beta
c_initial = c.copy()

C_eq = phi_alpha * Ceq_alpha + phi_beta * Ceq_beta
M = (D_alpha * phi_alpha + D_beta * phi_beta) / (R * 300)

# -------------------------------------------------------
# Time evolution
# -------------------------------------------------------
timeN = []
DrivingForceN = []
EnergyN = []

for step in range(1, nsteps + 1):
    # Chemical potential
    mu = A * Vm * (c - Ceq_alpha) * phi_alpha + A * Vm * (c - Ceq_beta) * phi_beta

    mu_xx = laplace(mu, mode="reflect") / dx**2
    # Update M
    M = (D_alpha * phi_alpha + D_beta * phi_beta) / (R * 300)

    # Update concentration
    dc = M * mu_xx
    c = c + dt * dc

    # Free energy
    f_alpha = 0.5 * A * (c - Ceq_alpha)**2
    f_beta = 0.5 * A * (c - Ceq_beta)**2
    f_local = phi_alpha * f_alpha + phi_beta * f_beta

    Energy = np.trapezoid(f_local, x)
    EnergyN.append(abs(Energy))

    # Driving force
    Delta_f = (f_beta - f_alpha) * phi_alpha * phi_beta
    Delta_f_avg = np.mean(Delta_f) * 500

    timeN.append(step * dt)
    DrivingForceN.append(abs(Delta_f_avg))

    phi_xx = laplace(phi, mode="reflect") / dx**2

    # Double-well derivative
    dW_dphi = 72 * 2 * phi * (1 - phi) * (1 - 2 * phi) / w**2

    # Phase-field evolution
    phi_dot = L_phi * (sigma * (phi_xx - dW_dphi) +
                       (6 / w) * phi_alpha * phi_beta * Delta_f_avg)

    phi = np.clip(phi + dt * phi_dot, 0, 1)

    # Update phase fractions + equilibrium
    phi_alpha = phi
    phi_beta = 1 - phi
    C_eq = phi_alpha * Ceq_alpha + phi_beta * Ceq_beta

    # Debug output every 500 steps
    if step % 500 == 0:
        total_C = np.trapezoid(c, x)
        total_C_initial = np.trapezoid(c_initial, x)
        Error = abs((total_C - total_C_initial) / total_C_initial) * 100

        print("==========================================================")
        print(f"Step {step}/{nsteps}")
        print(f"Max c_dot         : {np.max(dc)}")
        print(f"Max c_increment   : {np.max(dc) * dt}")
        print(f"C initial         : {total_C_initial}")
        print(f"C total           : {total_C}")
        print(f"Error (%)         : {Error}")
        print(f"phi_dot max       : {np.max(np.abs(phi_dot))}")
        print(f"Driving Force     : {Delta_f_avg}")
        print("==========================================================")

# -------------------------------------------------------
# Final plots (optional)
# -------------------------------------------------------
plot = Plotter()



plot.plot1D(timeN, DrivingForceN,
    xlabel="time (s)",
    ylabel="Driving Force",
    filename="DrivingForce.png",
)


Data = [x, c, timeN, EnergyN]
Labels = ["x (m)", "c", "time (s)", "Energy"]
plot.plot1x2(Data, Labels, filename="Composition_Energy.png")

