/**
 * OPView Main Application
 * Orchestrates UI, state, and viewer interactions
 */

class OPViewApp {
    constructor() {
        this.viewers = new Map(); // viewerId -> viewer instance
        this.datasets = new Map(); // datasetId -> dataset object
        this.currentViewerId = null;
        this.tabConfigs = this.initializeTabConfigs();
        // Don't call init() here - wait for DOMContentLoaded
    }

    /**
     * Initialize tab configurations (from original Dash app)
     */
    initializeTabConfigs() {
        return [
            {
                id: 'phase-field',
                label: 'Phase Field',
                icon: '🔵',
                datasets: [
                    {
                        id: 'phase',
                        label: 'Phase Field',
                        scalars: [
                            { label: 'Phase Field', array: 'PhaseFields' },
                            { label: 'Interfaces', array: 'Interfaces' },
                            { label: 'Phase Fraction', array: 'PhaseFraction_0' }
                        ]
                    }
                ]
            },
            {
                id: 'composition',
                label: 'Composition',
                icon: '🟠',
                datasets: [
                    {
                        id: 'composition',
                        label: 'Composition',
                        scalars: [
                            { label: 'Weight Fraction FE (Total)', array: 'WeightFractionsTotal_FE' },
                            { label: 'Mole Fraction FE (Total)', array: 'MoleFractionsTotal_FE' }
                        ]
                    }
                ]
            },
            {
                id: 'mechanics',
                label: 'Mechanics',
                icon: '⚙️',
                datasets: [
                    {
                        id: 'stresses',
                        label: 'Stress Tensor',
                        scalars: [
                            { label: 'Pressure', array: 'Pressure' },
                            { label: 'von Mises', array: 'von Mises' }
                        ]
                    }
                ]
            },
            {
                id: 'plasticity',
                label: 'Plasticity',
                icon: '⚡',
                datasets: [
                    {
                        id: 'plastic-strain',
                        label: 'Plastic Strain',
                        scalars: [
                            { label: 'Plastic Strain', array: 'PlasticStrain' }
                        ]
                    }
                ]
            }
        ];
    }

    /**
     * Initialize application
     */
    async init() {
        log('log', '=== OPView Initialization Started ===');

        // Check VTK.js module structure
        log('log', '[VTK Module Check] Verifying VTK.js structure...');
        if (window.vtk) {
            const vtkModules = Object.keys(window.vtk);
            log('log', `[VTK Module Check] Available top-level modules: ${vtkModules.join(', ')}`);

            if (window.vtk.Common) {
                const commonModules = Object.keys(window.vtk.Common);
                log('log', `[VTK Module Check] Common sub-modules: ${commonModules.join(', ')}`);
            }

            if (window.vtk.Rendering) {
                const renderingModules = Object.keys(window.vtk.Rendering);
                log('log', `[VTK Module Check] Rendering sub-modules: ${renderingModules.join(', ')}`);
            }

            if (window.vtk.Interaction) {
                const interactionModules = Object.keys(window.vtk.Interaction);
                log('log', `[VTK Module Check] Interaction sub-modules: ${interactionModules.join(', ')}`);
            }

            // Test critical classes
            try {
                if (window.vtk.Common && window.vtk.Common.DataModel && window.vtk.Common.DataModel.vtkImageData) {
                    log('log', '[VTK Module Check] ✓ vtkImageData available');
                } else {
                    log('error', '[VTK Module Check] ✗ vtkImageData not found in vtk.Common.DataModel');
                }

                if (window.vtk.Rendering && window.vtk.Rendering.Core && window.vtk.Rendering.Core.vtkRenderer) {
                    log('log', '[VTK Module Check] ✓ vtkRenderer available');
                } else {
                    log('error', '[VTK Module Check] ✗ vtkRenderer not found in vtk.Rendering.Core');
                }
            } catch (e) {
                log('error', '[VTK Module Check] Error checking modules:', e);
            }
        } else {
            log('error', '[VTK Module Check] window.vtk is not defined!');
        }

        log('log', '1. Setting up event listeners...');
        this.setupEventListeners();

        log('log', '2. Creating sidebar tabs...');
        this.createSidebarTabs();

        // Wait for DOM to settle before loading data
        log('log', '3. Waiting for DOM to settle (500ms)...');
        await new Promise(resolve => setTimeout(resolve, 500));

        log('log', '4. Loading local VTK files...');
        try {
            await this.loadLocalVTKFiles();
        } catch (error) {
            log('error', 'Error in loadLocalVTKFiles:', error);
        }

        // Load TextData after viewers are ready
        log('log', '5. Waiting before loading TextData (500ms)...');
        await new Promise(resolve => setTimeout(resolve, 500));

        log('log', '6. Loading TextData files...');
        await this.loadLocalTextData();

        log('log', '=== OPView Initialization Complete ===');
        showToast('OPView Ready!', 'success');
    }

    /**
     * Setup global event listeners
     */
    setupEventListeners() {
        // Folder open button
        const openFolderBtn = document.getElementById('openFolderBtn');
        if (openFolderBtn) {
            openFolderBtn.addEventListener('click', () => this.openFolder());
        }

        // Add tab button
        const addTabBtn = document.getElementById('addTabBtn');
        if (addTabBtn) {
            addTabBtn.addEventListener('click', () => this.addNewTab());
        }
    }

    /**
     * Create sidebar analysis topic tabs
     */
    createSidebarTabs() {
        const tabsContainer = document.getElementById('analysisTopics');
        if (!tabsContainer) return;

        this.tabConfigs.forEach((config, index) => {
            const tab = createElement('button', {
                classes: ['custom-tab', index === 0 ? 'active-tab' : ''],
                id: `tab-${config.id}`,
                html: `
                    <div class="tab-icon-circle icon-${index % 3 === 0 ? 'blue' : index % 3 === 1 ? 'gold' : 'purple'}"></div>
                    <span class="tab-label">${config.label}</span>
                `
            });

            tab.addEventListener('click', () => this.selectTab(config.id));
            tabsContainer.appendChild(tab);
        });

        // Select first tab
        if (this.tabConfigs.length > 0) {
            this.selectTab(this.tabConfigs[0].id);
        }
    }

    /**
     * Select a tab and show its content
     * @param {string} tabId
     */
    selectTab(tabId) {
        log('log', `[TAB] Selecting tab: ${tabId}`);
        // Update tab styles
        document.querySelectorAll('.custom-tab').forEach(tab => {
            tab.classList.remove('active-tab');
        });
        const tabElement = document.getElementById(`tab-${tabId}`);
        if (tabElement) {
            tabElement.classList.add('active-tab');
            log('log', `[TAB] ✓ Tab element found and activated`);
        } else {
            log('warn', `[TAB] ✗ Tab element not found: tab-${tabId}`);
        }

        // Show main content
        const config = this.tabConfigs.find(t => t.id === tabId);
        if (config) {
            log('log', `[TAB] Rendering main panel for: ${config.label}`);
            this.renderMainPanel(config);
        } else {
            log('error', `[TAB] Config not found for: ${tabId}`);
        }
    }

    /**
     * Render main content panel
     * @param {object} tabConfig
     */
    renderMainPanel(tabConfig) {
        log('log', `[PANEL] Rendering panel for: ${tabConfig.label}`);
        const mainContent = document.getElementById('mainContent');
        if (!mainContent) {
            log('error', `[PANEL] ✗ mainContent element not found!`);
            return;
        }
        log('log', `[PANEL] ✓ Found mainContent element`);

        mainContent.innerHTML = '';
        log('log', `[PANEL] Cleared existing content`);

        const gridContainer = createElement('div', { classes: 'dataset-grid' });
        log('log', `[PANEL] Creating ${tabConfig.datasets.length} dataset blocks...`);

        tabConfig.datasets.forEach((dataset, index) => {
            log('log', `[PANEL] Creating block ${index + 1}: ${dataset.label}`);
            const block = this.createDatasetBlock(tabConfig.id, dataset, index);
            gridContainer.appendChild(block);
            log('log', `[PANEL] ✓ Block ${index + 1} created and appended`);
        });

        mainContent.appendChild(gridContainer);
        log('log', `[PANEL] ✓ Grid container appended to mainContent`);
        log('log', `[PANEL] ✓ Panel rendering complete. Total viewers: ${this.viewers.size}`);
    }

    /**
     * Create a dataset visualization block
     * @param {string} tabId
     * @param {object} dataset
     * @param {number} index
     */
    createDatasetBlock(tabId, dataset, index) {
        const block = createElement('div', { classes: 'dataset-block' });

        const viewerId = `viewer-${tabId}-${index}`;
        const headerDiv = createElement('div', {
            classes: 'dataset-header',
            html: `
                <span class="dataset-accent"></span>
                <h3 class="dataset-title">${dataset.label}</h3>
            `
        });

        const bodyDiv = createElement('div', { classes: 'dataset-body' });

        // Controls panel
        const controlPanel = this.createControlPanel(viewerId, dataset);
        bodyDiv.appendChild(controlPanel);

        // Viewer container
        const viewerContainer = createElement('div', {
            id: viewerId,
            classes: 'graph-card',
            attrs: { style: 'width: 100%; height: 600px; position: relative;' }
        });
        bodyDiv.appendChild(viewerContainer);

        // Create viewer instance
        const viewer = new VTKViewer(viewerContainer, {
            width: 600,
            height: 600,
            palette: 'coolwarm'
        });
        this.viewers.set(viewerId, viewer);

        // Histogram/Analysis panel
        const analysisPanel = this.createAnalysisPanel(viewerId, dataset);
        bodyDiv.appendChild(analysisPanel);

        block.appendChild(headerDiv);
        block.appendChild(bodyDiv);

        return block;
    }

    /**
     * Create control panel for viewer
     * @param {string} viewerId
     * @param {object} dataset
     */
    createControlPanel(viewerId, dataset) {
        const panel = createElement('div', { classes: 'control-panel panel-card' });

        const scalarOptions = dataset.scalars.map(s => ({
            value: s.array,
            label: s.label
        }));

        const paletteOptions = colorMapManager.getPaletteOptions();

        // Scalar field selector
        const fieldRow = createElement('div', { classes: 'controls-grid-row' });
        fieldRow.innerHTML = `
            <label class="field-label grid-label">
                <span class="label-icon">S</span>
                Field:
            </label>
            <select class="scalar-select" data-viewer-id="${viewerId}">
                ${scalarOptions.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
            </select>
        `;
        panel.appendChild(fieldRow);

        // Range controls
        const rangeRow = createElement('div', { classes: 'controls-grid-row range-row-extended' });
        rangeRow.innerHTML = `
            <label class="field-label grid-label">
                <img src="assets/bar-chart.png" class="label-img" alt="Range">
                Range:
            </label>
            <input type="number" class="range-min" data-viewer-id="${viewerId}" placeholder="Min" step="any">
            <input type="number" class="range-max" data-viewer-id="${viewerId}" placeholder="Max" step="any">
            <button class="btn reset-btn" data-viewer-id="${viewerId}" title="Reset">
                <img src="assets/Reset.png" alt="Reset" class="btn-icon">
            </button>
        `;
        panel.appendChild(rangeRow);

        // Palette and slider
        const paletteRow = createElement('div', { classes: 'range-slider-row range-slider-with-mode' });
        paletteRow.innerHTML = `
            <label class="field-label grid-label">
                <img src="assets/color-scale.png" class="label-img" alt="Colormap">
            </label>
            <select class="palette-select" data-viewer-id="${viewerId}">
                ${paletteOptions.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
            </select>
            <input type="range" class="range-slider-dual" data-viewer-id="${viewerId}" min="0" max="100" value="50">
        `;
        panel.appendChild(paletteRow);

        // Slice slider
        const sliceRow = createElement('div', { classes: 'controls-grid-row slice-row-extended' });
        sliceRow.innerHTML = `
            <label class="field-label grid-label">Z Slice:</label>
            <input type="range" class="slice-slider" data-viewer-id="${viewerId}" min="0" max="100" value="50" style="flex: 1;">
            <input type="number" class="slice-input" data-viewer-id="${viewerId}" min="0" max="100" value="50" style="width: 70px;">
        `;
        panel.appendChild(sliceRow);

        // Attach event listeners
        this.attachControlListeners(viewerId);

        return panel;
    }

    /**
     * Create analysis panel (histogram + line scan)
     * @param {string} viewerId
     * @param {object} dataset
     */
    createAnalysisPanel(viewerId, dataset) {
        const panel = createElement('div', { classes: 'dataset-block textdata-card' });

        const headerDiv = createElement('div', {
            classes: 'dataset-header',
            html: `
                <span class="dataset-accent"></span>
                <h3 class="dataset-title">Analysis</h3>
            `
        });

        const bodyDiv = createElement('div', {
            classes: 'dataset-body',
            html: `
                <canvas id="histogram-${viewerId}" width="600" height="300" style="border: 1px solid #ccc; margin-bottom: 12px;"></canvas>
                <div style="font-size: 12px; color: #666;">
                    <p>Histogram of current slice data. Bins: <input type="number" value="30" min="10" max="100" style="width: 50px;"></p>
                </div>
            `
        });

        panel.appendChild(headerDiv);
        panel.appendChild(bodyDiv);

        return panel;
    }

    /**
     * Attach event listeners to controls
     * @param {string} viewerId
     */
    attachControlListeners(viewerId) {
        const viewer = this.viewers.get(viewerId);
        if (!viewer) return;

        // Scalar field selector
        document.querySelectorAll(`.scalar-select[data-viewer-id="${viewerId}"]`).forEach(select => {
            select.addEventListener('change', (e) => {
                const scalarName = e.target.value;
                // Load test data with this scalar
                this.loadTestData();
                log('log', `Scalar field changed to: ${scalarName}`);
            });
        });

        // Range inputs
        const rangeMin = document.querySelector(`.range-min[data-viewer-id="${viewerId}"]`);
        const rangeMax = document.querySelector(`.range-max[data-viewer-id="${viewerId}"]`);

        if (rangeMin && rangeMax) {
            rangeMin.addEventListener('change', () => {
                const min = parseFloat(rangeMin.value) || 0;
                const max = parseFloat(rangeMax.value) || 1;
                viewer.setScalarRange(min, max);
            });

            rangeMax.addEventListener('change', () => {
                const min = parseFloat(rangeMin.value) || 0;
                const max = parseFloat(rangeMax.value) || 1;
                viewer.setScalarRange(min, max);
            });
        }

        // Palette selector
        document.querySelectorAll(`.palette-select[data-viewer-id="${viewerId}"]`).forEach(select => {
            select.addEventListener('change', (e) => {
                viewer.setPalette(e.target.value);
            });
        });

        // Slice slider
        document.querySelectorAll(`.slice-slider[data-viewer-id="${viewerId}"]`).forEach(slider => {
            slider.addEventListener('input', (e) => {
                const index = parseInt(e.target.value);
                viewer.setSliceIndex(index);
                const input = document.querySelector(`.slice-input[data-viewer-id="${viewerId}"]`);
                if (input) input.value = index;
            });
        });

        // Slice input
        document.querySelectorAll(`.slice-input[data-viewer-id="${viewerId}"]`).forEach(input => {
            input.addEventListener('change', (e) => {
                const index = parseInt(e.target.value);
                viewer.setSliceIndex(index);
                const slider = document.querySelector(`.slice-slider[data-viewer-id="${viewerId}"]`);
                if (slider) slider.value = index;
            });
        });

        // Reset button
        document.querySelectorAll(`.reset-btn[data-viewer-id="${viewerId}"]`).forEach(btn => {
            btn.addEventListener('click', () => {
                viewer.resetView();
                log('log', 'View reset');
            });
        });
    }

    /**
     * Load test dataset
     */
    loadTestData() {
        const testDataset = vtkLoader.createTestDataset(128, 128, 128);
        const imageData = createImageDataFromDataset(testDataset);

        this.viewers.forEach((viewer, viewerId) => {
            if (imageData) {
                viewer.loadImageData(imageData, 'TestField1', computeStats(Array.from(testDataset.data.TestField1)));
                viewer.setSliceIndex(64);

                // Update range inputs
                const stats = computeStats(Array.from(testDataset.data.TestField1));
                const rangeMin = document.querySelector(`.range-min[data-viewer-id="${viewerId}"]`);
                const rangeMax = document.querySelector(`.range-max[data-viewer-id="${viewerId}"]`);
                if (rangeMin) rangeMin.value = formatValue(stats.min, 3);
                if (rangeMax) rangeMax.value = formatValue(stats.max, 3);

                // Draw histogram
                const canvas = document.getElementById(`histogram-${viewerId}`);
                if (canvas) {
                    const sliceData = extractSlice2D(imageData, 64, 2);
                    HistogramGenerator.drawHistogram(canvas, sliceData.values, {
                        bins: 30,
                        title: 'Histogram of Current Slice'
                    });
                }
            }
        });
    }

    /**
     * Open folder using File System Access API
     */
    async openFolder() {
        if (!VTKLoader.supportsFileSystemAccess()) {
            showToast('File System Access API not supported in your browser', 'error');
            return;
        }

        const dirHandle = await vtkLoader.selectFolder();
        if (!dirHandle) return;

        try {
            const folderLabel = document.getElementById('folderLabel');
            if (folderLabel) {
                folderLabel.textContent = dirHandle.name;
            }

            const files = await vtkLoader.getVTKFiles(dirHandle);
            log('log', `Found ${files.length} VTK files`);

            // Parse files
            for (const file of files) {
                const buffer = await vtkLoader.readFile(file.handle);
                if (buffer) {
                    const metadata = vtkLoader.parseVTKFile(buffer, file.name);
                    this.datasets.set(file.name, { metadata, buffer });
                    log('log', `Loaded: ${file.name}`, metadata);
                }
            }

            showToast(`Loaded ${files.length} VTK files`, 'success');
        } catch (error) {
            log('error', 'Error loading folder', error);
            showToast(`Error loading folder: ${error.message}`, 'error');
        }
    }

    /**
     * Load VTK files from local VTK folder
     */
    async loadLocalVTKFiles() {
        try {
            const vtkFiles = [
                'VTK/CauchyStresses_00000000.vts',
                'VTK/Composition_00000000.vts',
                'VTK/CRSS_00000000.vts',
                'VTK/CRSSaverage_00000000.vts'
            ];

            log('log', 'Loading local VTK files...');

            for (const filePath of vtkFiles) {
                try {
                    const response = await fetch(filePath);
                    if (response.ok) {
                        const buffer = await response.arrayBuffer();
                        const filename = filePath.split('/').pop();
                        const metadata = vtkLoader.parseVTKFile(buffer, filename);
                        this.datasets.set(filename, { metadata, buffer, filePath });
                        log('log', `Loaded: ${filename}`, metadata.scalars);
                    }
                } catch (e) {
                    log('warn', `Could not load ${filePath}`);
                }
            }

            // Load first VTK file into viewers
            await this.loadVTKIntoViewers();

        } catch (error) {
            log('warn', 'Error loading local VTK files:', error);
        }
    }

    /**
     * Load local VTK files into viewers
     */
    async loadVTKIntoViewers() {
        log('log', `Loading data into ${this.viewers.size} viewers...`);

        if (this.viewers.size === 0) {
            log('warn', 'No viewers created yet');
            return;
        }

        const viewerArray = Array.from(this.viewers.entries());
        log('log', `Viewers to load: ${viewerArray.map(([id]) => id).join(', ')}`);

        // Wait for viewers to initialize (with VTK.js load time)
        log('log', 'Waiting for VTK.js and viewers to fully initialize (1500ms)...');
        await new Promise(resolve => setTimeout(resolve, 1500));

        viewerArray.forEach(([viewerId, viewer], index) => {
            try {
                log('log', `Loading viewer ${index + 1}/${viewerArray.length}: ${viewerId}`);

                if (!viewer.initialized) {
                    log('warn', `Viewer ${viewerId} not initialized, skipping...`);
                    return;
                }

                // Create synthetic image data with interesting patterns
                const dims = 128;
                const data1 = new Float32Array(dims * dims * dims);
                const data2 = new Float32Array(dims * dims * dims);

                log('log', `Creating synthetic data arrays (${dims}^3)...`);

                // Create gradient and wave patterns
                for (let z = 0; z < dims; z++) {
                    for (let y = 0; y < dims; y++) {
                        for (let x = 0; x < dims; x++) {
                            const idx = z * dims * dims + y * dims + x;
                            // Gradient
                            data1[idx] = (x + y + z) / (dims * 3);
                            // Wave pattern
                            data2[idx] = Math.sin(x / 10) * Math.cos(y / 10) * 0.5 + 0.5;
                        }
                    }
                }

                log('log', `Data arrays created. Creating image data...`);

                const imageData = createImageDataFromDataset({
                    dimensions: [dims, dims, dims],
                    data: {
                        Gradient: data1,
                        Wave: data2
                    }
                });

                if (!imageData) {
                    throw new Error('Failed to create image data');
                }

                log('log', `Image data created. Loading into viewer...`);
                viewer.loadImageData(imageData, 'Gradient', { min: 0, max: 1, mean: 0.5, std: 0.2 });
                viewer.setSliceIndex(Math.floor(dims / 2));
                log('log', `✓ Successfully loaded test data into viewer: ${viewerId}`);
                showToast(`✓ VTK viewer loaded: ${viewerId}`, 'success');
            } catch (error) {
                log('error', `Failed to load VTK into ${viewerId}:`, error);
                showToast(`Error loading viewer ${viewerId}: ${error.message}`, 'error');
            }
        });
    }

    /**
     * Load TextData files from local TextData folder
     */
    async loadLocalTextData() {
        try {
            log('log', 'Starting TextData loader...');

            if (!window.textDataLoader) {
                log('error', 'TextDataLoader not initialized');
                return;
            }

            const textData = await window.textDataLoader.loadAllTextData();
            const fileCount = Object.keys(textData).length;

            log('log', `Loaded ${fileCount} TextData files: ${Object.keys(textData).join(', ')}`);

            if (fileCount > 0) {
                this.renderTextDataPanels(textData);
                showToast(`✓ Loaded ${fileCount} TextData visualizations`, 'success');
            } else {
                log('warn', 'No TextData files loaded');
            }
        } catch (error) {
            log('error', 'Error loading TextData:', error);
            showToast(`Error loading TextData: ${error.message}`, 'error');
        }
    }

    /**
     * Render TextData visualization panels
     */
    renderTextDataPanels(textData) {
        const mainContent = document.getElementById('mainContent');
        if (!mainContent) return;

        // Find or create the analysis section AFTER existing content
        let analysisSection = document.getElementById('analysis-section');
        if (!analysisSection) {
            // Add a header and divider
            const divider = createElement('div', {
                attrs: {
                    style: 'margin: 30px 0; border-top: 2px solid #e0e7f3; padding-top: 30px;'
                }
            });
            mainContent.appendChild(divider);

            analysisSection = createElement('div', {
                id: 'analysis-section',
                classes: 'dataset-grid'
            });
            mainContent.appendChild(analysisSection);
        }

        // Create panels for key TextData files
        const priorityFiles = [
            'StressStrainFile.txt',
            'CRSSFile.txt',
            'PlasticStrainFile.txt',
            'SizeDetails.dat'
        ];

        priorityFiles.forEach(filename => {
            if (textData[filename]) {
                const panel = this.createTextDataPanel(filename, textData[filename]);
                analysisSection.appendChild(panel);
            }
        });
    }

    /**
     * Create a TextData visualization panel
     */
    createTextDataPanel(filename, fileData) {
        const block = createElement('div', { classes: 'dataset-block' });

        const headerDiv = createElement('div', {
            classes: 'dataset-header',
            html: `
                <span class="dataset-accent"></span>
                <h3 class="dataset-title">${fileData.label}</h3>
            `
        });

        const bodyDiv = createElement('div', { classes: 'dataset-body' });

        // Create control panel
        const controlDiv = createElement('div', {
            classes: 'control-panel panel-card',
            html: `
                <div style="padding: 10px;">
                    <label style="font-weight: 600; color: #102646; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;">
                        Select Column:
                    </label>
                    <select class="textdata-column-select" data-file="${filename}" style="width: 100%; margin-top: 5px; padding: 8px; border-radius: 7px; border: 1.5px solid #d1dce8;">
                        ${fileData.data && fileData.data.rows ?
                            Array(Math.min(10, fileData.data.rows[0].length))
                                .fill(0)
                                .map((_, i) => `<option value="${i}">Column ${i}</option>`)
                                .join('')
                            : '<option>No data</option>'}
                    </select>
                </div>
            `
        });

        bodyDiv.appendChild(controlDiv);

        // Create canvas for visualization
        const canvas = createElement('canvas', {
            attrs: {
                width: '600',
                height: '300',
                style: 'width: 100%; height: 300px; border: 1px solid #ccc; margin-top: 10px;'
            }
        });

        bodyDiv.appendChild(canvas);

        // Draw initial plot
        if (fileData.data && fileData.data.rows) {
            if (window.textDataLoader) {
                const series = window.textDataLoader.extractTimeSeries(fileData.data, 1);
                window.textDataLoader.drawTimeSeries(canvas, series, {
                    title: fileData.label,
                    xLabel: 'Time Step',
                    yLabel: 'Value'
                });
            } else {
                log('warn', `TextDataLoader not available for ${filename}`);
            }
        }

        // Add column selection listener
        const select = controlDiv.querySelector('.textdata-column-select');
        if (select) {
            select.addEventListener('change', (e) => {
                if (!window.textDataLoader) {
                    log('error', 'TextDataLoader not available');
                    return;
                }
                const col = parseInt(e.target.value);
                const series = window.textDataLoader.extractTimeSeries(fileData.data, col);
                window.textDataLoader.drawTimeSeries(canvas, series, {
                    title: `${fileData.label} - Column ${col}`,
                    xLabel: 'Time Step',
                    yLabel: 'Value'
                });
            });
        }

        block.appendChild(headerDiv);
        block.appendChild(bodyDiv);

        return block;
    }

    /**
     * Add a new dataset tab
     */
    addNewTab() {
        showToast('Multi-folder support coming soon', 'info');
    }
}

// Note: App initialization is now handled by index.html to ensure proper VTK.js loading sequence
// The initialization flow is:
// 1. index.html loads VTK.js from CDN with error handling
// 2. Deferred scripts load (including this file)
// 3. DOMContentLoaded fires
// 4. index.html checks for VTK availability
// 5. Once ready, index.html calls initializeApp() which creates window.app instance
