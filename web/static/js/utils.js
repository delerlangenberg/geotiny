/**
 * Utility functions for Geotiny web interface
 */

// Format number to fixed decimal places
function formatNumber(num, decimals = 3) {
    return Number(num).toFixed(decimals);
}

// Format large numbers with commas
function formatLargeNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Convert timestamp to readable format
function formatTimestamp(iso) {
    try {
        const date = new Date(iso);
        return date.toLocaleString();
    } catch {
        return iso;
    }
}

// Get relative time string (e.g., "2 minutes ago")
function getRelativeTime(iso) {
    try {
        const date = new Date(iso);
        const now = new Date();
        const diffSeconds = Math.floor((now - date) / 1000);

        if (diffSeconds < 60) return `${diffSeconds} seconds ago`;
        if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} minutes ago`;
        if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hours ago`;
        return `${Math.floor(diffSeconds / 86400)} days ago`;
    } catch {
        return iso;
    }
}

// Set status badge color based on status
function getStatusColor(status) {
    const colors = {
        'connected': '#10b981',
        'disconnected': '#ef4444',
        'warning': '#f97316',
        'online': '#10b981',
        'offline': '#ef4444',
    };
    return colors[status] || '#94a3b8';
}

// Make API call with error handling
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            'Content-Type': 'application/json',
            ...options
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API call failed: ${endpoint}`, error);
        return { status: 'error', message: error.message };
    }
}

// Debounce function
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

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Insert at top of page
    const container = document.querySelector('.container-fluid') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    // Auto dismiss
    if (duration > 0) {
        setTimeout(() => alertDiv.remove(), duration);
    }

    return alertDiv;
}

// Generate random color
function getRandomColor() {
    const colors = [
        '#3b82f6', // blue
        '#06b6d4', // cyan
        '#10b981', // green
        '#f97316', // orange
        '#ec4899', // pink
        '#8b5cf6', // purple
    ];
    return colors[Math.floor(Math.random() * colors.length)];
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatNumber,
        formatLargeNumber,
        formatTimestamp,
        getRelativeTime,
        getStatusColor,
        apiCall,
        debounce,
        throttle,
        showNotification,
        getRandomColor,
    };
}
