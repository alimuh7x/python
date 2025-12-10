# OPView - Quick Start Guide

## ⚡ 30-Second Setup

### Step 1: Open Terminal
```bash
cd /mnt/e/RUB/OpenPhase/python/trunk/OPView
```

### Step 2: Start Local Server
```bash
# Python 3
python3 -m http.server 8000

# OR Python 2
python -m SimpleHTTPServer 8000
```

### Step 3: Open Browser
Visit: **http://localhost:8000**

---

## 🎯 What You See

1. **Header** - OPView title + Folder selector + Documentation link
2. **Left Sidebar** - Analysis topics (Phase Field, Composition, Mechanics, Plasticity)
3. **Main Panel** - Dataset visualization blocks with:
   - **Controls** - Scalar field dropdown, range inputs, palette selector, slice slider
   - **Viewer** - VTK.js 3D visualization (currently showing test data)
   - **Analysis** - Histogram of current slice

---

## 📂 Load Your Own Data

### Method 1: File System Access API (Chrome/Edge only)
1. Click **"📁 Open Folder"** button (top right)
2. Select folder containing .vti, .vts, .vtk files
3. App auto-detects files and populates dropdowns

### Method 2: Without File System Access (All Browsers)
1. Edit `js/app.js` → `loadTestData()` function
2. Create `vtkImageData` with your data
3. Call `viewer.loadImageData(imageData, 'ScalarName', stats)`

---

## 🎮 Basic Controls

| Control | Action |
|---------|--------|
| **Scalar Field** | Switch between data arrays |
| **Range Min/Max** | Set color scale limits |
| **Palette** | Change colormap (Coolwarm, Viridis, etc.) |
| **Slice Slider** | Navigate through Z-slices |
| **Reset Button** | Reset view to initial state |

---

## 🔴 Common Issues

### Issue: "File System Access API not supported"
**Solution**: Use Chrome/Edge 88+, or use local HTTP server

### Issue: "Viewer shows blank white area"
**Solution**: Check browser console (F12) for errors. VTK.js needs WebGL.

### Issue: "Histogram not updating"
**Solution**: Ensure scalar field is properly loaded. Check console logs.

---

## 📚 Full Documentation

See **README.md** for:
- Complete feature list
- Architecture overview
- API reference
- Backend integration guide
- Troubleshooting

---

## 🚀 Next Steps

1. **Load your data** → Click "📁 Open Folder"
2. **Explore visualizations** → Select different scalar fields
3. **Analyze slices** → Use histogram + statistics
4. **Export results** → Screenshot button (when implemented)
5. **Add backend** → See Backend Integration in README.md

---

## 🆘 Need Help?

1. Open browser DevTools (F12)
2. Check Console tab for error messages
3. Review README.md → Troubleshooting section
4. Check VTK.js docs: https://kitware.github.io/vtk-js/

---

**Enjoy visualizing your phase-field simulations! 🎉**
