#!/home/alimuh7x/myenv/bin/python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

# Add src/ folder to Python's module search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(CURRENT_DIR, "..", "..", "src")
sys.path.append(os.path.realpath(SRC_PATH))

OUTPUT_DIR = Path(__file__).parent


def save_field_plot(x, y, field, title, filename, cmap='jet', X=None, Y=None, U=None, V=None, skip=15, scale=0.03):
    """Save 2D field plot with optional arrows"""
    fig, ax = plt.subplots(figsize=(8, 7))

    im = ax.imshow(
        field,
        extent=[x.min(), x.max(), y.min(), y.max()],
        origin='lower',
        aspect='auto',
        cmap=cmap
    )

    if X is not None and Y is not None and U is not None and V is not None:
        # Downsample and normalize arrows
        Xs = X[::skip, ::skip]
        Ys = Y[::skip, ::skip]
        Us = U[::skip, ::skip]
        Vs = V[::skip, ::skip]

        mag = np.sqrt(Us**2 + Vs**2)
        mag[mag == 0] = 1
        Us = Us / mag
        Vs = Vs / mag

        ax.quiver(Xs, Ys, scale * Us, scale * Vs, color='black', linewidth=1.5, scale=1, scale_units='xy')

    ax.set_xlabel('x', fontsize=14)
    ax.set_ylabel('y', fontsize=14)
    ax.set_title(title, fontsize=14)
    plt.colorbar(im, ax=ax)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: {filename}")


def main() -> None:
    # 2D Poisson equation using FFT: ∇²φ = -ρ/ε₀
    # Parameters
    mu = 5e-10
    Nx, Ny = 512, 512
    Lx, Ly = 1.0, 1.0

    dx = Lx / Nx
    dy = Ly / Ny
    epsilon0 = 8.854e-12

    x = np.linspace(0, Lx - dx, Nx)
    y = np.linspace(0, Ly - dy, Ny)
    X, Y = np.meshgrid(x, y)

    # Charge density (initial)
    rho = np.sin(2 * np.pi * X) * np.cos(2 * np.pi * Y)

    # Solve Poisson equation in Fourier space
    rho_hat = np.fft.fft2(rho)

    kx = (2 * np.pi / Lx) * np.concatenate([np.arange(0, Nx // 2), np.arange(-Nx // 2, 0)])
    ky = (2 * np.pi / Ly) * np.concatenate([np.arange(0, Ny // 2), np.arange(-Ny // 2, 0)])
    KX, KY = np.meshgrid(kx, ky)

    k2 = KX**2 + KY**2
    k2[0, 0] = 1  # avoid division by zero

    phi_hat = rho_hat / (epsilon0 * k2)
    phi_hat[0, 0] = 0  # zero-mean potential
    phi = np.fft.ifft2(phi_hat).real

    # Electric field
    phi_y, phi_x = np.gradient(phi, dy, dx)
    Ex = -phi_x
    Ey = -phi_y
    E_mag = np.sqrt(Ex**2 + Ey**2)

    # Separate positive and negative charge densities
    rho_pos = np.maximum(rho, 0)  # positive charge (e.g., Fe2+)
    rho_neg = np.minimum(rho, 0)  # negative charge (e.g., Cl-)

    z_pos = +1
    z_neg = -1
    mu_pos = mu
    mu_neg = mu

    # Fluxes for each charge type
    Jx_pos = mu_pos * rho_pos * Ex * z_pos
    Jy_pos = mu_pos * rho_pos * Ey * z_pos

    Jx_neg = mu_neg * rho_neg * Ex * z_neg
    Jy_neg = mu_neg * rho_neg * Ey * z_neg

    # Total flux
    Jx_total = Jx_pos + Jx_neg
    Jy_total = Jy_pos + Jy_neg

    # Rate of charge change (divergence of flux)
    divJy, divJx = np.gradient(Jy_total, dy, dx)
    rho_dot = -(divJx + divJy)
    rho_dot = rho_dot - np.mean(rho_dot)

    # Update charge density
    dt = 0.01
    new_rho = rho + dt * rho_dot

    # Visualization
    skip = 15

    # Initial charge density
    save_field_plot(x, y, rho, "Initial ρ", "rho_initial.png")

    # Positive charge density
    save_field_plot(x, y, rho_pos, "Positive charge density ρ⁺", "rho_positive.png")

    # Negative charge density
    save_field_plot(x, y, rho_neg, "Negative charge density ρ⁻", "rho_negative.png")

    # Electric potential with field arrows
    save_field_plot(x, y, phi, "Electric potential φ with field arrows", "potential_phi_with_E.png",
                    X=X, Y=Y, U=Ex, V=Ey, skip=skip, scale=0.03)

    # Electric field magnitude with arrows
    save_field_plot(x, y, E_mag, "Electric field magnitude |E|", "E_magnitude_with_arrows.png",
                    X=X, Y=Y, U=Ex, V=Ey, skip=skip, scale=0.03)

    # Updated charge density
    save_field_plot(x, y, new_rho, "Updated charge density", "rho_updated.png")

    print("✅ All 2D plots completed")


if __name__ == "__main__":
    main()
