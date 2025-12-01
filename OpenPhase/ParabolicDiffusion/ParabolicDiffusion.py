#!/home/alimuh7x/myenv/bin/python3
import numpy as np
from scipy.ndimage import laplace
from src.Plotter import Plotter

# -------------------------------------------------------
# Diffusion and timestep estimator
# -------------------------------------------------------
# Set physical parameters for diffusion and estimate stable timestep
D = 1e-18           # Diffusion coefficient (m^2/s)
dx = 0.5e-9         # Spatial grid size (m)
M = 5e-18           # Mobility (initial guess)
dt = 0.01           # Time step (s)
c_increment = 1e-6  # Concentration increment (for stability check)

# Estimate maximum rate of concentration change and recommended time step
c_dot_est = D / dx**2
dt_recommended = dx**2 / (10 * D)

# Print stability criteria and parameter summary
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
# Set up spatial grid and simulation parameters
Nx = 100            # Number of grid points
dx = 0.5e-9         # Grid spacing (m)
x = np.arange(Nx) * dx   # Spatial coordinates
i = np.arange(Nx)        # Index array


dt = 0.0001         # Time step for simulation (s)
nsteps = 10000      # Number of time steps

# Phase-field parameters
w = 8 * dx          # Interface width
A = 4e8             # Free energy parameter
L_phi = 1e-15       # Phase-field mobility
sigma = 0.5         # Surface tension coefficient

R = 8.3145          # Gas constant (J/mol/K)
D_alpha = 5e-16     # Diffusion coefficient in alpha phase
D_beta = 5e-16      # Diffusion coefficient in beta phase
Vm = 7.4e-6         # Molar volume (m^3/mol)

# -------------------------------------------------------
# Initial phase-field
# -------------------------------------------------------
# Initialize phase-field profile and concentrations
ProfilePosition = x - np.mean(x)    # Centered position array
# Initialize phase-field profile (tanh interface)
phi = 0.5 * (1 - np.tanh(3 * ProfilePosition / w))

phi_alpha = phi.copy()              # Fraction of alpha phase
phi_beta = 1 - phi                  # Fraction of beta phase

C_alpha = 1.0                      # Concentration in alpha phase
C_beta = 0.0                       # Concentration in beta phase

Ceq_alpha = 1.0                    # Equilibrium concentration in alpha
Ceq_beta = 0.2                     # Equilibrium concentration in beta

# Initial concentration profile
c = phi_alpha * C_alpha + phi_beta * C_beta
c_initial = c.copy()               # Store initial concentration

# Equilibrium concentration profile
C_eq = phi_alpha * Ceq_alpha + phi_beta * Ceq_beta
# Mobility profile (depends on phase fractions)
M = (D_alpha * phi_alpha + D_beta * phi_beta) / (R * 300)

# -------------------------------------------------------
# Time evolution
# -------------------------------------------------------
# Main simulation loop: evolve concentration and phase-field
# Store time, driving force, and energy for analysis

timeN = []             # Time array for plotting
DrivingForceN = []     # Driving force history
EnergyN = []           # Free energy history

for step in range(1, nsteps + 1):
    # Chemical potential (local free energy derivative)
    mu = A * Vm * (c - Ceq_alpha) * phi_alpha + A * Vm * (c - Ceq_beta) * phi_beta

    # Laplacian of chemical potential (for diffusion)
    mu_xx = laplace(mu, mode="reflect") / dx**2
    # Update mobility profile
    M = (D_alpha * phi_alpha + D_beta * phi_beta) / (R * 300)

    # Update concentration using diffusion equation
    dc = M * mu_xx
    c = c + dt * dc

    # Free energy density for each phase
    f_alpha = 0.5 * A * (c - Ceq_alpha)**2
    f_beta = 0.5 * A * (c - Ceq_beta)**2
    f_local = phi_alpha * f_alpha + phi_beta * f_beta

    # Total free energy (integrated over space)
    Energy = np.trapezoid(f_local, x)
    EnergyN.append(abs(Energy))

    # Driving force for phase transformation
    Delta_f = (f_beta - f_alpha) * phi_alpha * phi_beta
    Delta_f_avg = np.mean(Delta_f) * 500   # Scaled average driving force

    timeN.append(step * dt)
    DrivingForceN.append(abs(Delta_f_avg))

    # Laplacian of phase-field (for interface evolution)
    phi_xx = laplace(phi, mode="reflect") / dx**2

    # Double-well potential derivative (drives phase separation)
    dW_dphi = 72 * 2 * phi * (1 - phi) * (1 - 2 * phi) / w**2

    # Phase-field evolution equation
    phi_dot = L_phi * (sigma * (phi_xx - dW_dphi) +
                       (6 / w) * phi_alpha * phi_beta * Delta_f_avg)

    # Update phase-field, ensuring values stay in [0, 1]
    phi = np.clip(phi + dt * phi_dot, 0, 1)

    # Update phase fractions and equilibrium concentration
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
# Plot results: driving force, composition, and energy evolution
plot = Plotter()



plot.plot1D(timeN, DrivingForceN,
    xlabel="time (s)",
    ylabel="Driving Force",
    filename="DrivingForce.png",
)


Data = [x, c, timeN, EnergyN]
Labels = ["x (m)", "c", "time (s)", "Energy"]
plot.plot1x2(Data, Labels, filename="Composition_Energy.png")


