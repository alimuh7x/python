/**
 * TextData Parser and Loader
 * Handles loading and parsing text data files (.txt, .dat)
 */

class TextDataLoader {
    constructor() {
        this.textDataDir = 'TextData';
        this.files = {};
        this.cache = {};
    }

    /**
     * Load all available TextData files
     * @returns {Promise<object>}
     */
    async loadAllTextData() {
        const files = {
            'SizeDetails.dat': { label: 'Size Details', type: 'matrix' },
            'SizeAveInfo.dat': { label: 'Size Average Info', type: 'matrix' },
            'StressStrainFile.txt': { label: 'Stress-Strain Curves', type: 'curves' },
            'CRSSFile.txt': { label: 'CRSS Data', type: 'curves' },
            'CRSSGrainsFile.txt': { label: 'CRSS Grains', type: 'curves' },
            'PlasticStrainFile.txt': { label: 'Plastic Strain', type: 'curves' },
            'PlasticityDiagnosis.txt': { label: 'Plasticity Diagnosis', type: 'matrix' },
            'DDFile.txt': { label: 'Dislocation Density', type: 'curves' },
            'DDGrainsFile.txt': { label: 'DD Grains', type: 'curves' },
            'NeighboInfo.dat': { label: 'Neighbor Info', type: 'matrix' }
        };

        const loaded = {};

        for (const [filename, meta] of Object.entries(files)) {
            try {
                const data = await this.loadTextDataFile(`${this.textDataDir}/${filename}`);
                if (data) {
                    loaded[filename] = { ...meta, data };
                    log('log', `Loaded: ${filename}`, data);
                }
            } catch (error) {
                log('warn', `Could not load ${filename}:`, error.message);
            }
        }

        return loaded;
    }

    /**
     * Load a single text data file
     * @param {string} filePath
     * @returns {Promise<object>}
     */
    async loadTextDataFile(filePath) {
        try {
            const response = await fetch(filePath);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const text = await response.text();
            return this.parseTextData(text);
        } catch (error) {
            log('warn', `Failed to load ${filePath}:`, error);
            return null;
        }
    }

    /**
     * Parse text data content
     * @param {string} text
     * @returns {object}
     */
    parseTextData(text) {
        const lines = text.split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'));

        if (lines.length === 0) {
            return null;
        }

        const rows = [];
        const headers = [];

        lines.forEach((line, idx) => {
            const values = line.split(/\s+/).map(v => {
                const num = parseFloat(v);
                return isNaN(num) ? v : num;
            });

            if (idx === 0 && values.some(v => typeof v === 'string')) {
                // First line is header
                headers.push(...values);
            } else {
                rows.push(values);
            }
        });

        return {
            headers,
            rows,
            columns: rows.length > 0 ? rows[0].length : 0,
            timeSteps: rows.length
        };
    }

    /**
     * Extract time series from parsed data
     * @param {object} data
     * @param {number} column
     * @returns {object} {times, values}
     */
    extractTimeSeries(data, column = 0) {
        if (!data || !data.rows) {
            return { times: [], values: [] };
        }

        const times = [];
        const values = [];

        data.rows.forEach(row => {
            if (row.length > 0) {
                times.push(row[0]); // First column is usually time
            }
            if (row.length > column) {
                values.push(row[column]);
            }
        });

        return { times, values };
    }

    /**
     * Extract multiple columns for multi-curve plot
     * @param {object} data
     * @param {Array<number>} columns
     * @returns {Array<{label, times, values}>}
     */
    extractMultiCurves(data, columns) {
        if (!data || !data.rows) {
            return [];
        }

        const times = [];
        const series = columns.map(() => ({ values: [] }));

        data.rows.forEach((row, idx) => {
            if (idx === 0) return; // Skip header
            if (row.length > 0) {
                times.push(row[0]);
            }

            columns.forEach((col, i) => {
                if (row.length > col) {
                    series[i].values.push(row[col]);
                }
            });
        });

        series.forEach((s, i) => {
            s.label = data.headers && data.headers[columns[i]]
                ? data.headers[columns[i]]
                : `Column ${columns[i]}`;
            s.times = times;
        });

        return series;
    }

    /**
     * Draw a time series plot on canvas
     * @param {HTMLCanvasElement} canvas
     * @param {object} data - {times, values}
     * @param {object} options
     */
    drawTimeSeries(canvas, data, options = {}) {
        const {
            title = 'Time Series',
            xLabel = 'Time Step',
            yLabel = 'Value',
            palette = 'coolwarm'
        } = options;

        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;

        // Clear
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);

        if (!data || !data.times || data.times.length === 0) {
            ctx.fillStyle = '#999';
            ctx.font = '14px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', width / 2, height / 2);
            return;
        }

        const { times, values } = data;
        const margin = { top: 40, right: 20, bottom: 50, left: 60 };
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        const minTime = Math.min(...times);
        const maxTime = Math.max(...times);
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);

        const timeRange = maxTime - minTime || 1;
        const valRange = maxVal - minVal || 1;

        // Draw grid
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = margin.top + (plotHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(width - margin.right, y);
            ctx.stroke();
        }

        // Draw line
        const palette_colors = colorMapManager.presets[palette] || colorMapManager.presets['coolwarm'];
        ctx.strokeStyle = '#0066cc';
        ctx.lineWidth = 2;
        ctx.beginPath();

        values.forEach((val, idx) => {
            const t = (times[idx] - minTime) / timeRange;
            const v = (val - minVal) / valRange;
            const x = margin.left + t * plotWidth;
            const y = margin.top + plotHeight - v * plotHeight;

            if (idx === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        // Draw points
        ctx.fillStyle = '#0066cc';
        values.forEach((val, idx) => {
            const t = (times[idx] - minTime) / timeRange;
            const v = (val - minVal) / valRange;
            const x = margin.left + t * plotWidth;
            const y = margin.top + plotHeight - v * plotHeight;
            ctx.fillRect(x - 2, y - 2, 4, 4);
        });

        // Draw axes
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top);
        ctx.lineTo(margin.left, margin.top + plotHeight);
        ctx.lineTo(width - margin.right, margin.top + plotHeight);
        ctx.stroke();

        // Labels
        ctx.fillStyle = '#000';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(xLabel, width / 2, height - 10);

        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(yLabel, 0, 0);
        ctx.restore();

        // Title
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(title, width / 2, 20);

        // Statistics
        const stats = computeStats(values);
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(`Min: ${formatValue(stats.min, 3)}`, margin.left + 5, height - 25);
        ctx.fillText(`Max: ${formatValue(stats.max, 3)}`, margin.left + 5, height - 12);
        ctx.fillText(`Mean: ${formatValue(stats.mean, 3)}`, width - 120, height - 25);
    }

    /**
     * Draw multiple curves on canvas
     * @param {HTMLCanvasElement} canvas
     * @param {Array<{label, times, values}>} series
     * @param {object} options
     */
    drawMultiCurves(canvas, series, options = {}) {
        const {
            title = 'Multi-Curve Plot',
            xLabel = 'Time Step',
            yLabel = 'Value'
        } = options;

        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;

        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);

        if (!series || series.length === 0) {
            ctx.fillStyle = '#999';
            ctx.font = '14px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No data', width / 2, height / 2);
            return;
        }

        const margin = { top: 40, right: 20, bottom: 50, left: 60 };
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        // Find global min/max
        let allValues = [];
        series.forEach(s => allValues.push(...s.values));
        const minVal = Math.min(...allValues);
        const maxVal = Math.max(...allValues);
        const valRange = maxVal - minVal || 1;

        // Grid
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = margin.top + (plotHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(width - margin.right, y);
            ctx.stroke();
        }

        // Draw each series
        const colors = ['#0066cc', '#ff0000', '#00cc00', '#ffaa00', '#aa00ff', '#00aaaa'];

        series.forEach((s, seriesIdx) => {
            if (!s.times || s.times.length === 0) return;

            const timeRange = Math.max(...s.times) - Math.min(...s.times) || 1;
            const minTime = Math.min(...s.times);

            ctx.strokeStyle = colors[seriesIdx % colors.length];
            ctx.lineWidth = 2;
            ctx.beginPath();

            s.values.forEach((val, idx) => {
                const t = (s.times[idx] - minTime) / timeRange;
                const v = (val - minVal) / valRange;
                const x = margin.left + t * plotWidth;
                const y = margin.top + plotHeight - v * plotHeight;

                if (idx === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });

            ctx.stroke();
        });

        // Axes
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top);
        ctx.lineTo(margin.left, margin.top + plotHeight);
        ctx.lineTo(width - margin.right, margin.top + plotHeight);
        ctx.stroke();

        // Labels
        ctx.fillStyle = '#000';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(xLabel, width / 2, height - 10);

        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText(yLabel, 0, 0);
        ctx.restore();

        // Title
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(title, width / 2, 20);

        // Legend
        ctx.font = '10px Inter, sans-serif';
        let legendY = margin.top + 20;
        series.forEach((s, idx) => {
            ctx.fillStyle = colors[idx % colors.length];
            ctx.fillRect(width - 150, legendY, 10, 10);
            ctx.fillStyle = '#000';
            ctx.textAlign = 'left';
            ctx.fillText(s.label || `Series ${idx + 1}`, width - 135, legendY + 8);
            legendY += 15;
        });
    }
}

// Create global instance
const textDataLoader = new TextDataLoader();
