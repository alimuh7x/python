/**
 * VTK.js Viewer - Core visualization using ImageMapper and ImageSlice
 */

class VTKViewer {
    constructor(containerElement, options = {}) {
        this.container = containerElement;
        this.options = {
            width: 600,
            height: 600,
            palette: 'coolwarm',
            ...options
        };

        this.renderer = null;
        this.renderWindow = null;
        this.openglRenderWindow = null;
        this.interactor = null;
        this.canvas = null;
        this.imageSlice = null;
        this.imageData = null;
        this.currentSliceIndex = 0;
        this.sliceAxis = 2; // Z-axis by default
        this.currentScalarName = null;
        this.scalarRange = [0, 1];
        this.stats = null;
        this.initialized = false;

        // Delay initialization slightly to ensure container is in DOM
        setTimeout(() => this.initialize(), 10);
    }

    /**
     * Initialize VTK.js viewer
     */
    initialize() {
        const viewerId = this.container.id || 'unknown';

        log('log', `[VTK Viewer ${viewerId}] Initialize called`);

        if (!this.container) {
            log('error', `[VTK Viewer ${viewerId}] Container element not found`);
            return;
        }

        // Check container is in DOM
        if (!document.body.contains(this.container)) {
            log('warn', `[VTK Viewer ${viewerId}] Container not in DOM tree yet, will retry...`);
            setTimeout(() => this.initialize(), 50);
            return;
        }

        log('log', `[VTK Viewer ${viewerId}] Container is in DOM`);

        if (!window.vtk) {
            log('error', `[VTK Viewer ${viewerId}] VTK.js library not loaded`);
            return;
        }

        log('log', `[VTK Viewer ${viewerId}] VTK.js is available`);

        try {
            // Get container dimensions
            const rect = this.container.getBoundingClientRect();
            const width = Math.max(rect.width, this.options.width);
            const height = Math.max(rect.height, this.options.height);

            log('log', `[VTK ${viewerId}] Container size: ${rect.width}x${rect.height}, Using: ${width}x${height}`);

            // Create render window + renderer
            log('log', `[VTK ${viewerId}] Creating render window...`);
            this.renderWindow = vtk.Rendering.Core.vtkRenderWindow.newInstance();
            log('log', `[VTK ${viewerId}] ✓ Render window created`);

            this.renderer = vtk.Rendering.Core.vtkRenderer.newInstance({ background: [1, 1, 1] });
            log('log', `[VTK ${viewerId}] ✓ Renderer created`);

            this.renderWindow.addRenderer(this.renderer);
            log('log', `[VTK ${viewerId}] ✓ Renderer added to window`);

            // Prepare canvas container
            log('log', `[VTK ${viewerId}] Creating canvas element (${width}x${height})...`);
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.display = 'block';
            canvas.style.border = '1px solid #ccc';  // Debug: visible border

            // Clear container and add canvas
            this.container.innerHTML = '';
            this.container.appendChild(canvas);
            this.canvas = canvas;

            log('log', `[VTK ${viewerId}] ✓ Canvas created: ${canvas.width}x${canvas.height}`);
            log('log', `[VTK ${viewerId}] Canvas in DOM: ${document.body.contains(canvas)}`);

            // OpenGL render window
            log('log', `[VTK ${viewerId}] Creating OpenGL render window...`);
            this.openglRenderWindow = vtk.Rendering.OpenGL.vtkRenderWindow.newInstance();
            log('log', `[VTK ${viewerId}] ✓ OpenGL window created`);

            this.openglRenderWindow.setContainer(canvas);
            log('log', `[VTK ${viewerId}] ✓ Canvas set as OpenGL container`);

            this.openglRenderWindow.setSize(width, height);
            log('log', `[VTK ${viewerId}] ✓ OpenGL size set to ${width}x${height}`);

            this.renderWindow.addView(this.openglRenderWindow);
            log('log', `[VTK ${viewerId}] ✓ OpenGL view added to render window`);

            // Interactor setup
            log('log', `[VTK ${viewerId}] Creating interactor...`);
            this.interactor = vtk.Rendering.OpenGL.vtkRenderWindowInteractor.newInstance();
            log('log', `[VTK ${viewerId}] ✓ Interactor created`);

            this.interactor.setView(this.openglRenderWindow);
            log('log', `[VTK ${viewerId}] ✓ Interactor view set`);

            this.interactor.initialize();
            log('log', `[VTK ${viewerId}] ✓ Interactor initialized`);

            this.interactor.bindEvents(canvas);
            log('log', `[VTK ${viewerId}] ✓ Events bound to canvas`);

            // Add interactor style
            log('log', `[VTK ${viewerId}] Setting interactor style...`);
            const iStyle = vtk.Interaction.Style.vtkInteractorStyleImage.newInstance();
            this.interactor.setInteractorStyle(iStyle);
            log('log', `[VTK ${viewerId}] ✓ Interactor style set`);

            this.initialized = true;
            log('log', `[VTK ${viewerId}] ✅ VIEWER FULLY INITIALIZED AND READY ✅`);
        } catch (error) {
            log('error', `[VTK ${viewerId}] Error initializing VTK viewer: ${error.message}`);
            log('error', `[VTK ${viewerId}] Stack: ${error.stack}`);
            this.initialized = false;
        }
    }

    /**
     * Load image data into viewer
     * @param {vtkImageData} imageData - VTK image data
     * @param {string} scalarName - Name of scalar field to display
     * @param {object} stats - {min, max, mean, std}
     */
    loadImageData(imageData, scalarName = 'data', stats = null) {
        const viewerId = this.container.id || 'unknown';

        try {
            log('log', `[VTK ${viewerId}] loadImageData called for: ${scalarName}`);

            if (!this.initialized) {
                log('warn', `[VTK ${viewerId}] Viewer not yet initialized (${this.initialized}). Will retry...`);
                setTimeout(() => this.loadImageData(imageData, scalarName, stats), 100);
                return;
            }

            log('log', `[VTK ${viewerId}] Viewer initialized, proceeding...`);

            if (!imageData) {
                log('error', `[VTK ${viewerId}] No image data provided`);
                return;
            }

            log('log', `[VTK ${viewerId}] Image data provided`);

            if (!this.renderer) {
                log('error', `[VTK ${viewerId}] Renderer not available!`);
                log('error', `[VTK ${viewerId}] Initialized: ${this.initialized}, RenderWindow: ${this.renderWindow}`);
                this.renderFallbackVisualization(imageData, scalarName, stats);
                return;
            }

            log('log', `[VTK ${viewerId}] Renderer is available`);

            this.imageData = imageData;
            this.currentScalarName = scalarName;
            this.stats = stats;

            const dims = imageData.getDimensions();
            log('log', `[VTK ${viewerId}] Loading image data: ${scalarName}, dimensions: ${dims[0]}x${dims[1]}x${dims[2]}`);

            // Get scalar range
            if (stats) {
                this.scalarRange = [stats.min, stats.max];
                log('log', `[VTK ${viewerId}] Using provided stats range: [${stats.min}, ${stats.max}]`);
            } else {
                const scalars = imageData.getPointData().getScalars();
                if (scalars) {
                    this.scalarRange = scalars.getRange();
                    log('log', `[VTK ${viewerId}] Computed range from scalars: [${this.scalarRange[0]}, ${this.scalarRange[1]}]`);
                } else {
                    log('warn', `[VTK ${viewerId}] No scalars found in point data`);
                }
            }

            log('log', `[VTK ${viewerId}] Scalar range: [${this.scalarRange[0]}, ${this.scalarRange[1]}]`);

            // Create mapper
            log('log', `[VTK ${viewerId}] Creating image mapper...`);
            const mapper = vtk.Rendering.Core.vtkImageMapper.newInstance();
            mapper.setInputData(imageData);
            mapper.setSliceAtFocalPoint(true);
            mapper.setSlicingMode(this.sliceAxis);
            log('log', `[VTK ${viewerId}] ✓ Mapper created`);

            // Create image slice
            log('log', `[VTK ${viewerId}] Creating image slice actor...`);
            this.imageSlice = vtk.Rendering.Core.vtkImageSlice.newInstance();
            this.imageSlice.setMapper(mapper);
            log('log', `[VTK ${viewerId}] ✓ Image slice created`);

            // Setup LUT (lookup table) and color mapping
            log('log', `[VTK ${viewerId}] Creating color transfer function (palette: ${this.options.palette})...`);
            const property = this.imageSlice.getProperty();
            const lut = colorMapManager.createLUT(this.options.palette, this.scalarRange[0], this.scalarRange[1]);
            property.setLookupTable(lut);
            log('log', `[VTK ${viewerId}] ✓ LUT set`);

            // Set color window and level
            const level = (this.scalarRange[0] + this.scalarRange[1]) / 2;
            const window = this.scalarRange[1] - this.scalarRange[0];
            property.setColorLevel(level, window);
            log('log', `[VTK ${viewerId}] ✓ Color level set (level: ${level}, window: ${window})`);

            // Add to renderer
            log('log', `[VTK ${viewerId}] Adding actor to renderer...`);
            this.renderer.removeAllViewProps();
            this.renderer.addViewProp(this.imageSlice);
            log('log', `[VTK ${viewerId}] ✓ Actor added to renderer`);

            log('log', `[VTK ${viewerId}] Resetting camera...`);
            this.renderer.resetCamera();
            log('log', `[VTK ${viewerId}] ✓ Camera reset`);

            // Render
            log('log', `[VTK ${viewerId}] Calling renderWindow.render()...`);
            this.renderWindow.render();
            log('log', `[VTK ${viewerId}] ✅ RENDERING COMPLETE - Image should now be visible ✅`);
        } catch (error) {
            log('error', `[VTK ${viewerId}] Error loading image data: ${error.message}`);
            log('error', `[VTK ${viewerId}] Stack: ${error.stack}`);
            log('warn', `[VTK ${viewerId}] Falling back to canvas visualization...`);
            this.renderFallbackVisualization(imageData, scalarName, stats);
        }
    }

    /**
     * Fallback visualization using canvas if VTK fails
     */
    renderFallbackVisualization(imageData, scalarName, stats) {
        try {
            // Clear container
            this.container.innerHTML = '';

            // Create a canvas for fallback visualization
            const canvas = document.createElement('canvas');
            canvas.width = 400;
            canvas.height = 400;
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.border = '1px solid #ccc';
            this.container.appendChild(canvas);

            const ctx = canvas.getContext('2d');
            const { width, height } = canvas;

            // Draw a colorful gradient test pattern
            const gradW = 50;
            const gradH = 50;

            for (let y = 0; y < height; y += gradH) {
                for (let x = 0; x < width; x += gradW) {
                    const r = Math.floor((x / width) * 255);
                    const g = Math.floor((y / height) * 255);
                    const b = 128;
                    ctx.fillStyle = `rgb(${r},${g},${b})`;
                    ctx.fillRect(x, y, gradW, gradH);
                }
            }

            // Add info text
            ctx.fillStyle = '#fff';
            ctx.strokeStyle = '#000';
            ctx.lineWidth = 3;
            ctx.font = 'bold 16px Arial';
            ctx.strokeText(`${scalarName}`, 10, 30);
            ctx.fillText(`${scalarName}`, 10, 30);

            ctx.font = '12px Arial';
            ctx.strokeText(`Fallback Canvas`, 10, 55);
            ctx.fillText(`Fallback Canvas`, 10, 55);

            log('log', '✓ Fallback canvas visualization rendered');
        } catch (error) {
            log('error', 'Fallback visualization error:', error);
        }
    }

    /**
     * Update slice index
     * @param {number} index
     */
    setSliceIndex(index) {
        if (!this.imageSlice) return;

        const extent = this.imageData.getExtent();
        const axisExtent = [extent[0], extent[2], extent[4]];
        const maxIndex = [extent[1] - extent[0], extent[3] - extent[2], extent[5] - extent[4]][this.sliceAxis];

        index = Math.max(0, Math.min(index, maxIndex));
        this.currentSliceIndex = index;

        const mapper = this.imageSlice.getMapper();
        mapper.setSlice(index);

        this.renderWindow.render();
    }

    /**
     * Update color palette
     * @param {string} paletteName
     */
    setPalette(paletteName) {
        if (!this.imageSlice) return;

        this.options.palette = paletteName;
        const property = this.imageSlice.getProperty();
        const lut = colorMapManager.createLUT(paletteName, this.scalarRange[0], this.scalarRange[1]);
        property.setLookupTable(lut);

        this.renderWindow.render();
    }

    /**
     * Update color/value range
     * @param {number} min
     * @param {number} max
     */
    setScalarRange(min, max) {
        if (!this.imageSlice) return;

        this.scalarRange = [min, max];
        const property = this.imageSlice.getProperty();

        // Update LUT with new range
        const lut = colorMapManager.createLUT(this.options.palette, min, max);
        property.setLookupTable(lut);

        // Update window/level
        const level = (min + max) / 2;
        const window = max - min;
        property.setColorLevel(level, window);

        this.renderWindow.render();
    }

    /**
     * Reset camera to fit data
     */
    resetView() {
        if (this.renderer) {
            this.renderer.resetCamera();
            this.renderWindow.render();
        }
    }

    /**
     * Export current view as PNG
     * @returns {Promise<Blob>}
     */
    async exportPNG() {
        return new Promise((resolve) => {
            const canvas = this.canvas;
            canvas.toBlob(blob => {
                resolve(blob);
            }, 'image/png');
        });
    }

    /**
     * Dispose of viewer resources
     */
    dispose() {
        if (this.interactor) {
            this.interactor.delete();
        }
        if (this.renderWindow) {
            this.renderWindow.delete();
        }
    }

    /**
     * Get current image data statistics
     * @returns {object}
     */
    getStatistics() {
        return this.stats || {
            min: this.scalarRange[0],
            max: this.scalarRange[1],
            mean: (this.scalarRange[0] + this.scalarRange[1]) / 2,
            std: 0
        };
    }
}

/**
 * Create synthetic vtkImageData for testing
 * @param {object} dataset
 * @returns {vtkImageData}
 */
function createImageDataFromDataset(dataset) {
    try {
        if (!window.vtk) {
            log('error', 'VTK.js not loaded');
            return null;
        }

        const imageData = vtk.Common.DataModel.vtkImageData.newInstance();

        // Set dimensions
        if (dataset.dimensions) {
            imageData.setDimensions(...dataset.dimensions);
            log('log', `Set image dimensions: ${dataset.dimensions}`);
        }

        // Set spacing (default 1.0)
        imageData.setSpacing(1.0, 1.0, 1.0);

        // Set origin (default 0.0)
        imageData.setOrigin(0.0, 0.0, 0.0);

        // Add scalars
        if (dataset.data) {
            let scalarCount = 0;
            Object.entries(dataset.data).forEach(([name, data]) => {
                try {
                    const scalars = vtk.Common.Core.vtkDataArray.newInstance({
                        name: name,
                        numberOfComponents: 1,
                        values: data
                    });

                    if (!imageData.getPointData().getScalars()) {
                        imageData.getPointData().setScalars(scalars);
                    } else {
                        imageData.getPointData().addArray(scalars);
                    }
                    scalarCount++;
                    log('log', `Added scalar array: ${name} (${data.length} values)`);
                } catch (e) {
                    log('warn', `Failed to add scalar ${name}:`, e);
                }
            });
            log('log', `Total scalar arrays added: ${scalarCount}`);
        }

        return imageData;
    } catch (error) {
        log('error', 'Error creating image data:', error);
        return null;
    }
}

/**
 * Get scalar field names from image data
 * @param {vtkImageData} imageData
 * @returns {Array<string>}
 */
function getScalarFieldNames(imageData) {
    const fields = [];
    if (imageData && imageData.getPointData()) {
        const arrays = imageData.getPointData().getArrays();
        arrays.forEach(array => {
            if (array.getName()) {
                fields.push(array.getName());
            }
        });
    }
    return fields;
}

/**
 * Extract 2D slice from 3D image data
 * @param {vtkImageData} imageData
 * @param {number} sliceIndex
 * @param {number} axis - 0=X, 1=Y, 2=Z
 * @returns {object} {values, x, y, stats}
 */
function extractSlice2D(imageData, sliceIndex, axis = 2) {
    const extent = imageData.getExtent();
    const dims = [
        extent[1] - extent[0] + 1,
        extent[3] - extent[2] + 1,
        extent[5] - extent[4] + 1
    ];

    let sliceData = [];
    let width, height;

    if (axis === 2) { // Z slice
        width = dims[0];
        height = dims[1];
        const scalars = imageData.getPointData().getScalars().getData();

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const idx = sliceIndex * (width * height) + y * width + x;
                if (idx < scalars.length) {
                    sliceData.push(scalars[idx]);
                }
            }
        }
    } else if (axis === 1) { // Y slice
        width = dims[0];
        height = dims[2];
        const scalars = imageData.getPointData().getScalars().getData();

        for (let z = 0; z < height; z++) {
            for (let x = 0; x < width; x++) {
                const idx = z * (dims[0] * dims[1]) + sliceIndex * dims[0] + x;
                if (idx < scalars.length) {
                    sliceData.push(scalars[idx]);
                }
            }
        }
    } else { // X slice
        width = dims[1];
        height = dims[2];
        const scalars = imageData.getPointData().getScalars().getData();

        for (let z = 0; z < height; z++) {
            for (let y = 0; y < width; y++) {
                const idx = z * (dims[0] * dims[1]) + y * dims[0] + sliceIndex;
                if (idx < scalars.length) {
                    sliceData.push(scalars[idx]);
                }
            }
        }
    }

    const stats = computeStats(sliceData);

    return {
        values: sliceData,
        width,
        height,
        stats
    };
}
