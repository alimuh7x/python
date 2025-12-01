#!/home/alimuh7x/myenv/bin/python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

import numpy as np
import matplotlib.pyplot as plt
from Plotter import Plotter



def run_basic_simulation():
    # Parameters
    W = 1
    kappa = 0.5
    L = 20
    Nx = 500
    x = np.linspace(-L / 2, L / 2, Nx)

    # Diffuse interface
    phi = 0.5 * (1 + np.tanh(x))
    dphidx = np.gradient(phi, x)
    f_bulk = W * (phi ** 2) * ((1 - phi) ** 2)
    f_grad = 0.5 * kappa * (dphidx ** 2)

    phi_lower = 0.1
    phi_upper = 0.9
    i1 = np.argmin(np.abs(phi - phi_lower))
    i2 = np.argmin(np.abs(phi - phi_upper))
    xi = np.abs(x[i2] - x[i1])
    print(f'Interface thickness ξ = {xi:.4f}')

    F_total = np.trapezoid(f_bulk + f_grad, x)
    print(f'Total energy F = {F_total:.6f}')

    plotter = Plotter()
    plotter.plot1D(x, phi, xlabel='x', ylabel='phi', filename='Emperical_phi.png')
    plotter.plot1D(x, f_bulk, xlabel='x', ylabel='potential', filename='Emperical_potential.png')
    plotter.plot1D(x, f_grad, xlabel='x', ylabel='grad', filename='Emperical_grad.png')
    print('Plots created and saved as Emperical.png')

    eta = 4
    sigma = 1
    phi_phys = 0.5 * (1 + np.tanh(3 * x / eta))
    dphidx_phys = np.gradient(phi_phys, x)
    f_bulk_phys = 18 * sigma / eta * (phi_phys ** 2) * ((1 - phi_phys) ** 2)
    f_grad_phys = 0.5 * sigma * eta * (dphidx_phys ** 2)

    F_total_phys = np.trapezoid(f_bulk_phys + f_grad_phys, x)
    F_bulk = np.trapezoid(f_bulk_phys, x)
    F_grad = np.trapezoid(f_grad_phys, x)
    print(f'Total energy F = {F_total_phys:.6f}')
    print(f'Potential energy F = {F_bulk:.6f}')
    print(f'Gradient energy F = {F_grad:.6f}')

    return {
        'x': x,
        'phi': phi,
        'f_bulk': f_bulk,
        'f_grad': f_grad,
        'xi': xi,
        'F_total': F_total,
        'phi_phys': phi_phys,
        'f_bulk_phys': f_bulk_phys,
        'f_grad_phys': f_grad_phys,
        'F_total_phys': F_total_phys,
        'F_bulk': F_bulk,
        'F_grad': F_grad,
    }


if __name__ == '__main__':
    run_basic_simulation()
