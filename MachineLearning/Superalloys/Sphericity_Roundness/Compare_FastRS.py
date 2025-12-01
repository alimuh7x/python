#!/home/alimuh7x/myenv/bin/python3
"""
Comparative Sphericity and Roundness Analysis
==============================================
This script compares two VTK files (PF_Initial.vts and PF_old.vts) using fast_rs
to analyze γ' precipitates. Results are shown both normalized and unnormalized.

- PF_Initial.vts: 256x256x256 grid (slice at z=128)
- PF_old.vts: 128x128x128 grid (slice at z=64)

Normalization allows comparison independent of precipitate count.
"""

import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label
from scipy.spatial import KDTree
from fast_rs import rs
import pandas as pd

# ================================================================
# CONFIGURATION
# ================================================================
dx = 30.0  # nm (grid spacing)

datasets = [
    {
        'name': 'PF_Initial',
        'file': './PF_Initial.vts',
        'grid_size': (256, 256, 256),
        'slice_index': 128,
        'color': 'steelblue'
    },
    {
        'name': 'PF_old',
        'file': './PF_old.vts',
        'grid_size': (128, 128, 128),
        'slice_index': 64,
        'color': 'coral'
    }
]

print("=" * 70)
print("COMPARATIVE SPHERICITY & ROUNDNESS ANALYSIS")
print("=" * 70)
print(f"Grid spacing (dx): {dx} nm")
print()

# ================================================================
# PROCESS BOTH DATASETS
# ================================================================
all_results = []

for ds in datasets:
    print("=" * 70)
    print(f"PROCESSING: {ds['name']}")
    print("=" * 70)

    # Load VTK file
    mesh = pv.read(ds['file'])
    phi = mesh["PhaseFraction_1"]
    Nx, Ny, Nz = ds['grid_size']
    phi = phi.reshape(Nx, Ny, Nz)
    print(f"Grid size: {Nx} x {Ny} x {Nz}")

    # Extract slice
    slice_idx = ds['slice_index']
    phi_slice = phi[:, :, slice_idx]
    print(f"Extracting slice at z={slice_idx}")
    print(f"Slice dimensions: {phi_slice.shape[0]} x {phi_slice.shape[1]}")
    print(f"Physical size: {Nx*dx:.1f} x {Ny*dx:.1f} nm²")

    # Create binary field
    binary = (phi_slice > 0.5).astype(int)
    print(f"γ' voxels: {np.sum(binary):,}")

    # Label precipitates
    labels, N = label(binary)
    print(f"Precipitates detected: {N}")

    # Calculate sphericity and roundness
    print("Calculating sphericity & roundness...")
    sphericity_vec = []
    roundness_vec = []
    valid_labels = []
    volumes_nm3 = []
    volumes_voxels = []
    equiv_diameters_nm = []
    aspect_ratios = []
    centroids_physical = []

    voxel_volume = dx ** 3

    for i in range(1, N + 1):
        coords = np.argwhere(labels == i)
        if coords.shape[0] < 10:
            continue

        # Extract bounding box
        mins = coords.min(axis=0)
        maxs = coords.max(axis=0)

        # Create small binary mask (2D)
        precipitate_mask = np.zeros((maxs[0] - mins[0] + 3,
                                      maxs[1] - mins[1] + 3), dtype=bool)
        local_coords = coords - mins + 1
        precipitate_mask[local_coords[:, 0], local_coords[:, 1]] = True

        try:
            roundness, sphericity, _ = rs.rs_calculate(precipitate_mask)

            if len(roundness) > 0 and len(sphericity) > 0:
                roundness_vec.append(roundness[0])
                sphericity_vec.append(sphericity[0])
                valid_labels.append(i)

                # Calculate features
                V_voxels = coords.shape[0]
                V_nm3 = V_voxels * voxel_volume
                volumes_voxels.append(V_voxels)
                volumes_nm3.append(V_nm3)

                D_nm = (6 * V_nm3 / np.pi) ** (1 / 3)
                equiv_diameters_nm.append(D_nm)

                Lx, Ly = (maxs - mins + 1) * dx
                AR = max(Lx, Ly) / min(Lx, Ly)
                aspect_ratios.append(AR)

                centroid = np.mean(coords, axis=0) * dx
                centroids_physical.append(centroid)
        except:
            continue

        if i % 50 == 0:
            print(f"  Processed {i}/{N}...")

    sphericity_vec = np.array(sphericity_vec)
    roundness_vec = np.array(roundness_vec)

    # Calculate spatial statistics
    if len(centroids_physical) > 1:
        centroids_physical = np.array(centroids_physical)
        tree = KDTree(centroids_physical)
        distances, _ = tree.query(centroids_physical, k=2)
        nearest_neighbor_nm = distances[:, 1]
    else:
        nearest_neighbor_nm = np.array([])

    # Store results
    gamma_p_fraction = np.mean(binary)

    results = {
        'name': ds['name'],
        'color': ds['color'],
        'grid_size': ds['grid_size'],
        'slice_area_nm2': (Nx * dx) * (Ny * dx),
        'total_detected': N,
        'analyzed': len(valid_labels),
        'area_fraction': gamma_p_fraction,
        'volumes_nm3': np.array(volumes_nm3),
        'volumes_voxels': np.array(volumes_voxels),
        'equiv_diameters_nm': np.array(equiv_diameters_nm),
        'aspect_ratios': np.array(aspect_ratios),
        'sphericity': sphericity_vec,
        'roundness': roundness_vec,
        'nearest_neighbor_nm': nearest_neighbor_nm,
    }

    all_results.append(results)

    print(f"Successfully analyzed: {len(valid_labels)} precipitates")
    print(f"Area fraction: {gamma_p_fraction:.3f}")
    print(f"Mean sphericity: {np.nanmean(sphericity_vec):.3f}")
    print(f"Mean roundness: {np.nanmean(roundness_vec):.3f}")
    print()

# ================================================================
# COMPARATIVE VISUALIZATION
# ================================================================
print("=" * 70)
print("GENERATING COMPARATIVE PLOTS")
print("=" * 70)

# Create figure with unnormalized and normalized comparisons
fig = plt.figure(figsize=(20, 12))
gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

features = [
    ('volumes_nm3', 'Volume (nm³)', 'Volume Distribution'),
    ('equiv_diameters_nm', 'Equivalent Diameter (nm)', 'Diameter Distribution'),
    ('aspect_ratios', 'Aspect Ratio', 'Aspect Ratio Distribution'),
    ('sphericity', 'Sphericity (Wadell)', 'Sphericity Distribution'),
    ('roundness', 'Roundness (Wadell)', 'Roundness Distribution'),
    ('nearest_neighbor_nm', 'Nearest Neighbor (nm)', 'NN Distribution'),
]

for idx, (feature, xlabel, title) in enumerate(features):
    row = idx // 2
    col = (idx % 2) * 2

    # Unnormalized plot
    ax_unnorm = fig.add_subplot(gs[row, col])
    ax_unnorm.set_title(f"{title} (Unnormalized)", fontweight='bold')
    ax_unnorm.set_xlabel(xlabel)
    ax_unnorm.set_ylabel("Count")
    ax_unnorm.grid(True, alpha=0.3)

    # Normalized plot
    ax_norm = fig.add_subplot(gs[row, col + 1])
    ax_norm.set_title(f"{title} (Normalized)", fontweight='bold')
    ax_norm.set_xlabel(xlabel)
    ax_norm.set_ylabel("Probability Density")
    ax_norm.grid(True, alpha=0.3)

    for res in all_results:
        data = res[feature]
        # Remove NaN values
        data = data[~np.isnan(data)]

        if len(data) > 0:
            # Unnormalized histogram
            ax_unnorm.hist(data, bins=25, alpha=0.6,
                          label=f"{res['name']} (n={len(data)})",
                          color=res['color'], edgecolor='black')

            # Normalized histogram (density)
            ax_norm.hist(data, bins=25, alpha=0.6, density=True,
                        label=f"{res['name']}",
                        color=res['color'], edgecolor='black')

    ax_unnorm.legend()
    ax_norm.legend()

plt.savefig('comparison_morphology.png', dpi=300, bbox_inches='tight')
print("Saved: comparison_morphology.png")
plt.close()

# ================================================================
# SCATTER PLOT: SPHERICITY VS ROUNDNESS
# ================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

for res in all_results:
    sph = res['sphericity']
    rnd = res['roundness']

    # Remove NaN
    valid = ~(np.isnan(sph) | np.isnan(rnd))
    sph = sph[valid]
    rnd = rnd[valid]

    if len(sph) > 0:
        # Unnormalized (point size = 50)
        ax1.scatter(sph, rnd, s=50, alpha=0.5,
                   label=f"{res['name']} (n={len(sph)})",
                   c=res['color'], edgecolors='black', linewidth=0.5)

        # Normalized (point size scales with fraction)
        total_analyzed = sum(len(r['sphericity'][~np.isnan(r['sphericity'])])
                            for r in all_results)
        point_size = 100 * len(sph) / total_analyzed
        ax2.scatter(sph, rnd, s=point_size, alpha=0.5,
                   label=f"{res['name']} (normalized)",
                   c=res['color'], edgecolors='black', linewidth=0.5)

ax1.set_xlabel('Sphericity (Wadell)', fontsize=12)
ax1.set_ylabel('Roundness (Wadell)', fontsize=12)
ax1.set_title('Sphericity vs Roundness (Unnormalized)', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.set_xlabel('Sphericity (Wadell)', fontsize=12)
ax2.set_ylabel('Roundness (Wadell)', fontsize=12)
ax2.set_title('Sphericity vs Roundness (Normalized)', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comparison_sphericity_roundness.png', dpi=300)
print("Saved: comparison_sphericity_roundness.png")
plt.close()

# ================================================================
# SUMMARY TABLE
# ================================================================
print("\n" + "=" * 70)
print("COMPARATIVE SUMMARY")
print("=" * 70)

summary_data = []
for res in all_results:
    sph = res['sphericity'][~np.isnan(res['sphericity'])]
    rnd = res['roundness'][~np.isnan(res['roundness'])]

    summary_data.append({
        'Dataset': res['name'],
        'Grid Size': f"{res['grid_size'][0]}³",
        'Slice Area (µm²)': res['slice_area_nm2'] / 1e6,
        'Detected': res['total_detected'],
        'Analyzed': res['analyzed'],
        'Area Fraction': res['area_fraction'],
        'Mean Volume (nm³)': np.mean(res['volumes_nm3']),
        'Mean Diameter (nm)': np.mean(res['equiv_diameters_nm']),
        'Mean Aspect Ratio': np.mean(res['aspect_ratios']),
        'Mean Sphericity': np.nanmean(sph) if len(sph) > 0 else np.nan,
        'Mean Roundness': np.nanmean(rnd) if len(rnd) > 0 else np.nan,
        'Mean NN Distance (nm)': np.mean(res['nearest_neighbor_nm']) if len(res['nearest_neighbor_nm']) > 0 else np.nan,
    })

summary_df = pd.DataFrame(summary_data)
summary_df.to_csv('comparison_summary.csv', index=False)
print("\nSaved: comparison_summary.csv")
print("\n" + summary_df.to_string(index=False))

# ================================================================
# NORMALIZED STATISTICS TABLE
# ================================================================
print("\n" + "=" * 70)
print("NORMALIZED STATISTICS (per unit area)")
print("=" * 70)

norm_data = []
for res in all_results:
    area_um2 = res['slice_area_nm2'] / 1e6

    norm_data.append({
        'Dataset': res['name'],
        'Precipitates per µm²': res['analyzed'] / area_um2,
        'γ\' Area Fraction': res['area_fraction'],
        'Mean Spacing (nm)': np.mean(res['nearest_neighbor_nm']) if len(res['nearest_neighbor_nm']) > 0 else np.nan,
    })

norm_df = pd.DataFrame(norm_data)
norm_df.to_csv('comparison_normalized.csv', index=False)
print("\nSaved: comparison_normalized.csv")
print("\n" + norm_df.to_string(index=False))

print("\n" + "=" * 70)
print("COMPARISON ANALYSIS COMPLETE")
print("=" * 70)
print("Generated files:")
print("  - comparison_morphology.png (6-panel comparison)")
print("  - comparison_sphericity_roundness.png (scatter plots)")
print("  - comparison_summary.csv (detailed statistics)")
print("  - comparison_normalized.csv (area-normalized metrics)")
print("=" * 70)
