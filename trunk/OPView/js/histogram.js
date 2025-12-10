/**
 * Histogram generation and visualization using Canvas
 */

class HistogramGenerator {
    /**
     * Generate histogram from data array
     * @param {Array<number>} data
     * @param {number} bins
     * @returns {object} {edges, counts, stats}
     */
    static generateHistogram(data, bins = 30) {
        if (!data || data.length === 0) {
            return { edges: [], counts: [], stats: { min: 0, max: 0, mean: 0, std: 0 } };
        }

        const stats = computeStats(data);
        const { min, max, mean, std } = stats;

        if (max === min) {
            return {
                edges: [min],
                counts: [data.length],
                stats
            };
        }

        const edges = [];
        const counts = new Array(bins).fill(0);
        const binWidth = (max - min) / bins;

        for (let i = 0; i <= bins; i++) {
            edges.push(min + i * binWidth);
        }

        data.forEach(value => {
            let binIndex = Math.floor((value - min) / binWidth);
            if (binIndex === bins) binIndex = bins - 1;
            if (binIndex >= 0 && binIndex < bins) {
                counts[binIndex]++;
            }
        });

        return { edges, counts, stats };
    }

    /**
     * Draw histogram on canvas
     * @param {HTMLCanvasElement} canvas
     * @param {Array<number>} data
     * @param {object} options - {bins, minValue, maxValue, palette}
     */
    static drawHistogram(canvas, data, options = {}) {
        const {
            bins = 30,
            minValue = null,
            maxValue = null,
            palette = 'coolwarm',
            title = 'Histogram'
        } = options;

        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;

        // Clear canvas
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);

        if (!data || data.length === 0) {
            ctx.fillStyle = '#999';
            ctx.font = '14px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', width / 2, height / 2);
            return;
        }

        // Generate histogram
        const { edges, counts, stats } = HistogramGenerator.generateHistogram(data, bins);

        if (counts.length === 0) {
            ctx.fillStyle = '#999';
            ctx.font = '14px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No histogram data', width / 2, height / 2);
            return;
        }

        // Layout parameters
        const margin = { top: 40, right: 20, bottom: 50, left: 50 };
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        // Find max count for scaling
        const maxCount = Math.max(...counts);
        const minDataVal = stats.min;
        const maxDataVal = stats.max;

        // Draw background grid
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = margin.top + (plotHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(width - margin.right, y);
            ctx.stroke();
        }

        // Draw bars
        const palette_colors = colorMapManager.presets[palette] || colorMapManager.presets['coolwarm'];
        const barWidth = plotWidth / counts.length;

        counts.forEach((count, i) => {
            const x = margin.left + i * barWidth;
            const barHeight = (count / maxCount) * plotHeight;
            const y = margin.top + plotHeight - barHeight;

            // Get color from palette
            const t = i / (counts.length - 1);
            let color;
            const colors = palette_colors.colors;
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
            const r = Math.round((lower[1][0] + (upper[1][0] - lower[1][0]) * t2) * 255);
            const g = Math.round((lower[1][1] + (upper[1][1] - lower[1][1]) * t2) * 255);
            const b = Math.round((lower[1][2] + (upper[1][2] - lower[1][2]) * t2) * 255);
            color = `rgb(${r},${g},${b})`;

            ctx.fillStyle = color;
            ctx.fillRect(x, y, barWidth - 1, barHeight);

            // Draw bar border
            ctx.strokeStyle = '#999';
            ctx.lineWidth = 0.5;
            ctx.strokeRect(x, y, barWidth - 1, barHeight);
        });

        // Draw axes
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top);
        ctx.lineTo(margin.left, margin.top + plotHeight);
        ctx.lineTo(width - margin.right, margin.top + plotHeight);
        ctx.stroke();

        // Draw axis labels
        ctx.fillStyle = '#000';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';

        // X-axis labels
        const xSteps = 5;
        for (let i = 0; i <= xSteps; i++) {
            const x = margin.left + (plotWidth / xSteps) * i;
            const value = minDataVal + (maxDataVal - minDataVal) * (i / xSteps);
            const label = formatValue(value, 3);
            ctx.fillText(label, x, margin.top + plotHeight + 5);
        }

        // Y-axis label
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        for (let i = 0; i <= 4; i++) {
            const y = margin.top + plotHeight - (plotHeight / 4) * i;
            const count = Math.round((maxCount / 4) * i);
            ctx.fillText(count.toString(), margin.left - 10, y);
        }

        // Draw title
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(title, width / 2, 10);

        // Draw axis titles
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Value', width / 2, height - 10);

        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Count', 0, 0);
        ctx.restore();

        // Draw statistics
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(`n=${data.length}`, 10, height - 25);
        ctx.fillText(`μ=${formatValue(stats.mean, 3)}`, 10, height - 12);
        ctx.fillText(`σ=${formatValue(stats.std, 3)}`, width - 150, height - 25);
        ctx.fillText(`min=${formatValue(stats.min, 3)}`, width - 150, height - 12);
    }

    /**
     * Create line scan plot
     * @param {HTMLCanvasElement} canvas
     * @param {object} data - {x, y, values, stats}
     * @param {object} options
     */
    static drawLineScan(canvas, data, options = {}) {
        const {
            title = 'Line Scan Profile',
            palette = 'coolwarm'
        } = options;

        const ctx = canvas.getContext('2d');
        const { width, height } = canvas;

        // Clear canvas
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, width, height);

        if (!data || !data.values || data.values.length === 0) {
            ctx.fillStyle = '#999';
            ctx.font = '14px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No line scan data', width / 2, height / 2);
            return;
        }

        const { x = [], y = [], values = [] } = data;
        const margin = { top: 40, right: 20, bottom: 50, left: 50 };
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;

        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const range = maxVal - minVal || 1;

        // Draw background grid
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
        ctx.lineWidth = 2;
        ctx.beginPath();

        for (let i = 0; i < values.length; i++) {
            const x_pos = margin.left + (i / (values.length - 1)) * plotWidth;
            const normalized = (values[i] - minVal) / range;

            // Get color from palette
            let color;
            const colors = palette_colors.colors;
            let lower = colors[0];
            let upper = colors[colors.length - 1];

            for (let j = 0; j < colors.length - 1; j++) {
                if (colors[j][0] <= normalized && normalized <= colors[j + 1][0]) {
                    lower = colors[j];
                    upper = colors[j + 1];
                    break;
                }
            }

            const range_color = upper[0] - lower[0];
            const t2 = range_color > 0 ? (normalized - lower[0]) / range_color : 0;
            const r = Math.round((lower[1][0] + (upper[1][0] - lower[1][0]) * t2) * 255);
            const g = Math.round((lower[1][1] + (upper[1][1] - lower[1][1]) * t2) * 255);
            const b = Math.round((lower[1][2] + (upper[1][2] - lower[1][2]) * t2) * 255);
            color = `rgb(${r},${g},${b})`;

            const y_pos = margin.top + plotHeight - normalized * plotHeight;

            if (i === 0) {
                ctx.moveTo(x_pos, y_pos);
            } else {
                ctx.lineTo(x_pos, y_pos);
            }
        }

        ctx.stroke();

        // Draw points
        ctx.fillStyle = '#333';
        for (let i = 0; i < values.length; i++) {
            const x_pos = margin.left + (i / (values.length - 1)) * plotWidth;
            const normalized = (values[i] - minVal) / range;
            const y_pos = margin.top + plotHeight - normalized * plotHeight;

            ctx.fillRect(x_pos - 2, y_pos - 2, 4, 4);
        }

        // Draw axes
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(margin.left, margin.top);
        ctx.lineTo(margin.left, margin.top + plotHeight);
        ctx.lineTo(width - margin.right, margin.top + plotHeight);
        ctx.stroke();

        // Draw labels
        ctx.fillStyle = '#000';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';

        // X-axis
        const xLabel = data.direction === 'vertical' ? 'Y Position' : 'X Position';
        ctx.fillText(xLabel, width / 2, height - 10);

        // Y-axis label
        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Value', 0, 0);
        ctx.restore();

        // Y-axis values
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        for (let i = 0; i <= 4; i++) {
            const y = margin.top + plotHeight - (plotHeight / 4) * i;
            const val = minVal + (range / 4) * i;
            ctx.fillText(formatValue(val, 3), margin.left - 10, y);
        }

        // Title
        ctx.font = 'bold 14px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(title, width / 2, 15);
    }
}
