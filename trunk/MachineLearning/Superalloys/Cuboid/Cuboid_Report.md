# Cuboid Precipitate Analysis

## Overview

This module analyzes 3D phase-field simulations of cuboidal $\gamma'$ precipitates in Ni-based superalloys.
Given a phase-fraction field stored in a VTK file (`PF_Initial.vts`), the script `Cuboid_Feature.py`
extracts global, morphological, spatial, and topological descriptors of the precipitate population,
and saves both plots and CSV summaries for further post-processing or machine-learning workflows.

## Domain and Input Data

- Grid spacing: $dx = 30\,\text{nm}$
- Mesh size: $256 \times 256 \times 256$ (total voxels: $16\,777\,216$)
- Physical domain: $7680 \times 7680 \times 7680\,\text{nm}^3$ ($7.68^3\,\mu\text{m}^3$)
- Phase field: `PhaseFraction_1` (order parameter for the $\gamma'$ phase)
- Binary segmentation: voxels with $\phi > 0.5$ are classified as $\gamma'$
- Voxel volume: $dx^3 = 27\,000\,\text{nm}^3$

## Global Phase Statistics

The binary phase field is used to compute global descriptors of the $\gamma'$ population:

- Total precipitates detected: **1503**
- Precipitates analyzed (size filter $\geq 20$ voxels): **1236**
- Volume fraction of $\gamma'$: **0.6459** (64.59% of the domain)
- Euler characteristic of the $\gamma'$ network: **1322**

The Euler characteristic provides a topological measure of connectivity and the number of isolated
regions and tunnels in the precipitate network.

## Per-Precipitate Morphology

![Morphology feature distributions](morphology_features.png){ align=right width=45% }

For each individual precipitate (connected component above the size threshold), the script computes:

- **Volume $V$** in $\text{nm}^3$ and voxel count
- **Aspect ratio** based on the bounding-box edge lengths

**Equivalent spherical diameter $D_\text{eq}$ (nm)**

$D_\text{eq}$ is the diameter of a sphere having the same volume $V$ as the precipitate (volume-equivalent size).

$$
D_\text{eq} = \left(\frac{6V}{\pi}\right)^{1/3}
$$

**Sphericity $\Psi$**

$\Psi$ is the ratio of the surface area of that equivalent sphere to the actual surface area $S$ (1 for a perfect sphere, lower for faceted or irregular shapes).

$$
\Psi = \dfrac{\pi^{1/3}(6V)^{2/3}}{S}
$$

!!! info "Understanding Sphericity (Wadell Definition)"

    **Sphericity values for common shapes:**

    | Shape | Sphericity (Ψ) | Description |
    |-------|----------------|-------------|
    | Sphere | 1.000 | Perfect sphericity |
    | Cylinder (h=d) | 0.874 | Equal height and diameter |
    | Cube | 0.806 | Regular hexahedron |
    | Regular tetrahedron | 0.671 | Four equilateral triangular faces |

    **Visual comparison:**
    ```
    Sphere (Ψ=1.0)          Cube (Ψ=0.81)         Cuboidal γ' (Ψ≈0.001)
         ●●●                   ┌───┐                    ┌─────────┐
       ●●   ●●                 │   │                    │         │
      ●●     ●●                │   │                    └─────────┘
      ●●     ●●                │   │                   (highly elongated)
       ●●   ●●                 └───┘
         ●●●
    ```

    **For γ' precipitates in Ni-based superalloys:**

    The extremely low sphericity (≈0.0008) indicates highly faceted, cuboidal morphology.
    This is typical of coherent precipitates that minimize interfacial energy by aligning
    along preferred {100} crystallographic planes, resulting in elongated box-like shapes
    rather than compact equiaxed forms.

    **References:**

    - [Wadell Sphericity - Wikipedia](https://en.wikipedia.org/wiki/Sphericity)
    - [Sphericity calculation methods](https://www.sciencedirect.com/topics/engineering/sphericity)
    - [Particle shape analysis tools](https://github.com/geosharma/sphericity_and_roundness)

Summary statistics for this dataset:

- Mean volume: **$2.367 \times 10^8\,\text{nm}^3$** (~**8766.9** voxels)
- Mean equivalent diameter: **702.03 nm**
- Mean aspect ratio: **2.38**
- Total $\gamma'$ surface area: **$2.272 \times 10^9\,\text{nm}^2$**
- Mean sphericity: **0.0008**

The figure `morphology_features.png` provides histograms of these morphology metrics
for the entire precipitate population.

## Spatial Statistics

### Nearest-Neighbor Distribution

![Nearest-neighbor distribution](NN_distribution.png){ align=right width=45% }

Precipitate centroids are computed in physical units (nm), and a KD-tree is used to
evaluate the distance to the nearest neighbor for each precipitate. The resulting
distribution characterizes the mean spacing between cuboids:

- Mean nearest-neighbor distance: **612.35 nm**
- Standard deviation: **107.64 nm**

These statistics are visualized in `NN_distribution.png`.

### Pair Correlation Function $g(r)$

![Pair correlation g(r)](g_r.png){ align=right width=45% }

Pair correlation $g(r)$ is computed by counting precipitate pairs in shells $[r, r+\Delta r]$
and normalizing by the expected count for number density $\rho$:

$$
g(r) = \frac{1}{N \rho\, V_\text{shell}(r)}
\sum_{i=1}^{N} \sum_{j \neq i}
\Theta\big(|\mathbf{r}_i - \mathbf{r}_j| - r\big)\,
\Theta\big(r + \Delta r - |\mathbf{r}_i - \mathbf{r}_j|\big)
$$

- Bin width: $\Delta r = 30\,\text{nm}$
- Maximum radius: $r_\text{max} = 1800\,\text{nm}$

$V_\text{shell}(r)$ is the spherical-shell volume; $\Theta$ is the Heaviside step function. `g_r.png` shows the result.

## Output Files

The analysis generates the following files in the `Cuboid` directory:

- `NN_distribution.png` – histogram of nearest-neighbor distances
- `g_r.png` – pair correlation function $g(r)$ vs. distance
- `morphology_features.png` – histograms of volume, aspect ratio, sphericity, and equivalent diameter
- `precipitate_features.csv` – per-precipitate features
  (`volume_nm3, volume_voxels, aspect_ratio, sphericity, equiv_diameter_nm, nearest_neighbor_nm`)
- `pair_correlation.csv` – radial positions and $g(r)$ (`r_nm, g_r`)
- `global_summary.csv` – single-row summary of global statistics

## Usage

```bash
cd MachineLearning/Superalloys/Cuboid
python3 Cuboid_Feature.py
```

Make sure that `PF_Initial.vts` is present in the same directory and contains the
phase-field variable `PhaseFraction_1` on a $256^3$ grid with $dx = 30\,\text{nm}$.

## Applications

- Quantifying $\gamma'$ morphology in phase-field simulations of superalloys
- Calibrating phase-field models against experimental tomographic data
- Providing feature vectors for machine-learning models (e.g. microstructure–property links)
- Comparing precipitate statistics across heat-treatment conditions or alloy chemistries
