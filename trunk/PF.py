import numpy as np
import matplotlib.pyplot as plt

# Parameters
nx = 200           # grid points
dx = 1.0 / nx     # grid spacing
dt = 1e-4         # time step
n_steps = 10000   # number of time steps
W = 1.0           # double-well strength
kappa = 1e-2      # gradient energy coefficient
M = 1.0           # mobility

# Initialize field: sharp interface between 0 and 1
x = np.linspace(0, 1, nx)
phi =  (1 + np.tanh((x - 0.5) / (np.sqrt(2 * kappa / W))))

# Laplacian with Dirichlet BCs
def laplacian(f):
    lap = np.zeros_like(f)
    lap[1:-1] = (f[2:] - 2 * f[1:-1] + f[:-2]) / dx**2
    return lap

# Store snapshots
snapshots = []
snapshot_steps = []

for step in range(n_steps + 1):
    dF_dphi = W * 2 * phi * (1 - phi) * (1 - 2 * phi) - kappa * laplacian(phi)
    phi[1:-1] -= M * dF_dphi[1:-1] * dt

    # Dirichlet BCs
    phi[0] = 0.0
    phi[-1] = 1.0

    if step % 1000 == 0:
        snapshots.append(phi.copy())
        snapshot_steps.append(step)

# Plot all snapshots
plt.figure(figsize=(8, 5))
for snap, s in zip(snapshots, snapshot_steps):
    plt.plot(x, snap, label=f"step {s}")
plt.xlabel("x")
plt.ylabel("phi")
plt.title("Phase-field evolution with Dirichlet BCs")
plt.legend()
plt.show()


