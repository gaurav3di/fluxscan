// FluxScan Main Application JavaScript

// Initialize Socket.IO connection
const socket = io();

// Toast notification system
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const alertClass = type === 'error' ? 'alert-error' :
                      type === 'success' ? 'alert-success' :
                      type === 'warning' ? 'alert-warning' : 'alert-info';

    const toast = document.createElement('div');
    toast.className = `alert ${alertClass}`;
    toast.innerHTML = `<span>${message}</span>`;

    toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// WebSocket event handlers
socket.on('connect', function() {
    console.log('Connected to FluxScan WebSocket');
});

socket.on('disconnect', function() {
    console.log('Disconnected from FluxScan WebSocket');
});

socket.on('scan_progress', function(data) {
    console.log('Scan progress:', data);
    updateScanProgress(data.scan_id, data.progress, data.symbol);
});

socket.on('scan_complete', function(data) {
    console.log('Scan complete:', data);
    showToast(`Scan completed! Found ${data.signals_found} signals`, 'success');
    updateScanComplete(data.scan_id, data.status);
});

// Scan progress tracking
const activeScanProgress = {};

function updateScanProgress(scanId, progress, symbol) {
    const progressBar = document.getElementById(`progress-${scanId}`);
    const symbolText = document.getElementById(`symbol-${scanId}`);

    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`;
    }

    if (symbolText) {
        symbolText.textContent = `Scanning: ${symbol}`;
    }

    activeScanProgress[scanId] = progress;
}

function updateScanComplete(scanId, status) {
    const statusBadge = document.getElementById(`status-${scanId}`);
    if (statusBadge) {
        statusBadge.textContent = status;
        statusBadge.className = status === 'completed' ? 'badge badge-success' : 'badge badge-error';
    }

    // Remove from active scans
    delete activeScanProgress[scanId];

    // Reload results if on results page
    if (window.location.pathname.includes('results')) {
        setTimeout(() => location.reload(), 1000);
    }
}

// API Helper Functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Request failed');
    }

    return response.json();
}

// Scanner Functions
async function runScanner(scannerId, watchlistId, parameters = {}) {
    try {
        const result = await apiRequest('/scan/api/scan', {
            method: 'POST',
            body: JSON.stringify({
                scanner_id: scannerId,
                watchlist_id: watchlistId,
                parameters: parameters
            })
        });

        showToast('Scan started successfully', 'success');

        // Subscribe to scan updates
        socket.emit('subscribe_scan', { scan_id: result.scan_id });

        return result;
    } catch (error) {
        showToast(`Failed to start scan: ${error.message}`, 'error');
        throw error;
    }
}

async function validateScannerCode(code) {
    try {
        const result = await apiRequest('/scanners/api/scanners/validate', {
            method: 'POST',
            body: JSON.stringify({ code: code })
        });

        return result;
    } catch (error) {
        console.error('Validation error:', error);
        return { is_valid: false, errors: [error.message], warnings: [] };
    }
}

// Watchlist Functions
async function importWatchlist(name, symbols, exchange = 'NSE') {
    try {
        const result = await apiRequest('/watchlists/api/watchlists', {
            method: 'POST',
            body: JSON.stringify({
                name: name,
                symbols: symbols,
                exchange: exchange
            })
        });

        showToast('Watchlist imported successfully', 'success');
        return result;
    } catch (error) {
        showToast(`Failed to import watchlist: ${error.message}`, 'error');
        throw error;
    }
}

// Symbol search with debouncing
let searchTimeout;
function searchSymbols(query, callback) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(async () => {
        if (query.length < 2) {
            callback([]);
            return;
        }

        try {
            const results = await apiRequest(`/api/symbols/search?q=${encodeURIComponent(query)}`);
            callback(results);
        } catch (error) {
            console.error('Symbol search error:', error);
            callback([]);
        }
    }, 300);
}

// Export functions
async function exportResults(format = 'csv', filters = {}) {
    try {
        const response = await fetch('/api/results/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                format: format,
                ...filters
            })
        });

        if (format === 'csv') {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scan_results_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } else {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        showToast(`Export failed: ${error.message}`, 'error');
        throw error;
    }
}

// Initialize HTMX event handlers
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Reinitialize components after HTMX swap
    initializeComponents();
});

document.body.addEventListener('htmx:responseError', function(event) {
    showToast('Request failed. Please try again.', 'error');
});

// Component initialization
function initializeComponents() {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
        // Tooltip initialization logic
    });

    // Initialize modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        // Modal initialization logic
    });
}

// Theme toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Load saved theme
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    initializeComponents();
});

// Export functions for use in other scripts
window.FluxScan = {
    showToast,
    runScanner,
    validateScannerCode,
    importWatchlist,
    searchSymbols,
    exportResults,
    toggleTheme
};