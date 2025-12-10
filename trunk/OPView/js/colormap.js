/**
 * Colormap and LUT (Lookup Table) management for VTK.js
 */

class ColorMapManager {
    constructor() {
        this.currentPalette = 'coolwarm';
        this.lutCache = {};
        this.presets = this.initializePresets();
    }

    /**
     * Initialize color palette presets
     * @returns {object}
     */
    initializePresets() {
        return {
            'coolwarm': {
                label: 'Cool-Warm',
                colors: [
                    [0.0, [0.2298057, 0.29873814, 0.75367875]],  // Cool (blue)
                    [0.5, [0.865, 0.865, 0.865]],               // White
                    [1.0, [0.70567316, 0.01555616, 0.15003658]] // Warm (red)
                ]
            },
            'viridis': {
                label: 'Viridis',
                colors: [
                    [0.0, [0.267004, 0.004874, 0.329415]],
                    [0.25, [0.282623, 0.140461, 0.469470]],
                    [0.5, [0.253935, 0.265254, 0.529983]],
                    [0.75, [0.206756, 0.371758, 0.553806]],
                    [1.0, [0.993248, 0.906157, 0.143936]]
                ]
            },
            'plasma': {
                label: 'Plasma',
                colors: [
                    [0.0, [0.050383, 0.029803, 0.529975]],
                    [0.25, [0.282623, 0.140461, 0.469470]],
                    [0.5, [0.798216, 0.280180, 0.469470]],
                    [0.75, [0.940015, 0.475741, 0.131979]],
                    [1.0, [0.940015, 0.975255, 0.131979]]
                ]
            },
            'aqua-fire': {
                label: 'Aqua-Fire',
                colors: [
                    [0.0, [0.0, 0.5, 1.0]],      // Aqua/Cyan
                    [0.5, [1.0, 1.0, 1.0]],      // White
                    [1.0, [1.0, 0.0, 0.0]]       // Fire/Red
                ]
            },
            'blue-white-red': {
                label: 'Blue-White-Red',
                colors: [
                    [0.0, [0.0, 0.0, 1.0]],      // Blue
                    [0.5, [1.0, 1.0, 1.0]],      // White
                    [1.0, [1.0, 0.0, 0.0]]       // Red
                ]
            },
            'grayscale': {
                label: 'Grayscale',
                colors: [
                    [0.0, [0.0, 0.0, 0.0]],      // Black
                    [1.0, [1.0, 1.0, 1.0]]       // White
                ]
            },
            'inferno': {
                label: 'Inferno',
                colors: [
                    [0.0, [0.001462, 0.000466, 0.013866]],
                    [0.33, [0.282623, 0.140461, 0.469470]],
                    [0.67, [0.798216, 0.280180, 0.469470]],
                    [1.0, [0.988362, 0.998364, 0.644924]]
                ]
            }
        };
    }

    /**
     * Get available palette names
     * @returns {Array<string>}
     */
    getAvailablePalettes() {
        return Object.keys(this.presets);
    }

    /**
     * Get palette options for dropdown
     * @returns {Array<object>}
     */
    getPaletteOptions() {
        return this.getAvailablePalettes().map(name => ({
            value: name,
            label: this.presets[name].label
        }));
    }

    /**
     * Create VTK.js LUT from palette
     * @param {string} paletteName
     * @param {number} rangeMin
     * @param {number} rangeMax
     * @returns {vtkColorTransferFunction}
     */
    createLUT(paletteName = 'coolwarm', rangeMin = 0, rangeMax = 1) {
        const palette = this.presets[paletteName] || this.presets['coolwarm'];
        const cacheKey = `${paletteName}_${rangeMin}_${rangeMax}`;

        if (this.lutCache[cacheKey]) {
            return this.lutCache[cacheKey];
        }

        const lut = vtk.Rendering.Core.vtkColorTransferFunction.newInstance();
        lut.setValueRange(rangeMin, rangeMax);

        palette.colors.forEach(([position, rgb]) => {
            const value = rangeMin + (rangeMax - rangeMin) * position;
            lut.addRGBPoint(value, rgb[0], rgb[1], rgb[2]);
        });

        this.lutCache[cacheKey] = lut;
        return lut;
    }

    /**
     * Create a 256-color LUT as image data for colorbar visualization
     * @param {string} paletteName
     * @param {number} rangeMin
     * @param {number} rangeMax
     * @returns {Uint8Array}
     */
    createLUTImage(paletteName = 'coolwarm', rangeMin = 0, rangeMax = 1) {
        const palette = this.presets[paletteName] || this.presets['coolwarm'];
        const imageData = new Uint8Array(256 * 4); // RGBA

        for (let i = 0; i < 256; i++) {
            const t = i / 255; // 0-1
            const value = rangeMin + (rangeMax - rangeMin) * t;

            // Find the interpolated color
            let r, g, b;
            const colors = palette.colors;

            // Find surrounding colors
            let lower = colors[0];
            let upper = colors[colors.length - 1];

            for (let j = 0; j < colors.length - 1; j++) {
                if (colors[j][0] <= t && t <= colors[j + 1][0]) {
                    lower = colors[j];
                    upper = colors[j + 1];
                    break;
                }
            }

            // Interpolate
            const range = upper[0] - lower[0];
            const t2 = range > 0 ? (t - lower[0]) / range : 0;
            r = Math.round((lower[1][0] + (upper[1][0] - lower[1][0]) * t2) * 255);
            g = Math.round((lower[1][1] + (upper[1][1] - lower[1][1]) * t2) * 255);
            b = Math.round((lower[1][2] + (upper[1][2] - lower[1][2]) * t2) * 255);

            const idx = i * 4;
            imageData[idx] = r;
            imageData[idx + 1] = g;
            imageData[idx + 2] = b;
            imageData[idx + 3] = 255; // Alpha
        }

        return imageData;
    }

    /**
     * Create colorbar canvas for display
     * @param {HTMLCanvasElement} canvas
     * @param {string} paletteName
     * @param {number} rangeMin
     * @param {number} rangeMax
     * @param {string} label
     */
    drawColorbar(canvas, paletteName = 'coolwarm', rangeMin = 0, rangeMax = 1, label = '') {
        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;

        const colorbarHeight = Math.min(height - 60, height * 0.8);
        const colorbarWidth = 30;
        const startX = (width - colorbarWidth) / 2;
        const startY = (height - colorbarHeight) / 2;

        const palette = this.presets[paletteName] || this.presets['coolwarm'];

        // Draw gradient
        for (let i = 0; i < colorbarHeight; i++) {
            const t = 1 - i / colorbarHeight; // Reverse for top-to-bottom
            let r, g, b;

            const colors = palette.colors;
            let lower = colors[0];
            let upper = colors[colors.length - 1];

            for (let j = 0; j < colors.length - 1; j++) {
                if (colors[j][0] <= t && t <= colors[j + 1][0]) {
                    lower = colors[j];
                    upper = colors[j + 1];
                    break;
                }
            }

            const range = upper[0] - lower[0];
            const t2 = range > 0 ? (t - lower[0]) / range : 0;
            r = Math.round((lower[1][0] + (upper[1][0] - lower[1][0]) * t2) * 255);
            g = Math.round((lower[1][1] + (upper[1][1] - lower[1][1]) * t2) * 255);
            b = Math.round((lower[1][2] + (upper[1][2] - lower[1][2]) * t2) * 255);

            ctx.fillStyle = `rgb(${r},${g},${b})`;
            ctx.fillRect(startX, startY + i, colorbarWidth, 1);
        }

        // Draw border
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.strokeRect(startX, startY, colorbarWidth, colorbarHeight);

        // Draw labels
        ctx.fillStyle = '#333';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(formatValue(rangeMax), startX + colorbarWidth + 5, startY + 12);
        ctx.fillText(formatValue(rangeMin), startX + colorbarWidth + 5, startY + colorbarHeight);

        // Draw title
        if (label) {
            ctx.font = 'bold 12px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(label, startX + colorbarWidth / 2, startY - 10);
        }
    }

    /**
     * Convert palette to Plotly-compatible colorscale
     * @param {string} paletteName
     * @returns {Array}
     */
    toPlotlyColorscale(paletteName = 'coolwarm') {
        const palette = this.presets[paletteName] || this.presets['coolwarm'];
        return palette.colors.map(([pos, rgb]) => [pos, `rgb(${Math.round(rgb[0]*255)},${Math.round(rgb[1]*255)},${Math.round(rgb[2]*255)})`]);
    }
}

// Create global instance
const colorMapManager = new ColorMapManager();
window.colorMapManager = colorMapManager;
