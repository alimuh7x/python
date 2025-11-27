#!/home/alimuh7x/myenv/bin/python3
import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label
from scipy.spatial import KDTree
from skimage.measure import marching_cubes, mesh_surface_area, regionprops
from scipy.stats import wasserstein_distance
from scipy.spatial.distance import directed_hausdorff


# ================================================================
# PHYSICAL UNITS SETUP
# ================================================================
dx = 30.0  # nm (grid spacing)
print("="*70)
print("PHYSICAL UNITS SETUP")
print("="*70)
print(f"Grid spacing (dx): {dx} nm")
print()

# ================================================================
# 1. LOAD VTK FILE
# ================================================================
print("="*70)
print("LOADING VTK FILE")
print("="*70)
mesh = pv.read("./PF_Initial.vts")  # <-- YOUR VTK
phi = mesh["PhaseFraction_1"]  # PF order parameter (γ′ phase)
Nx, Ny, Nz = 256, 256, 256  # adjust if needed
phi = phi.reshape(Nx, Ny, Nz)
print(f"Loaded mesh with dimensions: {Nx} x {Ny} x {Nz}")
print(f"Physical domain size: {Nx*dx:.1f} x {Ny*dx:.1f} x {Nz*dx:.1f} nm³")
print(f"Total voxels: {Nx*Ny*Nz}")
print()

print("Creating binary phase field (threshold = 0.5)...")
binary = (phi > 0.5).astype(int)
print(f"Binary phase created: {np.sum(binary)} voxels belong to γ′ phase")
print()


# ================================================================
# 2. BASIC GLOBAL FEATURES
# ================================================================
print("="*70)
print("CALCULATING GLOBAL FEATURES")
print("="*70)
print("Computing γ′ volume fraction...")
gamma_p_fraction = np.mean(binary)
print(f"γ′ volume fraction = {gamma_p_fraction:.4f} ({gamma_p_fraction*100:.2f}%)")
print()


# ================================================================
# 3. LABEL PRECIPITATES
# ================================================================
print("="*70)
print("LABELING INDIVIDUAL PRECIPITATES")
print("="*70)
print("Running connected component labeling...")
labels, N = label(binary)
print(f"Number of precipitates detected = {N}")
print()


# ================================================================
# 4. PER-PRECIPITATE MORPHOLOGY FEATURES
# ================================================================
print("="*70)
print("CALCULATING PER-PRECIPITATE MORPHOLOGY")
print("="*70)
volumes = []  # Will store volumes in nm³
volumes_voxels = []  # Store voxel counts for reference
aspect_ratios = []
sphericities = []
equiv_diameters = []  # Will store diameters in nm
curvatures = []

print(f"Analyzing {N} precipitates (filtering out particles < 20 voxels)...")
voxel_volume = dx**3  # nm³ per voxel
print(f"Voxel volume: {voxel_volume:.1f} nm³")

filtered_count = 0
for i in range(1, N + 1):
    coords = np.argwhere(labels == i)
    if coords.shape[0] < 20:
        continue

    filtered_count += 1

    # ---------- Volume ----------
    V_voxels = coords.shape[0]
    V_nm3 = V_voxels * voxel_volume  # Convert to nm³
    volumes.append(V_nm3)
    volumes_voxels.append(V_voxels)

    # ---------- Bounding box aspect ratio ----------
    mins = coords.min(axis=0)
    maxs = coords.max(axis=0)
    Lx, Ly, Lz = (maxs - mins + 1) * dx  # Convert to nm
    AR = max(Lx, Ly, Lz) / min(Lx, Ly, Lz)
    aspect_ratios.append(AR)

    # ---------- Equivalent spherical diameter ----------
    D_nm = (6 * V_nm3 / np.pi) ** (1 / 3)  # in nm
    equiv_diameters.append(D_nm)

print(f"Analyzed {filtered_count} precipitates (after size filtering)")
print(f"Mean volume: {np.mean(volumes):.2f} nm³ ({np.mean(volumes_voxels):.1f} voxels)")
print(f"Mean equivalent diameter: {np.mean(equiv_diameters):.2f} nm")
print(f"Mean aspect ratio: {np.mean(aspect_ratios):.2f}")
print()


# ================================================================
# 5. EXTRACT SURFACE FOR CURVATURE & SPHERICITY
# ================================================================
print("="*70)
print("EXTRACTING SURFACE MESH AND CALCULATING SPHERICITY")
print("="*70)
print("Running marching cubes algorithm...")
verts, faces, _, _ = marching_cubes(binary, level=0.5)
# Scale vertices to physical units
verts_physical = verts * dx
faces_fixed = np.hstack([np.full((len(faces), 1), 3), faces])
surface_mesh = pv.PolyData(verts_physical, faces_fixed)

total_surface = mesh_surface_area(verts_physical, faces)
print(f"Total γ′ surface area = {total_surface:.2f} nm²")

# ---------- Sphericity ----------
print("Calculating sphericity for each precipitate...")
for v in volumes:
    S = total_surface
    sp = np.pi ** (1 / 3) * (6 * v) ** (2 / 3) / S
    sphericities.append(sp)

print(f"Mean sphericity = {np.mean(sphericities):.4f}")
print()


# ================================================================
# 6. SPATIAL STATISTICS (Nearest neighbor + g(r))
# ================================================================
print("="*70)
print("CALCULATING SPATIAL STATISTICS")
print("="*70)
print("Computing precipitate centroids...")
centroids = np.array([
    np.mean(np.argwhere(labels == i), axis=0)
    for i in range(1, N + 1)
    if np.argwhere(labels == i).shape[0] > 20
])
centroids_physical = centroids * dx  # Convert to nm

print(f"Building KD-tree for {len(centroids)} centroids...")
tree = KDTree(centroids_physical)
distances, _ = tree.query(centroids_physical, k=2)
nearest_neighbor = distances[:, 1]  # in nm

print(f"Mean nearest-neighbor distance = {np.mean(nearest_neighbor):.2f} nm")
print(f"Std nearest-neighbor distance = {np.std(nearest_neighbor):.2f} nm")
print()

print("Generating nearest-neighbor distribution plot...")
plt.figure(figsize=(10, 6))
plt.hist(nearest_neighbor, bins=25, edgecolor='black', alpha=0.7, color='steelblue')
plt.xlabel("Distance (nm)", fontsize=12)
plt.ylabel("Frequency", fontsize=12)
plt.title("Nearest Neighbor Distribution", fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("NN_distribution.png", dpi=300)
plt.close()
print("Saved: NN_distribution.png")
print()


# ================================================================
# 7. PAIR CORRELATION FUNCTION g(r)
# ================================================================
print("="*70)
print("CALCULATING PAIR CORRELATION FUNCTION g(r)")
print("="*70)

def pair_correlation(centers, dr=30, rmax=1800):
    """Calculate pair correlation function g(r) in physical units (nm)."""
    N = centers.shape[0]
    g = []
    radii = np.arange(dr, rmax, dr)

    # Physical domain volume in nm³
    domain_volume = (Nx * dx) * (Ny * dx) * (Nz * dx)

    print(f"Computing g(r) with dr={dr} nm, rmax={rmax} nm...")
    for idx, r in enumerate(radii):
        if idx % 10 == 0:
            print(f"  Processing r = {r:.1f} nm ({idx+1}/{len(radii)})...")
        count = 0
        for c in centers:
            d = np.linalg.norm(centers - c, axis=1)
            count += np.sum((d > r) & (d <= r + dr))

        shell_volume = 4 * np.pi * ((r + dr) ** 3 - r ** 3) / 3
        density = N / domain_volume
        g.append(count / (N * shell_volume * density))

    return radii, np.array(g)


r, g_r = pair_correlation(centroids_physical)
print(f"g(r) calculation complete")
print()

print("Generating g(r) plot...")
plt.figure(figsize=(10, 6))
plt.plot(r, g_r, linewidth=2, color='darkred')
plt.axhline(y=1, color='black', linestyle='--', alpha=0.5, label='Random distribution')
plt.xlabel("Distance r (nm)", fontsize=12)
plt.ylabel("g(r)", fontsize=12)
plt.title("Pair Correlation Function g(r)", fontsize=14, fontweight='bold')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("g_r.png", dpi=300)
plt.close()
print("Saved: g_r.png")
print()


# ================================================================
# 8. TOPOLOGY (Euler characteristic)
# ================================================================
print("="*70)
print("CALCULATING TOPOLOGY FEATURES")
print("="*70)
print("Computing Euler characteristic...")
regions = regionprops(binary.astype(int))
euler = regions[0].euler_number
print(f"Euler characteristic = {euler}")
print()


# ================================================================
# 9. SAVE ALL FEATURE VALUES
# ================================================================
print("="*70)
print("SAVING RESULTS")
print("="*70)
# CHANGE NOTE: output format switched from NPZ to CSV files for easier inspection.
# Files written: precipitate_features.csv, pair_correlation.csv, global_summary.csv.
# Accept this change? Remove this note once confirmed.
print("Saving feature data to CSV files...")

# Per-precipitate features
features_matrix = np.column_stack((
    np.array(volumes),
    np.array(volumes_voxels),
    np.array(aspect_ratios),
    np.array(sphericities),
    np.array(equiv_diameters),
    np.array(nearest_neighbor),
))
np.savetxt(
    "precipitate_features.csv",
    features_matrix,
    delimiter=",",
    header="volume_nm3,volume_voxels,aspect_ratio,sphericity,equiv_diameter_nm,nearest_neighbor_nm",
    comments=""
)
print("Saved: precipitate_features.csv")

# Pair correlation function g(r)
np.savetxt(
    "pair_correlation.csv",
    np.column_stack((r, g_r)),
    delimiter=",",
    header="r_nm,g_r",
    comments=""
)
print("Saved: pair_correlation.csv")

# Global summary statistics
summary_stats = np.array([[
    dx,
    gamma_p_fraction,
    filtered_count,
    np.mean(volumes),
    np.mean(equiv_diameters),
    np.mean(aspect_ratios),
    np.mean(sphericities),
    np.mean(nearest_neighbor),
    euler
]])
np.savetxt(
    "global_summary.csv",
    summary_stats,
    delimiter=",",
    header="dx_nm,volume_fraction,precipitates_analyzed,mean_volume_nm3,mean_equiv_diameter_nm,mean_aspect_ratio,mean_sphericity,mean_nearest_neighbor_nm,euler_characteristic",
    comments=""
)
print("Saved: global_summary.csv")
print()


# ================================================================
# 10. ADDITIONAL MORPHOLOGY PLOTS
# ================================================================
print("Generating morphology distribution plots...")

# Create a comprehensive figure with multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Volume distribution
axes[0, 0].hist(volumes, bins=30, edgecolor='black', alpha=0.7, color='green')
axes[0, 0].set_xlabel("Volume (nm³)", fontsize=11)
axes[0, 0].set_ylabel("Frequency", fontsize=11)
axes[0, 0].set_title("Precipitate Volume Distribution", fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# Aspect ratio distribution
axes[0, 1].hist(aspect_ratios, bins=30, edgecolor='black', alpha=0.7, color='orange')
axes[0, 1].set_xlabel("Aspect Ratio", fontsize=11)
axes[0, 1].set_ylabel("Frequency", fontsize=11)
axes[0, 1].set_title("Aspect Ratio Distribution", fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# Sphericity distribution
axes[1, 0].hist(sphericities, bins=30, edgecolor='black', alpha=0.7, color='purple')
axes[1, 0].set_xlabel("Sphericity", fontsize=11)
axes[1, 0].set_ylabel("Frequency", fontsize=11)
axes[1, 0].set_title("Sphericity Distribution", fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# Equivalent diameter distribution
axes[1, 1].hist(equiv_diameters, bins=30, edgecolor='black', alpha=0.7, color='teal')
axes[1, 1].set_xlabel("Equivalent Diameter (nm)", fontsize=11)
axes[1, 1].set_ylabel("Frequency", fontsize=11)
axes[1, 1].set_title("Equivalent Diameter Distribution", fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("morphology_features.png", dpi=300)
plt.close()
print("Saved: morphology_features.png")
print()

print("="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print("Generated files:")
print("  - precipitate_features.csv")  # CSV (was NPZ)
print("  - pair_correlation.csv")      # CSV (was NPZ)
print("  - global_summary.csv")        # CSV (was NPZ)
print("  - NN_distribution.png")
print("  - g_r.png")
print("  - morphology_features.png")
print()
print("Summary statistics:")
print(f"  Volume fraction: {gamma_p_fraction:.4f}")
print(f"  Number of precipitates: {filtered_count}")
print(f"  Mean volume: {np.mean(volumes):.2f} nm³")
print(f"  Mean diameter: {np.mean(equiv_diameters):.2f} nm")
print(f"  Mean aspect ratio: {np.mean(aspect_ratios):.2f}")
print(f"  Mean sphericity: {np.mean(sphericities):.4f}")
print(f"  Mean NN distance: {np.mean(nearest_neighbor):.2f} nm")
print(f"  Euler characteristic: {euler}")
print("="*70)
