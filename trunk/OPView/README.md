# OPView - Pure JavaScript VTK.js Standalone Viewer

A modern, offline-capable browser-based VTK visualization application built with **VTK.js** and **JavaScript**. Convert your phase-field simulation data into interactive, GPU-accelerated 3D visualizations.

**No Python server required. No build step. No dependencies. Just open `index.html` in your browser.**

## 🚀 Quick Start

### Option 1: Direct Browser Access
```bash
# Navigate to the OPView folder
cd /path/to/OPView

# Open in your browser (works with any HTTP server)
python3 -m http.server 8000

# Visit: http://localhost:8000/index.html
```

### Option 2: Local File System
Simply open `index.html` directly in your browser:
```bash
open index.html  # macOS
start index.html  # Windows
xdg-open index.html  # Linux
```

**Note:** For full File System Access API support (folder loading), use a local HTTP server.

---

## 📋 Features

### Core Visualization
- ✅ **GPU-Accelerated Rendering** - VTK.js ImageMapper + WebGL
- ✅ **Multiple Colormaps** - Coolwarm, Viridis, Plasma, Aqua-Fire, Blue-White-Red, Grayscale, Inferno
- ✅ **Interactive Controls**
  - Pan, zoom, rotate
  - Dynamic range selection (min/max inputs)
  - Slice navigation (0-N slices)
  - Palette switching
  - View reset

### Data Analysis
- ✅ **Real-time Histograms** - Canvas-based, no Python required
- ✅ **Line Scan Profiles** - Extract 1D traces from 2D slices
- ✅ **Statistics Display** - Min, max, mean, std deviation
- ✅ **Scalar Field Selection** - Switch between multiple datasets

### File Handling
- ✅ **Folder Loading** - File System Access API for VTK file discovery
- ✅ **VTK Format Support** - .vtk, .vti, .vtu, .vtr, .vts
- ✅ **Automatic Metadata Extraction** - Scalar fields, dimensions, bounds
- ✅ **Multi-Simulation Comparison** - Side-by-side viewing (expandable)

### UI/UX
- ✅ **Responsive Layout** - Preserves original Dash design
- ✅ **Tabbed Interface** - Phase Field, Composition, Mechanics, Plasticity
- ✅ **Professional Styling** - Modern glassmorphism design
- ✅ **Export Functionality** - Screenshot as PNG

---

## 📁 Project Structure

```
OPView/
├── index.html                 # Main HTML entry point
├── style.css                  # Preserved from original Dash app
├── README.md                  # This file
├── js/
│   ├── app.js                # Main application orchestrator
│   ├── viewer.js             # VTK.js viewer + ImageMapper
│   ├── loader.js             # File System Access API + VTK parser
│   ├── histogram.js          # Canvas-based histogram/line-scan
│   ├── colormap.js           # LUT management + color palettes
│   └── utils.js              # Helper functions
└── assets/
    ├── OP_Logo.png
    ├── OP_Logo_main.png
    ├── bar-chart.png
    ├── color-scale.png
    ├── Reset.png
    ├── download.png
    ├── plus.png
    ├── Horizontal.png
    └── Vertical.png
```

---

## 🎯 Architecture Overview

### Data Flow
```
User Opens Folder
    ↓
File System Access API (loader.js)
    ↓
VTK File Detection & Parsing (loader.js)
    ↓
vtkImageData Creation (viewer.js)
    ↓
VTK.js ImageMapper Rendering (viewer.js)
    ↓
Interactive Visualization + Analysis
```

### Component Responsibilities

#### **index.html**
- Main layout structure matching original Dash UI
- Sidebar navigation with analysis topic tabs
- Dynamic content area for dataset viewers
- Asset references and script imports

#### **app.js** (Orchestrator)
- Application state management
- Tab/panel rendering
- Event listener attachment
- Test data loading
- Folder integration

#### **viewer.js** (Visualization Engine)
- `VTKViewer` class: VTK.js wrapper
- ImageMapper + ImageSlice setup
- Slice navigation (0-N)
- Palette switching
- Range/threshold updates
- Export functionality

#### **loader.js** (Data I/O)
- `VTKLoader` class: File system integration
- Folder picker (File System Access API)
- VTK file detection (recursively)
- Header parsing for metadata
- Test dataset generation

#### **histogram.js** (Analysis)
- `HistogramGenerator` class: Canvas-based visualization
- Histogram generation & drawing
- Line scan extraction & plotting
- Statistics computation
- Palette-aware coloring

#### **colormap.js** (Color Management)
- `ColorMapManager` class: Palette management
- VTK.js LUT creation
- Multiple preset colormaps
- Colorbar visualization
- Plotly colorscale conversion

#### **utils.js** (Utilities)
- Number formatting (scientific notation)
- Color parsing
- DOM element creation
- Statistics computation
- Event debouncing
- Toast notifications

---

## 🎮 Usage Guide

### Loading VTK Data

#### Method 1: File System Access API (Recommended)
```javascript
// Click "📁 Open Folder" button in top-right
// Select a folder containing VTK files
// App automatically detects .vtk, .vti, .vtu, .vtr, .vts files
// Scalar fields populate in dropdowns
```

#### Method 2: Test Data (Built-in)
```javascript
// App auto-loads test dataset on startup
// 128×128×128 synthetic 3D data
// Two scalar fields for testing
```

#### Method 3: Programmatic (Future Python Backend)
```javascript
// Placeholder for fetch('/api/load-slice')
// Allows server-side VTK processing
```

### Controlling Visualization

#### Scalar Field Selection
```html
<!-- Dropdown populated with detected fields -->
<select class="scalar-select">
    <option value="PhaseFields">Phase Field</option>
    <option value="Interfaces">Interfaces</option>
    <option value="PhaseFraction_0">Phase Fraction</option>
</select>
```

#### Range / Threshold Control
```html
<input type="number" class="range-min" placeholder="Min">
<input type="number" class="range-max" placeholder="Max">
<button class="reset-btn">Reset View</button>
```

#### Slice Navigation
```html
<input type="range" class="slice-slider" min="0" max="127">
<input type="number" class="slice-input" value="64">
```

#### Color Palette
```html
<select class="palette-select">
    <option value="coolwarm">Cool-Warm</option>
    <option value="viridis">Viridis</option>
    <option value="plasma">Plasma</option>
    <option value="aqua-fire">Aqua-Fire</option>
</select>
```

#### Histogram & Analysis
- Canvas displays live histogram of current slice
- Adjustable bin count (10-100)
- Auto-updating statistics (min, max, mean, std)

---

## 🔧 Configuration

### Modify Color Palettes
Edit `js/colormap.js` → `ColorMapManager.initializePresets()`:

```javascript
'custom-palette': {
    label: 'My Palette',
    colors: [
        [0.0, [0.0, 0.0, 1.0]],  // Blue at min
        [0.5, [1.0, 1.0, 1.0]],  // White at mid
        [1.0, [1.0, 0.0, 0.0]]   // Red at max
    ]
}
```

### Adjust Rendering Resolution
Edit `js/viewer.js` → `VTKViewer.initialize()`:

```javascript
// Change interpolation resolution
const resolution = 512; // Higher = slower but smoother
```

### Modify Tab Configuration
Edit `js/app.js` → `OPViewApp.initializeTabConfigs()`:

```javascript
{
    id: 'custom-analysis',
    label: 'Custom Analysis',
    datasets: [
        {
            id: 'custom-data',
            label: 'Custom Data',
            scalars: [
                { label: 'Field 1', array: 'array_name' }
            ]
        }
    ]
}
```

---

## 🔌 Backend Integration (Future)

The app is designed to support Python backend for heavy analysis:

### 1. Expose Backend Functions

```javascript
// In app.js, add:
async function sendSliceToBackend(sliceData) {
    const response = await fetch('/api/process-slice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sliceData)
    });
    return response.json();
}

async function requestMask(sliceIndex) {
    const response = await fetch(`/api/generate-mask/${sliceIndex}`);
    return response.json();
}
```

### 2. Setup FastAPI Backend

```python
# backend/main.py
from fastapi import FastAPI
import numpy as np

app = FastAPI()

@app.post("/api/process-slice")
async def process_slice(data: dict):
    # Heavy analysis here
    return {"result": ...}

@app.get("/api/generate-mask/{index}")
async def generate_mask(index: int):
    # ML model inference
    return {"mask": ...}
```

### 3. Run Both Simultaneously

```bash
# Terminal 1: VTK.js viewer
python3 -m http.server 8000

# Terminal 2: FastAPI backend
python3 -m uvicorn backend.main:app --port 8001

# Visit http://localhost:8000 → uses /api → FastAPI :8001
```

---

## 🌐 Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| VTK.js Rendering | ✅ | ✅ | ✅ | ✅ |
| File System Access API | ✅ 88+ | ⏳ | ❌ | ✅ 88+ |
| Canvas Histograms | ✅ | ✅ | ✅ | ✅ |
| Local File Access | ✅ | ✅ | ✅ | ✅ |

**Firefox Note:** Use fallback file upload dialog or local HTTP server

---

## 🐛 Troubleshooting

### "Module not defined" error
- Ensure VTK.js CDN is loaded before other scripts
- Check browser console for CDN 404 errors

### File System Access API not working
- Use Chrome/Edge 88+
- Ensure running on localhost or HTTPS
- Use local HTTP server: `python3 -m http.server`

### Viewer not rendering
- Check that VTK files have valid POINT_DATA/CELL_DATA
- Verify scalar array names in UI match VTK file
- Check browser console for WebGL errors

### Performance issues
- Reduce interpolation resolution in `viewer.js`
- Use smaller datasets for testing
- Close browser tabs to free memory

---

## 📚 VTK.js Integration Details

### Data Structure
```javascript
// vtkImageData structure:
imageData.setDimensions(128, 128, 128);
imageData.setSpacing(1.0, 1.0, 1.0);
imageData.setOrigin(0.0, 0.0, 0.0);

// Add scalar arrays:
imageData.getPointData().addArray(vtkDataArray);
```

### Rendering Pipeline
```javascript
// 1. Create mapper
const mapper = vtk.Rendering.Core.vtkImageMapper.newInstance();
mapper.setInputData(imageData);
mapper.setSlicingMode(2); // Z-axis

// 2. Create actor
const imageSlice = vtk.Rendering.Core.vtkImageSlice.newInstance();
imageSlice.setMapper(mapper);

// 3. Setup LUT (color mapping)
const lut = vtkColorTransferFunction.newInstance();
lut.addRGBPoint(min, r, g, b);
lut.addRGBPoint(max, r, g, b);
imageSlice.getProperty().setLookupTable(lut);

// 4. Render
renderer.addViewProp(imageSlice);
renderer.resetCamera();
renderWindow.render();
```

---

## 🚀 Performance Tips

1. **Reduce histogram bin count** (default 30, min 10)
2. **Use lower resolution for large files** (edit viewer.js)
3. **Cache computed slices** (already implemented)
4. **Lazy-load analysis panels** (future optimization)

---

## 📖 API Reference

### VTKViewer Class

```javascript
// Create viewer
const viewer = new VTKViewer(containerElement, options);

// Load data
viewer.loadImageData(imageData, 'ScalarName', stats);

// Navigation
viewer.setSliceIndex(64);
viewer.setScalarRange(0, 1);
viewer.setPalette('viridis');

// UI
viewer.resetView();
const stats = viewer.getStatistics();

// Export
const blob = await viewer.exportPNG();
```

### ColorMapManager Class

```javascript
// Get available palettes
const palettes = colorMapManager.getAvailablePalettes();

// Create LUT
const lut = colorMapManager.createLUT('coolwarm', min, max);

// Draw colorbar
colorMapManager.drawColorbar(canvas, 'viridis', min, max, 'Title');
```

### HistogramGenerator Class

```javascript
// Generate histogram
const { edges, counts, stats } = HistogramGenerator.generateHistogram(data, 30);

// Draw on canvas
HistogramGenerator.drawHistogram(canvas, data, {
    bins: 30,
    title: 'Histogram',
    palette: 'coolwarm'
});

// Line scan
HistogramGenerator.drawLineScan(canvas, {
    values: [...],
    direction: 'horizontal'
});
```

### VTKLoader Class

```javascript
// Select folder
const dirHandle = await vtkLoader.selectFolder();

// Get VTK files
const files = await vtkLoader.getVTKFiles(dirHandle);

// Read file
const buffer = await vtkLoader.readFile(fileHandle);

// Parse metadata
const meta = vtkLoader.parseVTKFile(buffer, 'file.vti');

// Create test data
const dataset = vtkLoader.createTestDataset(128, 128, 128);
```

---

## 🤝 Contributing

To extend functionality:

1. **Add new colormap** → `colormap.js` presets
2. **Add new analysis tool** → `histogram.js` methods
3. **Add backend support** → Create `/api/` endpoints
4. **Improve parser** → Enhance `loader.js` VTK parser
5. **Custom shaders** → Extend `viewer.js` rendering

---

## 📝 License

This project converts the Dash/Plotly OPView application to pure JavaScript + VTK.js for offline use.

---

## 🆘 Support

- **VTK.js Docs**: https://kitware.github.io/vtk-js/
- **File System Access API**: https://web.dev/file-system-access/
- **Canvas API**: https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API

---

## ✨ Roadmap

- [ ] Binary VTK file reader (currently ASCII only)
- [ ] Time-series animation support
- [ ] Multi-fold comparison mode
- [ ] Custom shader support
- [ ] Volume rendering (3D isosurface)
- [ ] Machine learning inference integration
- [ ] Measurement tools (distance, angle)
- [ ] Data export (CSV, VTK)

---

**Version**: 1.0.0
**Last Updated**: 2025-12-10
**Status**: Fully Functional ✅

Open `index.html` in your browser to get started!
