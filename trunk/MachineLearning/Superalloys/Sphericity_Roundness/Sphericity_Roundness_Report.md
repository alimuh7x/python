# Sphericity and Roundness Analysis (fast_rs) - 2D Slice

## Overview

This module performs advanced morphological analysis of cuboidal $\gamma'$ precipitates in Ni-based superalloys using the `fast_rs` library, which implements Wadell's definitions of sphericity and roundness.

Given a phase-fraction field stored in a VTK file (`PF_Initial.vts`), the script `FastRS_Feature.py` extracts a single 2D slice (256×256) from the middle of the 3D volume and calculates per-precipitate sphericity and roundness metrics alongside morphological and spatial descriptors.

**Note**: This is a 2D slice analysis for demonstration purposes, enabling fast processing (~1-2 minutes) compared to full 3D analysis (1-3 hours).

## Methodology: Wadell Sphericity and Roundness

### fast_rs Library

![Fast sphericity and roundness concept](fast-sphericity-and-roundness-Image.png){ align=right width=45% }

The [fast_rs library](https://github.com/PaPieta/fast_rs) provides efficient calculation of Wadell sphericity and roundness for 3D objects:

**Wadell Sphericity ($\Psi$)**:
$$
\Psi = \frac{d_{\text{sphere}}}{d_{\text{circumsphere}}}
$$

where $d_{\text{sphere}}$ is the diameter of a sphere with the same volume as the object, and $d_{\text{circumsphere}}$ is the diameter of the smallest sphere that can circumscribe the object.

**Wadell Roundness ($R$)**:
$$
R = \frac{\sum_{i=1}^{n} r_i}{n \cdot r_{\text{max}}}
$$

where $r_i$ are the radii of curvature at surface points, and $r_{\text{max}}$ is the maximum inscribed sphere radius.

### Implementation Notes

Due to memory constraints when processing large 3D volumes (256³ voxels), we implement a per-precipitate analysis strategy:

1. **Connected Component Labeling**: Identify individual precipitates using scipy.ndimage
2. **Bounding Box Extraction**: Extract each precipitate into a minimal bounding box
3. **Individual Processing**: Calculate sphericity and roundness for each precipitate separately
4. **Feature Aggregation**: Combine results with morphological and spatial statistics

This approach avoids the ~256 GiB memory requirement of processing the entire volume at once.

## Domain and Input Data

- Grid spacing: $dx = 30\,\text{nm}$
- Full volume mesh size: $256 \times 256 \times 256$
- **Analyzed 2D slice**: $256 \times 256$ (extracted from z=128, middle of volume)
- Physical slice size: $7680 \times 7680\,\text{nm}^2$ ($7.68 \times 7.68\,\mu\text{m}^2$)
- Total voxels in slice: $65\,536$
- Phase field: `PhaseFraction_1` (order parameter for the $\gamma'$ phase)
- Binary segmentation: voxels with $\phi > 0.5$ are classified as $\gamma'$
- Voxel area (2D): $dx^2 = 900\,\text{nm}^2$

## Global Phase Statistics

The binary 2D phase field is used to compute global descriptors of the $\gamma'$ population:

- Total precipitates detected in slice: **120**
- Precipitates analyzed (size filter $\geq 10$ voxels): **118**
- Area fraction of $\gamma'$ in slice: **0.703** (70.3% of the slice area)

## Per-Precipitate Morphology

For each individual precipitate (connected component above the size threshold), the script computes:

- **Volume $V$** in $\text{nm}^3$ and voxel count
- **Aspect ratio** based on the bounding-box edge lengths

**Equivalent spherical diameter $D_\text{eq}$ (nm)**

$D_\text{eq}$ is the diameter of a sphere having the same volume $V$ as the precipitate (volume-equivalent size).

$$
D_\text{eq} = \left(\frac{6V}{\pi}\right)^{1/3}
$$

**Wadell Sphericity $\Psi$**

Calculated using the fast_rs library. Sphericity measures how closely a particle resembles a perfect sphere, with values ranging from 0 to 1.

**Wadell Roundness $R$**

Calculated using the fast_rs library. Roundness quantifies the smoothness of particle corners and edges, independent of overall shape.

!!! info "Understanding Sphericity vs Roundness"

    **Sphericity** and **Roundness** are distinct shape descriptors:

    | Property | Sphericity ($\Psi$) | Roundness ($R$) |
    |----------|---------------------|-----------------|
    | Definition | Ratio of equivalent sphere diameter to circumscribed sphere | Average corner/edge curvature |
    | Perfect sphere | 1.0 | 1.0 |
    | Perfect cube | ~0.806 | Low (sharp corners) |
    | Rounded cube | ~0.806 (unchanged) | High (smooth corners) |
    | Needle/rod | Very low | Can be high if ends are rounded |

    **For γ' precipitates:**

    - **Low sphericity** indicates deviation from equiaxed morphology (cuboidal, plate-like shapes)
    - **Low roundness** indicates sharp corners/edges typical of faceted crystallographic interfaces
    - Both metrics are expected to be significantly less than 1.0 for coherent $\gamma'$ precipitates that minimize interfacial energy along {100} planes

    **References:**

    - [fast_rs: Fast Sphericity & Roundness](https://github.com/PaPieta/fast_rs)
    - [Wadell, H. (1935). Volume, Shape, and Roundness of Quartz Particles](https://www.jstor.org/stable/30058011)
    - [Sphericity - Wikipedia](https://en.wikipedia.org/wiki/Sphericity)

## Spatial Statistics

### Nearest-Neighbor Distribution

Precipitate centroids are computed in physical units (nm), and a KD-tree is used to evaluate the distance to the nearest neighbor for each precipitate.

- Mean nearest-neighbor distance: **620.0 nm**
- Standard deviation: **112.9 nm**

### Summary Statistics (2D Slice)

- Mean volume (area × thickness): **$1.05 \times 10^7\,\text{nm}^3$** (~**390 voxels**)
- Mean equivalent diameter: **261.4 nm**
- Mean aspect ratio: **1.74**
- Sphericity and roundness: Successfully calculated for most precipitates (some NaN for highly elongated shapes)

## Results Visualization

### Morphology Feature Distributions

![Morphology features](morphology_features.png)

The morphology features plot shows six histograms displaying the distribution of key precipitate characteristics:

1. **Volume Distribution** (top-left): Shows the range of precipitate volumes in nm³
2. **Equivalent Diameter Distribution** (top-center): Distribution of volume-equivalent sphere diameters
3. **Aspect Ratio Distribution** (top-right): Bounding box aspect ratios showing shape anisotropy
4. **Sphericity Distribution** (bottom-left): Wadell sphericity values calculated by fast_rs
5. **Roundness Distribution** (bottom-center): Wadell roundness values showing corner/edge smoothness
6. **Nearest Neighbor Distribution** (bottom-right): Spatial distribution of precipitate spacing

### Sphericity vs Roundness Correlation

![Sphericity vs Roundness](sphericity_vs_roundness.png)

The scatter plot shows the relationship between sphericity and roundness for all analyzed precipitates, with points colored by precipitate volume. This visualization reveals:

- **Sphericity** (x-axis): Measures deviation from a perfect sphere (shape compactness)
- **Roundness** (y-axis): Quantifies corner and edge sharpness
- **Color scale**: Indicates precipitate volume, allowing identification of size-dependent shape characteristics

The distribution shows that these two metrics are independent - precipitates can have similar sphericity but different roundness values, demonstrating the value of measuring both properties.

## Output Files

The analysis generates the following files in the `Sphericity_Roundness` directory:

- `precipitate_features.csv` – per-precipitate features including:
  - `label_id`: Precipitate identifier
  - `volume_nm3`: Volume in nm³
  - `volume_voxels`: Volume in voxels
  - `equiv_diameter_nm`: Equivalent spherical diameter
  - `aspect_ratio`: Bounding box aspect ratio
  - `sphericity_wadell`: Wadell sphericity (fast_rs)
  - `roundness_wadell`: Wadell roundness (fast_rs)
  - `nearest_neighbor_nm`: Nearest-neighbor distance

- `global_summary.csv` – single-row summary of global statistics
- `morphology_features.png` – 6-panel histogram showing:
  - Volume distribution
  - Equivalent diameter distribution
  - Aspect ratio distribution
  - Sphericity distribution (Wadell)
  - Roundness distribution (Wadell)
  - Nearest-neighbor distance distribution

- `sphericity_vs_roundness.png` – scatter plot of sphericity vs roundness colored by precipitate volume

## Usage

```bash
cd MachineLearning/Superalloys/Sphericity_Roundness
/home/alimuh7x/myenv/bin/python3 FastRS_Feature.py
```

Make sure that `PF_Initial.vts` is present in the same directory and contains the phase-field variable `PhaseFraction_1` on a $256^3$ grid with $dx = 30\,\text{nm}$.

## Applications

- Quantifying $\gamma'$ morphology using Wadell metrics (more rigorous than simple geometric approximations)
- Comparing precipitate shape evolution across heat-treatment conditions
- Validating phase-field model outputs against experimental tomographic data
- Providing standardized feature vectors for machine-learning models
- Distinguishing between shape anisotropy (low sphericity) and surface roughness (low roundness)

## Comparison with Standard Sphericity Calculation

The `Cuboid_Feature.py` script uses a surface-area based sphericity approximation:

$$
\Psi_{\text{approx}} = \frac{\pi^{1/3}(6V)^{2/3}}{S}
$$

This approach has limitations:

- Uses total $\gamma'$ surface area rather than per-precipitate surface
- Less accurate for complex morphologies
- Cannot distinguish roundness from sphericity

The fast_rs library provides:

- Per-precipitate Wadell sphericity and roundness
- More rigorous definitions based on inscribed/circumscribed spheres
- Separate quantification of shape (sphericity) and corner sharpness (roundness)

## Performance Considerations

Processing ~1500 precipitates individually takes significant time (estimated 1-3 hours depending on system).

The per-precipitate approach trades computational time for memory efficiency, enabling analysis on standard workstations rather than requiring HPC resources.

## References

- [fast_rs GitHub Repository](https://github.com/PaPieta/fast_rs)
- Wadell, H. (1935). "Volume, Shape, and Roundness of Quartz Particles." *Journal of Geology*, 43(3), 250-280.
- Krumbein, W. C. (1941). "Measurement and Geological Significance of Shape and Roundness of Sedimentary Particles." *Journal of Sedimentary Petrology*, 11(2), 64-72.
