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
        if (!this.container) {
            log('error', 'Container element not found');
            return;
        }

        if (!window.vtk) {
            log('error', 'VTK.js library not loaded');
            return;
        }

        try {
            // Get container dimensions
            const rect = this.container.getBoundingClientRect();
            const width = Math.max(rect.width, this.options.width);
            const height = Math.max(rect.height, this.options.height);

            log('log', `Creating viewer with size: ${width}x${height}`);

            // Create render window + renderer
            this.renderWindow = vtk.Rendering.Core.vtkRenderWindow.newInstance();
            this.renderer = vtk.Rendering.Core.vtkRenderer.newInstance({ background: [1, 1, 1] });
            this.renderWindow.addRenderer(this.renderer);

            // Prepare canvas container
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            canvas.style.display = 'block';
            this.container.appendChild(canvas);
            this.canvas = canvas;

            // OpenGL render window
            this.openglRenderWindow = vtk.Rendering.OpenGL.vtkRenderWindow.newInstance();
            this.openglRenderWindow.setContainer(canvas);
            this.openglRenderWindow.setSize(width, height);
            this.renderWindow.addView(this.openglRenderWindow);

            // Interactor setup
            this.interactor = vtk.Rendering.OpenGL.vtkRenderWindowInteractor.newInstance();
            this.interactor.setView(this.openglRenderWindow);
            this.interactor.initialize();
            this.interactor.bindEvents(canvas);

            // Add interactor style
            const iStyle = vtk.Interaction.Style.vtkInteractorStyleImage.newInstance();
            this.interactor.setInteractorStyle(iStyle);

            this.initialized = true;
            log('log', '✓ VTK Viewer initialized successfully');
        } catch (error) {
            log('error', 'Error initializing VTK viewer:', error);
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
        try {
            if (!this.initialized) {
                log('warn', 'Viewer not yet initialized. Will retry...');
                setTimeout(() => this.loadImageData(imageData, scalarName, stats), 100);
                return;
            }

            if (!imageData) {
                log('error', 'No image data provided');
                return;
            }

            if (!this.renderer) {
                log('error', 'Renderer not initialized');
                return;
            }

            this.imageData = imageData;
            this.currentScalarName = scalarName;
            this.stats = stats;

            log('log', `Loading image data: ${scalarName}, dimensions: ${imageData.getDimensions()}`);

            // Get scalar range
            if (stats) {
                this.scalarRange = [stats.min, stats.max];
            } else {
                const scalars = imageData.getPointData().getScalars();
                if (scalars) {
                    this.scalarRange = scalars.getRange();
                }
            }

            log('log', `Scalar range: [${this.scalarRange[0]}, ${this.scalarRange[1]}]`);

            // Create mapper
            const mapper = vtk.Rendering.Core.vtkImageMapper.newInstance();
            mapper.setInputData(imageData);
            mapper.setSliceAtFocalPoint(true);
            mapper.setSlicingMode(this.sliceAxis);

            // Create image slice
            this.imageSlice = vtk.Rendering.Core.vtkImageSlice.newInstance();
            this.imageSlice.setMapper(mapper);

            // Setup LUT (lookup table) and color mapping
            const property = this.imageSlice.getProperty();
            const lut = colorMapManager.createLUT(this.options.palette, this.scalarRange[0], this.scalarRange[1]);
            property.setLookupTable(lut);

            // Set color window and level
            const level = (this.scalarRange[0] + this.scalarRange[1]) / 2;
            const window = this.scalarRange[1] - this.scalarRange[0];
            property.setColorLevel(level, window);

            // Add to renderer
            this.renderer.removeAllViewProps();
            this.renderer.addViewProp(this.imageSlice);
            this.renderer.resetCamera();

            // Render
            this.renderWindow.render();
            log('log', `✓ Image data loaded and rendered successfully`);
        } catch (error) {
            log('error', 'Error loading image data:', error);
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
