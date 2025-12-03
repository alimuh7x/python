# VTK 2D Slice Viewer

A production-ready interactive Dash application for visualizing VTK files with two-color threshold visualization.

## Features

- Load VTK files (.vtk, .vti, .vtp, .vtr, .vts)
- Automatic detection of 2D/3D data
- Interactive two-color threshold visualization
- Click on heatmap to set threshold
- Customizable colors (Color A for below threshold, Color B for above)
- Slice selection for 3D datasets
- Real-time statistics display
- Reset to initial state

## Installation

### Prerequisites

- Python 3.12 or higher (recommended)
- Windows/Linux/macOS

### Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Generating Sample Data

Generate synthetic VTI test files:

```bash
python sample_data/generate_sample_vti.py
```

This creates:
- `sample_data/sample_3d.vti` - 3D dataset (50x40x30)
- `sample_data/sample_2d.vti` - 2D dataset (100x80)
- `sample_data/phase_field.vti` - Phase field simulation (60x50x40)

## Running the Application

```bash
python app.py
```

Then open your browser to: **http://127.0.0.1:8050**

## Usage

### Controls

**Left Panel:**
- **Color A** - Color for values below threshold (e.g., "blue", "#0000FF", "rgb(0,0,255)")
- **Color B** - Color for values above threshold (e.g., "red", "#FF0000", "rgb(255,0,0)")
- **Threshold Value** - Manual threshold input
- **Slice Index** - Select slice for 3D datasets (Y-axis by default)
- **Reset Button** - Restore initial colors and threshold

**Right Panel:**
- **Heatmap** - Interactive 2D visualization
- **Click anywhere** on the heatmap to set threshold to that scalar value
- **Statistics** - Min, max, mean, std dev, and current threshold

### Color Formats

You can use:
- Color names: `blue`, `red`, `green`, `yellow`, etc.
- Hex codes: `#0000FF`, `#FF0000`
- RGB: `rgb(0, 0, 255)`, `rgb(255, 0, 0)`

### Loading Your Own VTK Files

1. Place your VTK file in the project directory
2. Edit `app.py` line 53:
```python
default_file = 'path/to/your/file.vti'
```
3. Restart the application

## Project Structure

```
Dash/
│
├── app.py                          # Main Dash application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── utils/
│   ├── __init__.py
│   └── vtk_reader.py              # VTK file loading and slicing
│
├── sample_data/
│   ├── generate_sample_vti.py     # Sample data generator
│   ├── sample_3d.vti              # Generated 3D test file
│   ├── sample_2d.vti              # Generated 2D test file
│   └── phase_field.vti            # Generated phase field data
│
└── assets/
    └── style.css                   # Custom CSS styling
```

## Technical Details

### Two-Color Threshold Logic

The application uses Plotly's `zmid` parameter with a custom colorscale:

```python
colorscale = [
    [0.0, colorA],  # Start with Color A
    [0.5, colorA],  # Continue to midpoint
    [0.5, colorB],  # Switch to Color B at midpoint
    [1.0, colorB]   # End with Color B
]
```

- Values < threshold → Color A
- Values ≥ threshold → Color B

### 3D Slicing

For 3D datasets:
- Default axis: Y
- Default slice: Middle slice (Ny // 2)
- Slicing uses PyVista's native slicing functionality
- Data interpolated to regular grid for visualization

### Data Flow

1. **Load VTK** → PyVista reads file
2. **Detect dimensions** → Determine 2D or 3D
3. **Extract slice** → Get 2D data (directly or via slicing)
4. **Interpolate** → Create regular grid using scipy
5. **Visualize** → Plotly heatmap with two-color threshold

## Troubleshooting

### VTK Import Error

If you see `ModuleNotFoundError: No module named 'vtk'`:

1. Ensure you're using Python 3.12 (VTK compatibility issue with 3.14)
2. Reinstall VTK: `pip install --force-reinstall vtk`
3. Check virtual environment is activated

### File Not Found

If sample files are missing:
```bash
python sample_data/generate_sample_vti.py
```

### Port Already in Use

Change the port in `app.py`:
```python
app.run_server(debug=True, host='127.0.0.1', port=8051)  # Change port
```

## Dependencies

- **dash** >= 2.14.0 - Web framework
- **plotly** >= 5.18.0 - Interactive plotting
- **pyvista** >= 0.43.0 - VTK file handling
- **numpy** >= 1.24.0 - Numerical arrays
- **scipy** >= 1.11.0 - Interpolation
- **vtk** >= 9.2.0 - VTK backend

## Future Enhancements

Possible extensions:
- Multiple VTK file support
- Volume rendering mode
- Custom colormap editor
- Export functions (PNG, MP4, GIF)
- Axis selection (X, Y, Z)
- Multiple scalar field selection
- Isosurface extraction

## License

This project is open-source and available for educational and research purposes.

## Contact

For issues or questions, please open an issue in the project repository.
