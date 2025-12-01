#!/home/alimuh7x/myenv/bin/python3
"""
Cube-to-Raft Transition Analysis using fast_rs
===============================================
This script compares three VTK files representing the cube-to-raft transition
in I3' precipitates at different strain levels using the fast_rs library.

- PhaseField_Initial.vts: Initial cubic morphology
- PhaseField_0.6_percent.vts: 0.6% strain
- PhaseField_1.0_precent.vts: 1.0% strain

All datasets: 128x128x128 grid
Analysis: Single z-slice at z=40
Results shown both normalized and unnormalized.
"""

# Import necessary libraries for VTK processing, numerical analysis, visualization, and morphological characterization.
# These modules enable reading phase-field data, computing precipitate features, and generating comparative plots.
import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import label
from scipy.spatial import KDTree
from scipy.stats import gaussian_kde
from fast_rs import rs
import pandas as pd

# ------------------------------------------------
# Helpers for histogram smoothing / zero fill
# ------------------------------------------------
def compute_feature_range(results, feature, fallback=(0.0, 1.0)):
    """Compute a global percentile-based range for a feature across all datasets."""
    ranges = []
    for res in results:
        data = res.get(feature, np.array([]))
        data = data[~np.isnan(data)]
        if len(data) > 0:
            ranges.append(np.percentile(data, [1, 99]))
    if not ranges:
        return fallback
    ranges = np.array(ranges)
    return float(np.min(ranges[:, 0])), float(np.max(ranges[:, 1]))


def smooth_density(data, x_min, x_max, num=200, edge_frac=0.05):
    """
    Return xs, ys for a smooth density curve.
    - Empty data returns zeros (flat baseline).
    - Single-point data uses a narrow Gaussian kernel.
    - Curves taper to zero at edges for smooth transitions.
    """
    xs = np.linspace(x_min, x_max, num) if x_max > x_min else np.linspace(0.0, 1.0, num)
    if x_max <= x_min:
        return xs, np.zeros_like(xs)

    data = data[~np.isnan(data)]
    if len(data) == 0:
        ys = np.zeros_like(xs)
    elif len(data) == 1:
        bw = max(1e-6, 0.1 * (x_max - x_min))
        ys = np.exp(-0.5 * ((xs - data[0]) / bw) ** 2)
        ys = ys / (np.trapz(ys, xs) + 1e-12)
    else:
        try:
            kde = gaussian_kde(data)
            ys = kde(xs)
        except Exception:
            # Fallback if covariance is singular (e.g., near-constant data)
            bw = max(1e-6, 0.05 * (x_max - x_min))
            ys = np.exp(-0.5 * ((xs - np.mean(data)) / bw) ** 2)
            ys = ys / (np.trapz(ys, xs) + 1e-12)

    # Taper edges smoothly to zero to avoid sharp cutoffs
    ramp_len = max(3, int(num * edge_frac))
    taper = np.ones_like(xs)
    taper[:ramp_len] = np.linspace(0.0, 1.0, ramp_len)
    taper[-ramp_len:] = np.linspace(1.0, 0.0, ramp_len)
    ys = ys * taper
    return xs, ys

# ================================================================
# CONFIGURATION
# ================================================================
# Define the physical grid spacing in nanometers for converting voxel dimensions to real-world measurements.
# This value is critical for accurate volume, diameter, and spacing calculations.
dx = 30.0  # nm (grid spacing)

# Extract a 2D slice from the 3D phase-field mesh at a specified z-index.
# Returns the phase fraction array for the slice and the full mesh dimensions.
def extract_slice(mesh, slice_z):
    """Return the XY slice at z = slice_z and the mesh dimensions."""
    Nx, Ny, Nz = mesh.dimensions
    phi = mesh["PhaseFraction_1"]
    start_idx = slice_z * Nx * Ny
    end_idx = start_idx + Nx * Ny
    return phi[start_idx:end_idx].reshape(Nx, Ny), (Nx, Ny, Nz)

# Configure the three datasets representing different stages of the cube-to-raft morphological transition.
# Each dataset specifies the VTK file path, slice index, visualization color (blue, red, green), and descriptive label.
datasets = [
    {
        'name': 'Initial',
        'file': './PhaseField_Initial.vts',
        'slice_index': 40,
        'color': '#2E86DE',  # Blue
        'label': 'Initial (Cubic)'
    },
    {
        'name': '0.6%',
        'file': './PhaseField_0.6_percent.vts',
        'slice_index': 40,
        'color': '#E74C3C',  # Red
        'label': '0.6% Strain'
    },
    {
        'name': '1.0%',
        'file': './PhaseField_1.0_precent.vts',
        'slice_index': 40,
        'color': '#27AE60',  # Green
        'label': '1.0% Strain (Raft)'
    }
]

print("=" * 70)
print("CUBE-TO-RAFT TRANSITION ANALYSIS (fast_rs)")
print("=" * 70)
print(f"Grid spacing (dx): {dx} nm")
print()

# ================================================================
# PROCESS ALL DATASETS
# ================================================================
# Initialize containers to store analysis results and slice information for each dataset.
# The loop below processes each VTK file to extract morphological features of precipitates.
all_results = []
slice_summaries = []

for ds in datasets:
    print("=" * 70)
    print(f"PROCESSING: {ds['label']}")
    print("=" * 70)

    # Load the VTK structured grid file containing 3D phase-field data.
    # Extract the 2D slice at the specified z-index for morphological analysis.
    mesh = pv.read(ds['file'])
    phi_slice, (Nx, Ny, Nz) = extract_slice(mesh, ds['slice_index'])
    print(f"Grid size: {Nx} x {Ny} x {Nz}")

    slice_idx = ds['slice_index']
    print(f"Extracting slice at z={slice_idx}")
    print(f"Physical size: {Nx*dx:.1f} x {Ny*dx:.1f} nmA�")

    # Convert the continuous phase fraction field to a binary mask by thresholding at 0.5.
    # This identifies γ' precipitate regions (value 1) versus the matrix (value 0).
    binary = (phi_slice > 0.5).astype(int)
    print(f"I3' voxels: {np.sum(binary):,}")
    phi = mesh["PhaseFraction_1"]
    print(f"I3' volume fraction in 3D: {100*np.mean(phi > 0.5):.1f}%")

    # Apply connected-component labeling to identify individual precipitates in the binary mask.
    # Each isolated region receives a unique label number for individual analysis.
    labels, N = label(binary)
    print(f"Precipitates detected: {N}")
    slice_summaries.append((ds['label'], binary, N, slice_idx))

    # Initialize arrays to store morphological features for each precipitate.
    # Features include sphericity, roundness, volume, diameter, aspect ratio, and centroid position.
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

    # Loop through each labeled precipitate to extract coordinates and compute morphological features.
    # Precipitates smaller than 10 voxels are excluded to avoid noise artifacts.
    for i in range(1, N + 1):
        coords = np.argwhere(labels == i)
        if coords.shape[0] < 10:
            continue

        # Determine the bounding box of the precipitate to create a local coordinate system.
        # This reduces memory usage and speeds up fast_rs calculations.
        mins = coords.min(axis=0)
        maxs = coords.max(axis=0)

        # Create a minimal binary mask for the precipitate with padding for edge detection.
        # Local coordinates are shifted relative to the bounding box minimum.
        precipitate_mask = np.zeros((maxs[0] - mins[0] + 3,
                                      maxs[1] - mins[1] + 3), dtype=bool)
        local_coords = coords - mins + 1
        precipitate_mask[local_coords[:, 0], local_coords[:, 1]] = True

        # Call the fast_rs library to compute Wadell's roundness and sphericity from the binary mask.
        # These metrics quantify how closely the precipitate shape resembles a perfect circle.
        try:
            roundness, sphericity, _ = rs.rs_calculate(precipitate_mask)

            if len(roundness) > 0 and len(sphericity) > 0:
                roundness_vec.append(roundness[0])
                sphericity_vec.append(sphericity[0])
                valid_labels.append(i)

                # Compute additional geometric features: volume, equivalent diameter, and aspect ratio.
                # Equivalent diameter is calculated assuming a spherical geometry for normalization.
                V_voxels = coords.shape[0]
                V_nm3 = V_voxels * voxel_volume
                volumes_voxels.append(V_voxels)
                volumes_nm3.append(V_nm3)

                D_nm = (6 * V_nm3 / np.pi) ** (1 / 3)
                equiv_diameters_nm.append(D_nm)

                Lx, Ly = (maxs - mins + 1) * dx
                AR = max(Lx, Ly) / min(Lx, Ly) if min(Lx, Ly) > 0 else 1.0
                aspect_ratios.append(AR)

                centroid = np.mean(coords, axis=0) * dx
                centroids_physical.append(centroid)
        except Exception:
            continue

        if i % 50 == 0:
            print(f"  Processed {i}/{N}...")

    sphericity_vec = np.array(sphericity_vec)
    roundness_vec = np.array(roundness_vec)

    # Build a KDTree from precipitate centroids to compute nearest-neighbor distances.
    # This quantifies the spatial distribution and average spacing between precipitates.
    if len(centroids_physical) > 1:
        centroids_physical = np.array(centroids_physical)
        tree = KDTree(centroids_physical)
        distances, _ = tree.query(centroids_physical, k=2)
        nearest_neighbor_nm = distances[:, 1]
    else:
        nearest_neighbor_nm = np.array([])

    # Package all computed features into a results dictionary for this dataset.
    # This includes morphological metrics, spatial statistics, and metadata for later visualization.
    gamma_p_fraction = np.mean(binary)

    results = {
        'name': ds['name'],
        'label': ds['label'],
        'color': ds['color'],
        'grid_size': (Nx, Ny, Nz),
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
    if len(sphericity_vec) > 0:
        print(f"Mean sphericity: {np.nanmean(sphericity_vec):.3f}")
        print(f"Mean roundness: {np.nanmean(roundness_vec):.3f}")
        print(f"Mean aspect ratio: {np.nanmean(aspect_ratios):.3f}")
    print()

# ================================================================
# COMPARATIVE VISUALIZATION
# ================================================================
print("=" * 70)
print("GENERATING COMPARATIVE PLOTS")
print("=" * 70)

# Create side-by-side visualization of binary slices showing precipitate morphology evolution.
# Each panel displays one strain level with the precipitate count labeled.
fig_slice, axes = plt.subplots(1, len(slice_summaries), figsize=(18, 6))
if len(slice_summaries) == 1:
    axes = [axes]
for ax, (label_txt, binary, N, slice_idx) in zip(axes, slice_summaries):
    ax.imshow(binary.T, origin='lower', cmap='viridis', interpolation='nearest')
    ax.set_title(f"{label_txt}\nz={slice_idx} slice\n{N} precipitates", fontweight='bold')
    ax.set_xlabel('X (voxels)')
    ax.set_ylabel('Y (voxels)')
plt.tight_layout()
plt.savefig('slice_comparison.png', dpi=200)
print("Saved: slice_comparison.png")
plt.close(fig_slice)

# Generate 6-panel comparative plot showing distribution curves for key morphological features.
# Uses kernel density estimation for smooth visualization with consistent x-axis ranges across datasets.
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.25)

features = [
    ('volumes_nm3', 'Volume (nmA3)', 'Volume Distribution'),
    ('equiv_diameters_nm', 'Equivalent Diameter (nm)', 'Diameter Distribution'),
    ('aspect_ratios', 'Aspect Ratio', 'Aspect Ratio Distribution'),
    ('sphericity', 'Sphericity (Wadell)', 'Sphericity Distribution'),
    ('roundness', 'Roundness (Wadell)', 'Roundness Distribution'),
    ('nearest_neighbor_nm', 'Nearest Neighbor (nm)', 'NN Distribution'),
]

# Pre-compute global ranges so zero-count datasets still plot smoothly
feature_ranges = {
    feature: compute_feature_range(all_results, feature)
    for feature, _, _ in features
}

for idx, (feature, xlabel, title) in enumerate(features):
    row = idx // 2
    col = idx % 2

    ax = fig.add_subplot(gs[row, col])
    ax.set_title(f"{title}", fontweight='bold')
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Density")
    ax.grid(True, alpha=0.3)

    x_min, x_max = feature_ranges.get(feature, (0.0, 1.0))

    for res in all_results:
        data = res[feature]
        xs, ys = smooth_density(data, x_min, x_max)
        ax.plot(xs, ys, label=f"{res['label']} (n={len(data[~np.isnan(data)])})", color=res['color'], linewidth=2)

    ax.legend()

plt.savefig('comparison_morphology.png', dpi=300, bbox_inches='tight')
print("Saved: comparison_morphology.png")
plt.close()

# ================================================================
# SCATTER PLOT: SPHERICITY VS ROUNDNESS
# ================================================================
# Create scatter plot comparing sphericity and roundness across all three strain levels.
# Color coding (blue, red, green) helps distinguish the cube-to-raft morphological transition.
fig, ax1 = plt.subplots(1, 1, figsize=(8, 7))

for res in all_results:
    sph = res['sphericity']
    rnd = res['roundness']

    valid = ~(np.isnan(sph) | np.isnan(rnd))
    sph = sph[valid]
    rnd = rnd[valid]

    if len(sph) > 0:
        ax1.scatter(
            sph,
            rnd,
            s=50,
            alpha=0.6,
            label=f"{res['label']} (n={len(sph)})",
            c=res['color'],
            edgecolors='black',
            linewidth=0.5
        )

ax1.set_xlabel('Sphericity (Wadell)', fontsize=12)
ax1.set_ylabel('Roundness (Wadell)', fontsize=12)
ax1.set_title('Sphericity vs Roundness', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comparison_sphericity_roundness.png', dpi=300)
print("Saved: comparison_sphericity_roundness.png")
plt.close()

# ================================================================
# TREND VISUALIZATION (LINE/BAR) FOR QUICK COMPARISON
# ================================================================
# Generate 6-panel bar chart showing mean values and standard errors for key metrics.
# This provides a quick visual summary of how features evolve from cubic to raft morphology.
trend_metrics_data = [
    ("Area fraction", 'area_fraction'),
    ("Mean diameter (nm)", 'equiv_diameters_nm'),
    ("Mean aspect ratio", 'aspect_ratios'),
    ("Mean sphericity", 'sphericity'),
    ("Mean roundness", 'roundness'),
    ("Mean spacing (nm)", 'nearest_neighbor_nm'),
]

trend_metrics = []
for title, data_key in trend_metrics_data:
    means = []
    errors = []
    for res in all_results:
        if data_key == 'area_fraction':
            means.append(res['area_fraction'])
            errors.append(0) # Area fraction is a single value per slice, no error bar
        else:
            data = res[data_key]
            data = data[~np.isnan(data)]
            if len(data) > 1:
                means.append(np.nanmean(data))
                errors.append(np.nanstd(data) / np.sqrt(len(data)))
            elif len(data) == 1:
                means.append(data[0])
                errors.append(0)
            else:
                means.append(np.nan)
                errors.append(np.nan)
    trend_metrics.append((title, means, errors))

stages = [res['label'] for res in all_results]
x = np.arange(len(stages))

fig_trend, axes_trend = plt.subplots(2, 3, figsize=(12, 6))
axes_trend = axes_trend.ravel()
colors = [res['color'] for res in all_results]

for ax, (title, values, errors) in zip(axes_trend, trend_metrics):
    bars = ax.bar(x, values, color=colors, width=0.6, yerr=errors, capsize=5, ecolor='black', zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(stages, rotation=20, ha='right')
    ax.set_title(title, fontweight='bold')
    ax.grid(True, axis='y', alpha=0.5, zorder=0)

    # Add data labels on top of bars
    for i, bar in enumerate(bars):
        yval = bar.get_height()
        if np.isnan(yval):
            continue
        # ---- Adjust text position for error bars ------
        error_val = errors[i] if not np.isnan(errors[i]) else 0
        text_y_pos = yval + error_val + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.02 # A little above the error bar
        ax.text(bar.get_x() + bar.get_width() / 2.0, text_y_pos, f'{yval:.3f}',
                va='bottom', ha='center', fontsize=9, fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.2'))

    # Auto-adjust y-axis to give space for labels and error bars
    if not all(np.isnan(values)):
        min_val = np.nanmin(values - np.array(errors)) if len(values) > 0 else 0
        max_val = np.nanmax(values + np.array(errors)) if len(values) > 0 else 0
        
        # Ensure min_val is not negative for non-negative metrics, or allow if appropriate
        min_val = min(min_val, np.nanmin(values)) # Use min of value or value - error
        max_val = max(max_val, np.nanmax(values)) # Use max of value or value + error

        range_val = max_val - min_val
        
        if range_val > 0:
            ax.set_ylim(max(0, min_val - range_val * 0.1), max_val + range_val * 0.25)
        else:
            # Handle cases with no range (e.g., all values are the same or only one value)
            buffer = max(0.1 * abs(max_val), 0.1) if not np.isnan(max_val) else 0.1
            ax.set_ylim(max(0, min_val - buffer), max_val + buffer * 1.5) # Increased buffer for labels
            if np.isnan(max_val) and np.isnan(min_val): # If all values are NaN
                ax.set_ylim(0, 1)


plt.tight_layout()
plt.savefig('trend_summary.png', dpi=300)
print("Saved: trend_summary.png")
plt.close(fig_trend)

# ================================================================
# SUMMARY TABLES
# ================================================================
# Export detailed summary statistics to CSV files for further analysis and documentation.
# Includes both absolute measurements and normalized precipitate density metrics.
print("\n" + "=" * 70)
print("COMPARATIVE SUMMARY")
print("=" * 70)

summary_data = []
for res in all_results:
    sph = res['sphericity'][~np.isnan(res['sphericity'])]
    rnd = res['roundness'][~np.isnan(res['roundness'])]

    summary_data.append({
        'Stage': res['label'],
        'Detected': res['total_detected'],
        'Analyzed': res['analyzed'],
        'Area Fraction': res['area_fraction'],
        'Mean Volume (nmA3)': np.mean(res['volumes_nm3']),
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

# Normalized statistics
print("\n" + "=" * 70)
print("NORMALIZED STATISTICS (per A�mA�)")
print("=" * 70)

norm_data = []
for res in all_results:
    area_um2 = res['slice_area_nm2'] / 1e6

    norm_data.append({
        'Stage': res['label'],
        'Precipitates per A�mA�': res['analyzed'] / area_um2,
        'I3\' Area Fraction': res['area_fraction'],
        'Mean Spacing (nm)': np.mean(res['nearest_neighbor_nm']) if len(res['nearest_neighbor_nm']) > 0 else np.nan,
    })

norm_df = pd.DataFrame(norm_data)
norm_df.to_csv('comparison_normalized.csv', index=False)
print("\nSaved: comparison_normalized.csv")
print("\n" + norm_df.to_string(index=False))

print("\n" + "=" * 70)
print("CUBE-TO-RAFT ANALYSIS COMPLETE")
print("=" * 70)
print("Generated files:")
print("  - slice_comparison.png")
print("  - comparison_morphology.png")
print("  - comparison_sphericity_roundness.png")
print("  - trend_summary.png")
print("  - comparison_summary.csv")
print("  - comparison_normalized.csv")
print("=" * 70)
