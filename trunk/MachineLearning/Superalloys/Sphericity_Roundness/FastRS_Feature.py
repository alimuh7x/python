#!/home/alimuh7x/myenv/bin/python3
"""
Sphericity and Roundness Analysis using fast_rs (2D Slice)
===========================================================
This script analyzes γ' precipitates in a single 2D slice using the fast_rs
library to calculate Wadell sphericity and roundness for each individual precipitate.

For demonstration purposes, we analyze a single slice (256x256) from the middle
of the 3D volume to enable fast processing.

Reference: https://github.com/PaPieta/fast_rs
"""

import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label
from scipy.spatial import KDTree
from fast_rs import rs
import pandas as pd

# ================================================================
# PHYSICAL UNITS SETUP
# ================================================================
dx = 30.0  # nm (grid spacing)
print("=" * 70)
print("FAST_RS SPHERICITY & ROUNDNESS ANALYSIS (2D SLICE)")
print("=" * 70)
print(f"Grid spacing (dx): {dx} nm")
print("Note: Analyzing single 2D slice for fast processing")
print()

# ================================================================
# 1. LOAD VTK FILE AND EXTRACT SINGLE SLICE
# ================================================================
print("=" * 70)
print("LOADING VTK FILE")
print("=" * 70)
mesh = pv.read("./PF_Initial.vts")
phi = mesh["PhaseFraction_1"]  # γ' phase order parameter
Nx, Ny, Nz = 256, 256, 256
phi = phi.reshape(Nx, Ny, Nz)
print(f"Loaded mesh with dimensions: {Nx} x {Ny} x {Nz}")

# Extract middle slice (2D analysis for speed)
slice_index = Nz // 2  # Middle slice in z-direction
phi_slice = phi[:, :, slice_index]
print(f"Extracting 2D slice at z={slice_index} (middle of volume)")
print(f"Slice dimensions: {phi_slice.shape[0]} x {phi_slice.shape[1]}")
print(f"Physical slice size: {Nx*dx:.1f} x {Ny*dx:.1f} nm²")
print(f"Total voxels in slice: {phi_slice.size:,}")
print()

print("Creating binary phase field (threshold = 0.5)...")
binary = (phi_slice > 0.5).astype(int)
print(f"Binary phase created: {np.sum(binary):,} voxels belong to γ' phase")
print()

# ================================================================
# 2. LABEL PRECIPITATES FIRST
# ================================================================
print("=" * 70)
print("LABELING INDIVIDUAL PRECIPITATES")
print("=" * 70)
print("Running connected component labeling...")
labels, N = label(binary)
print(f"Number of precipitates detected: {N}")
print()

# ================================================================
# 3. CALCULATE SPHERICITY AND ROUNDNESS PER PRECIPITATE
# ================================================================
print("=" * 70)
print("CALCULATING SPHERICITY & ROUNDNESS (fast_rs)")
print("=" * 70)
print("Processing each precipitate individually to avoid memory issues...")
print("This may take some time...")

sphericity_vec = []
roundness_vec = []
valid_labels = []

for i in range(1, N + 1):
    coords = np.argwhere(labels == i)
    if coords.shape[0] < 10:  # Filter small particles (reduced threshold for 2D)
        continue

    # Extract bounding box for this precipitate
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)

    # Create a small binary mask for this precipitate only (2D)
    precipitate_mask = np.zeros((maxs[0] - mins[0] + 3,
                                  maxs[1] - mins[1] + 3), dtype=bool)

    # Place precipitate in center of small mask
    local_coords = coords - mins + 1
    precipitate_mask[local_coords[:, 0],
                     local_coords[:, 1]] = True

    try:
        # Calculate sphericity and roundness for this precipitate
        roundness, sphericity, _ = rs.rs_calculate(precipitate_mask)

        if len(roundness) > 0 and len(sphericity) > 0:
            roundness_vec.append(roundness[0])
            sphericity_vec.append(sphericity[0])
            valid_labels.append(i)
    except Exception as e:
        print(f"Warning: Failed to process precipitate {i}: {str(e)}")
        continue

    if i % 100 == 0:
        print(f"Processed {i}/{N} precipitates...")

sphericity_vec = np.array(sphericity_vec)
roundness_vec = np.array(roundness_vec)

print(f"Analysis complete!")
print(f"Successfully analyzed: {len(roundness_vec)} precipitates")
print(f"Mean sphericity (Wadell): {np.mean(sphericity_vec):.4f}")
print(f"Mean roundness (Wadell): {np.mean(roundness_vec):.4f}")
print()

# ================================================================
# 4. EXTRACT ADDITIONAL FEATURES FOR VALID PRECIPITATES
# ================================================================
print("=" * 70)
print("EXTRACTING ADDITIONAL MORPHOLOGY FEATURES")
print("=" * 70)

volumes_nm3 = []
volumes_voxels = []
equiv_diameters_nm = []
aspect_ratios = []
centroids_physical = []

voxel_volume = dx ** 3

print(f"Extracting features for {len(valid_labels)} analyzed precipitates...")
for label_id in valid_labels:
    coords = np.argwhere(labels == label_id)

    # Volume
    V_voxels = coords.shape[0]
    V_nm3 = V_voxels * voxel_volume
    volumes_voxels.append(V_voxels)
    volumes_nm3.append(V_nm3)

    # Equivalent diameter
    D_nm = (6 * V_nm3 / np.pi) ** (1 / 3)
    equiv_diameters_nm.append(D_nm)

    # Aspect ratio from bounding box (2D)
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    Lx, Ly = (maxs - mins + 1) * dx
    AR = max(Lx, Ly) / min(Lx, Ly)
    aspect_ratios.append(AR)

    # Centroid in physical units
    centroid = np.mean(coords, axis=0) * dx
    centroids_physical.append(centroid)

print(f"Extracted features for {len(volumes_nm3)} precipitates")
print()

# ================================================================
# 5. SPATIAL STATISTICS (Nearest Neighbor)
# ================================================================
print("=" * 70)
print("CALCULATING SPATIAL STATISTICS")
print("=" * 70)
print("Computing nearest-neighbor distances...")

centroids_physical = np.array(centroids_physical)
tree = KDTree(centroids_physical)
distances, _ = tree.query(centroids_physical, k=2)
nearest_neighbor_nm = distances[:, 1]

print(f"Mean nearest-neighbor distance: {np.mean(nearest_neighbor_nm):.2f} nm")
print(f"Std nearest-neighbor distance: {np.std(nearest_neighbor_nm):.2f} nm")
print()

# ================================================================
# 6. GLOBAL STATISTICS
# ================================================================
print("=" * 70)
print("GLOBAL STATISTICS")
print("=" * 70)
gamma_p_fraction = np.mean(binary)
print(f"γ' volume fraction: {gamma_p_fraction:.4f} ({gamma_p_fraction*100:.2f}%)")
print(f"Total precipitates detected: {len(roundness_vec)}")
print(f"Precipitates analyzed (≥20 voxels): {len(volumes_nm3)}")
print(f"Mean volume: {np.mean(volumes_nm3):.2e} nm³ (~{np.mean(volumes_voxels):.1f} voxels)")
print(f"Mean equivalent diameter: {np.mean(equiv_diameters_nm):.2f} nm")
print(f"Mean aspect ratio: {np.mean(aspect_ratios):.2f}")
print(f"Mean sphericity (Wadell): {np.mean(sphericity_vec):.4f}")
print(f"Mean roundness (Wadell): {np.mean(roundness_vec):.4f}")
print()

# ================================================================
# 7. SAVE RESULTS TO CSV
# ================================================================
print("=" * 70)
print("SAVING RESULTS")
print("=" * 70)

# Per-precipitate features
features_df = pd.DataFrame({
    'label_id': valid_labels,
    'volume_nm3': volumes_nm3,
    'volume_voxels': volumes_voxels,
    'equiv_diameter_nm': equiv_diameters_nm,
    'aspect_ratio': aspect_ratios,
    'sphericity_wadell': sphericity_vec,
    'roundness_wadell': roundness_vec,
    'nearest_neighbor_nm': nearest_neighbor_nm
})

features_df.to_csv('precipitate_features.csv', index=False)
print("Saved: precipitate_features.csv")

# Global summary
summary_df = pd.DataFrame({
    'dx_nm': [dx],
    'volume_fraction': [gamma_p_fraction],
    'total_precipitates_detected': [N],
    'precipitates_analyzed': [len(volumes_nm3)],
    'mean_volume_nm3': [np.mean(volumes_nm3)],
    'mean_equiv_diameter_nm': [np.mean(equiv_diameters_nm)],
    'mean_aspect_ratio': [np.mean(aspect_ratios)],
    'mean_sphericity_wadell': [np.mean(sphericity_vec)],
    'mean_roundness_wadell': [np.mean(roundness_vec)],
    'mean_nearest_neighbor_nm': [np.mean(nearest_neighbor_nm)]
})

summary_df.to_csv('global_summary.csv', index=False)
print("Saved: global_summary.csv")
print()

# ================================================================
# 8. VISUALIZATION
# ================================================================
print("=" * 70)
print("GENERATING PLOTS")
print("=" * 70)

# Morphology features plot
fig, axes = plt.subplots(2, 3, figsize=(16, 10))

# Volume distribution
axes[0, 0].hist(volumes_nm3, bins=30, edgecolor='black', alpha=0.7, color='green')
axes[0, 0].set_xlabel("Volume (nm³)", fontsize=11)
axes[0, 0].set_ylabel("Frequency", fontsize=11)
axes[0, 0].set_title("Precipitate Volume Distribution", fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# Equivalent diameter distribution
axes[0, 1].hist(equiv_diameters_nm, bins=30, edgecolor='black', alpha=0.7, color='teal')
axes[0, 1].set_xlabel("Equivalent Diameter (nm)", fontsize=11)
axes[0, 1].set_ylabel("Frequency", fontsize=11)
axes[0, 1].set_title("Equivalent Diameter Distribution", fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# Aspect ratio distribution
axes[0, 2].hist(aspect_ratios, bins=30, edgecolor='black', alpha=0.7, color='orange')
axes[0, 2].set_xlabel("Aspect Ratio", fontsize=11)
axes[0, 2].set_ylabel("Frequency", fontsize=11)
axes[0, 2].set_title("Aspect Ratio Distribution", fontsize=12, fontweight='bold')
axes[0, 2].grid(True, alpha=0.3)

# Sphericity distribution (Wadell)
axes[1, 0].hist(sphericity_vec, bins=30, edgecolor='black', alpha=0.7, color='purple')
axes[1, 0].set_xlabel("Sphericity (Wadell)", fontsize=11)
axes[1, 0].set_ylabel("Frequency", fontsize=11)
axes[1, 0].set_title("Sphericity Distribution (fast_rs)", fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# Roundness distribution (Wadell)
axes[1, 1].hist(roundness_vec, bins=30, edgecolor='black', alpha=0.7, color='crimson')
axes[1, 1].set_xlabel("Roundness (Wadell)", fontsize=11)
axes[1, 1].set_ylabel("Frequency", fontsize=11)
axes[1, 1].set_title("Roundness Distribution (fast_rs)", fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

# Nearest neighbor distribution
axes[1, 2].hist(nearest_neighbor_nm, bins=30, edgecolor='black', alpha=0.7, color='steelblue')
axes[1, 2].set_xlabel("Distance (nm)", fontsize=11)
axes[1, 2].set_ylabel("Frequency", fontsize=11)
axes[1, 2].set_title("Nearest Neighbor Distribution", fontsize=12, fontweight='bold')
axes[1, 2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("morphology_features.png", dpi=300)
plt.close()
print("Saved: morphology_features.png")
print()

# Sphericity vs Roundness scatter plot
plt.figure(figsize=(10, 8))
plt.scatter(sphericity_vec, roundness_vec, alpha=0.6, s=50, c=volumes_nm3,
            cmap='viridis', edgecolors='black', linewidth=0.5)
plt.xlabel("Sphericity (Wadell)", fontsize=12)
plt.ylabel("Roundness (Wadell)", fontsize=12)
plt.title("Sphericity vs Roundness (colored by volume)", fontsize=14, fontweight='bold')
plt.colorbar(label='Volume (nm³)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("sphericity_vs_roundness.png", dpi=300)
plt.close()
print("Saved: sphericity_vs_roundness.png")
print()

print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print("Generated files:")
print("  - precipitate_features.csv")
print("  - global_summary.csv")
print("  - morphology_features.png")
print("  - sphericity_vs_roundness.png")
print()
print("Summary statistics:")
print(f"  Volume fraction: {gamma_p_fraction:.4f}")
print(f"  Number of precipitates: {len(volumes_nm3)}")
print(f"  Mean sphericity (Wadell): {np.mean(sphericity_vec):.4f}")
print(f"  Mean roundness (Wadell): {np.mean(roundness_vec):.4f}")
print(f"  Mean volume: {np.mean(volumes_nm3):.2e} nm³")
print(f"  Mean diameter: {np.mean(equiv_diameters_nm):.2f} nm")
print(f"  Mean aspect ratio: {np.mean(aspect_ratios):.2f}")
print(f"  Mean NN distance: {np.mean(nearest_neighbor_nm):.2f} nm")
print("=" * 70)
