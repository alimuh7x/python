#!/home/alimuh7x/myenv/bin/python3
"""
Show slice data from VTK files
===============================
Simple visualization of z=64 slice from each VTK file showing
precipitate distribution.
"""

import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label

files = ['PhaseField_Initial.vts', 'PhaseField_0.6_percent.vts', 'PhaseField_1.0_precent.vts']
names = ['Initial', '0.6% Strain', '1.0% Strain']

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for idx, (f, name) in enumerate(zip(files, names)):
    mesh = pv.read(f'./{f}')

    # Get dimensions from mesh
    Nx, Ny, Nz = mesh.dimensions
    print(f'{name}: dimensions = {Nx} x {Ny} x {Nz}')

    # Read slice by slice at z=64
    phi = mesh['PhaseFraction_1']

    # Calculate the linear index for slice z=40
    slice_z = 40
    start_idx = slice_z * Nx * Ny
    end_idx = start_idx + Nx * Ny

    # Extract the slice data
    phi_slice = phi[start_idx:end_idx].reshape(Nx, Ny)
    binary = (phi_slice > 0.5).astype(int)
    labels_arr, N = label(binary)

    axes[idx].imshow(binary.T, origin='lower', cmap='gray', interpolation='nearest')
    axes[idx].set_title(f'{name}\nz=40 slice\n{N} precipitates', fontweight='bold')
    axes[idx].set_xlabel('X (voxels)')
    axes[idx].set_ylabel('Y (voxels)')

plt.tight_layout()
plt.savefig('slice_comparison.png', dpi=200)
print('Saved: slice_comparison.png')

# Print summary
print('\nSummary:')
for f, name in zip(files, names):
    mesh = pv.read(f'./{f}')
    Nx, Ny, Nz = mesh.dimensions
    phi = mesh['PhaseFraction_1']

    # Read slice at z=40
    slice_z = 40
    start_idx = slice_z * Nx * Ny
    end_idx = start_idx + Nx * Ny
    phi_slice = phi[start_idx:end_idx].reshape(Nx, Ny)

    binary = (phi_slice > 0.5).astype(int)
    labels_arr, N = label(binary)
    gamma_frac = np.mean(binary)
    print(f'{name}: {N} precipitates, {gamma_frac*100:.1f}% area fraction')
