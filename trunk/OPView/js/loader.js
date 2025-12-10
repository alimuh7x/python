/**
 * VTK File Loader using File System Access API
 * Handles loading VTK files and extracting data
 */

class VTKLoader {
    constructor() {
        this.fileCache = new Map();
        this.dataCache = new Map();
    }

    /**
     * Check if browser supports File System Access API
     * @returns {boolean}
     */
    static supportsFileSystemAccess() {
        return 'showDirectoryPicker' in window;
    }

    /**
     * Open folder picker and return directory handle
     * @returns {Promise<FileSystemDirectoryHandle>}
     */
    async selectFolder() {
        try {
            const handle = await window.showDirectoryPicker();
            return handle;
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Error selecting folder:', error);
            }
            return null;
        }
    }

    /**
     * Get all VTK files from a directory
     * @param {FileSystemDirectoryHandle} dirHandle
     * @returns {Promise<Array<{name, handle, path}>>}
     */
    async getVTKFiles(dirHandle) {
        const files = [];

        async function traverse(handle, path = '') {
            try {
                for await (const entry of handle.values()) {
                    const fullPath = path ? `${path}/${entry.name}` : entry.name;

                    if (entry.kind === 'file') {
                        if (entry.name.match(/\.(vtk|vti|vtu|vtr|vts)$/i)) {
                            files.push({
                                name: entry.name,
                                path: fullPath,
                                handle: entry
                            });
                        }
                    } else if (entry.kind === 'directory') {
                        await traverse(entry, fullPath);
                    }
                }
            } catch (error) {
                log('warn', `Error traversing directory: ${error.message}`);
            }
        }

        await traverse(dirHandle);
        return files;
    }

    /**
     * Read file content as ArrayBuffer
     * @param {FileSystemFileHandle} handle
     * @returns {Promise<ArrayBuffer>}
     */
    async readFile(handle) {
        try {
            const file = await handle.getFile();
            return await file.arrayBuffer();
        } catch (error) {
            log('error', `Error reading file: ${error.message}`);
            return null;
        }
    }

    /**
     * Parse VTK file and extract metadata
     * @param {ArrayBuffer} buffer
     * @param {string} filename
     * @returns {object} {scalars, dimensions, type}
     */
    parseVTKFile(buffer, filename) {
        const decoder = new TextDecoder();
        const dataView = new DataView(buffer);

        // Read header (assuming ASCII VTK format)
        const headerSize = Math.min(2000, buffer.byteLength);
        const headerText = decoder.decode(new Uint8Array(buffer, 0, headerSize));
        const headerLines = headerText.split('\n');

        const metadata = {
            filename: filename,
            type: 'unknown',
            scalars: [],
            dimensions: null,
            bounds: null,
            dataType: 'float',
            numberOfComponents: 1
        };

        // Parse header
        for (let i = 0; i < headerLines.length; i++) {
            const line = headerLines[i].trim();

            if (line.startsWith('# vtk DataFile Version')) {
                metadata.version = line.split(' ').pop();
            } else if (line.startsWith('DATASET')) {
                metadata.type = line.split(' ')[1];
            } else if (line.startsWith('DIMENSIONS')) {
                const dims = line.split(' ').slice(1).map(Number);
                metadata.dimensions = dims;
            } else if (line.startsWith('BOUNDS')) {
                const bounds = line.split(' ').slice(1).map(Number);
                metadata.bounds = bounds;
            } else if (line.startsWith('SCALARS')) {
                const parts = line.split(' ');
                metadata.scalars.push({
                    name: parts[1],
                    type: parts[2],
                    numberOfComponents: parseInt(parts[3]) || 1
                });
            } else if (line.startsWith('POINT_DATA') || line.startsWith('CELL_DATA')) {
                // Extract scalar field names from rest of file
                for (let j = i + 1; j < Math.min(i + 50, headerLines.length); j++) {
                    const dataLine = headerLines[j].trim();
                    if (dataLine.startsWith('SCALARS')) {
                        const parts = dataLine.split(' ');
                        if (!metadata.scalars.find(s => s.name === parts[1])) {
                            metadata.scalars.push({
                                name: parts[1],
                                type: parts[2],
                                numberOfComponents: parseInt(parts[3]) || 1
                            });
                        }
                    }
                }
                break;
            }
        }

        return metadata;
    }

    /**
     * Create a synthetic 3D dataset for testing
     * @param {number} nx, ny, nz dimensions
     * @returns {object}
     */
    createTestDataset(nx = 128, ny = 128, nz = 128) {
        const dataset = {
            filename: 'test_data.vti',
            type: 'VTI',
            dimensions: [nx, ny, nz],
            scalars: [
                { name: 'TestField1', type: 'float' },
                { name: 'TestField2', type: 'float' }
            ],
            bounds: [0, nx - 1, 0, ny - 1, 0, nz - 1]
        };

        // Generate test data
        const testField1 = new Float32Array(nx * ny * nz);
        const testField2 = new Float32Array(nx * ny * nz);

        for (let z = 0; z < nz; z++) {
            for (let y = 0; y < ny; y++) {
                for (let x = 0; x < nx; x++) {
                    const idx = z * ny * nx + y * nx + x;
                    // Create gradient patterns
                    testField1[idx] = (x + y + z) / (nx + ny + nz);
                    testField2[idx] = Math.sin(x / 20) * Math.cos(y / 20) * 0.5 + 0.5;
                }
            }
        }

        dataset.data = {
            TestField1: testField1,
            TestField2: testField2
        };

        return dataset;
    }
}

// Create global loader instance
const vtkLoader = new VTKLoader();
