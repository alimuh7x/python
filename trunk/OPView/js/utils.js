/**
 * Utility functions for OPView
 */

/**
 * Format a number for display with scientific notation fallback
 * @param {number} value - The value to format
 * @param {number} decimals - Number of decimal places (default: 6)
 * @returns {string} Formatted value
 */
function formatValue(value, decimals = 6) {
    if (value === null || value === undefined) return '';
    const absVal = Math.abs(value);
    if (absVal === 0 || (1e-6 <= absVal && absVal < 1e4)) {
        return value.toFixed(decimals);
    }
    return value.toExponential(decimals);
}

/**
 * Parse a color string to RGB object
 * @param {string} color - Color name, hex, or rgb() string
 * @returns {object} Object with r, g, b properties (0-1 range)
 */
function parseColor(color) {
    const ctx = document.createElement('canvas').getContext('2d');
    ctx.fillStyle = color;
    const rgb = ctx.canvas.style.backgroundColor || ctx.canvas.style.color;

    if (rgb.startsWith('rgb')) {
        const matches = rgb.match(/[\d.]+/g);
        return {
            r: parseInt(matches[0]) / 255,
            g: parseInt(matches[1]) / 255,
            b: parseInt(matches[2]) / 255
        };
    }

    // Fallback: parse hex
    const hex = color.startsWith('#') ? color : '#' + color;
    const bigint = parseInt(hex.slice(1), 16);
    return {
        r: ((bigint >> 16) & 255) / 255,
        g: ((bigint >> 8) & 255) / 255,
        b: (bigint & 255) / 255
    };
}

/**
 * Create element with classes and attributes
 * @param {string} tag - HTML tag name
 * @param {object} options - {id, classes, attrs, text, html}
 * @returns {HTMLElement}
 */
function createElement(tag, options = {}) {
    const el = document.createElement(tag);
    if (options.id) el.id = options.id;
    if (options.classes) {
        if (typeof options.classes === 'string') {
            el.className = options.classes;
        } else {
            el.classList.add(...options.classes);
        }
    }
    if (options.attrs) {
        Object.entries(options.attrs).forEach(([key, value]) => {
            el.setAttribute(key, value);
        });
    }
    if (options.text) el.textContent = options.text;
    if (options.html) el.innerHTML = options.html;
    return el;
}

/**
 * Clamp a value between min and max
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

/**
 * Compute statistics from array
 * @param {Array<number>} data
 * @returns {object} {min, max, mean, std}
 */
function computeStats(data) {
    if (!data || data.length === 0) {
        return { min: 0, max: 0, mean: 0, std: 0 };
    }

    const min = Math.min(...data);
    const max = Math.max(...data);
    const mean = data.reduce((a, b) => a + b, 0) / data.length;
    const variance = data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / data.length;
    const std = Math.sqrt(variance);

    return { min, max, mean, std };
}

/**
 * Debounce a function
 * @param {function} func
 * @param {number} wait
 * @returns {function}
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Show toast notification
 * @param {string} message
 * @param {string} type - 'info', 'success', 'error'
 * @param {number} duration - milliseconds
 */
function showToast(message, type = 'info', duration = 3000) {
    const container = document.querySelector('.toast-anchor') || document.body;
    const toast = createElement('div', {
        classes: 'toast',
        text: message
    });

    toast.style.borderLeftColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';
    container.appendChild(toast);

    setTimeout(() => toast.remove(), duration);
}

/**
 * Download canvas as PNG
 * @param {HTMLCanvasElement} canvas
 * @param {string} filename
 */
function downloadCanvasPNG(canvas, filename = 'screenshot.png') {
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = filename;
    link.click();
}

/**
 * Create a simple histogram from data
 * @param {Array<number>} data
 * @param {number} bins
 * @returns {object} {edges, counts}
 */
function createHistogram(data, bins = 30) {
    if (!data || data.length === 0) {
        return { edges: [], counts: [] };
    }

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min;

    if (range === 0) {
        return { edges: [min], counts: [data.length] };
    }

    const edges = [];
    const counts = new Array(bins).fill(0);
    const binWidth = range / bins;

    for (let i = 0; i <= bins; i++) {
        edges.push(min + i * binWidth);
    }

    data.forEach(value => {
        let binIndex = Math.floor((value - min) / binWidth);
        if (binIndex === bins) binIndex = bins - 1; // Handle edge case
        counts[binIndex]++;
    });

    return { edges, counts };
}

/**
 * Interpolate between two values
 * @param {number} a
 * @param {number} b
 * @param {number} t - 0-1
 * @returns {number}
 */
function lerp(a, b, t) {
    return a + (b - a) * t;
}

/**
 * Check if running in browser
 * @returns {boolean}
 */
function isBrowser() {
    return typeof window !== 'undefined' && typeof document !== 'undefined';
}

/**
 * Log with timestamp and level
 * @param {string} level - 'log', 'warn', 'error'
 * @param {string} message
 * @param {*} data
 */
function log(level = 'log', message, data) {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = `[${timestamp}] [OPView]`;
    if (data !== undefined) {
        console[level](prefix, message, data);
    } else {
        console[level](prefix, message);
    }
}
