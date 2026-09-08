/* ====================================================================
   TrustLens - Main JavaScript
   ====================================================================
   Frontend logic for image upload, verification, and blockchain display
   ==================================================================== */

// ====================================================================
// UPLOAD PAGE FUNCTIONALITY
// ====================================================================

// Listen for form submission
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleUpload);
    }

    // Load and display uploads list
    loadUploadsList();

    // Refresh uploads every 5 seconds
    setInterval(loadUploadsList, 5000);
});

/**
 * Handle image upload form submission
 * Sends file and uploader name to the Flask backend
 */
function handleUpload(event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const uploaderName = document.getElementById('uploaderName').value || 'Anonymous';
    const file = fileInput.files[0];

    if (!file) {
        showStatus('uploadStatus', 'Please select a file', 'error');
        return;
    }

    // Show loading state
    showStatus('uploadStatus', 'Uploading...', 'loading');

    // Create FormData to send file
    const formData = new FormData();
    formData.append('file', file);
    formData.append('uploader_name', uploaderName);

    // Send to backend
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus(
                'uploadStatus',
                `✅ ${data.message}\n` +
                `File Hash: ${data.file_hash.substring(0, 32)}...\n` +
                `Block #${data.block_index} added to blockchain`,
                'success'
            );

            // Clear form
            uploadForm.reset();

            // Reload gallery
            loadUploadsList();
        } else {
            showStatus('uploadStatus', `❌ ${data.error}`, 'error');
        }
    })
    .catch(error => {
        showStatus('uploadStatus', `❌ Error: ${error.message}`, 'error');
    });
}

/**
 * Load and display all uploaded images
 */
function loadUploadsList() {
    fetch('/api/uploads')
        .then(response => response.json())
        .then(data => {
            if (!data.success) return;

            const uploadsList = document.getElementById('uploadsList');
            if (!uploadsList) return;

            if (data.uploads.length === 0) {
                uploadsList.innerHTML = '<p class="text-center loading">No images uploaded yet</p>';
                return;
            }

            // Clear and build gallery
            uploadsList.innerHTML = '';

            data.uploads.forEach(upload => {
                const item = document.createElement('div');
                item.className = 'gallery-item';

                const uploadTime = new Date(upload.upload_timestamp).toLocaleString();
                const hashPreview = upload.file_hash.substring(0, 16) + '...';

                item.innerHTML = `
                    <div class="gallery-item-image">
                        📁
                    </div>
                    <div class="gallery-item-info">
                        <div class="gallery-item-filename">${escapeHtml(upload.filename)}</div>
                        <div class="gallery-item-hash">
                            <strong>Hash:</strong><br>
                            ${upload.file_hash}
                        </div>
                        <div class="gallery-item-uploader">
                            <strong>Uploader:</strong> ${escapeHtml(upload.uploader_name)}<br>
                            <strong>Time:</strong> ${uploadTime}<br>
                            <strong>Block:</strong> #${upload.block_index}
                        </div>
                    </div>
                `;

                uploadsList.appendChild(item);
            });

            // Update blockchain status
            updateBlockchainStatus(data);
        });
}

/**
 * Update blockchain status display
 */
function updateBlockchainStatus(data) {
    const statusDiv = document.getElementById('blockchainStatus');
    if (!statusDiv) return;

    let html = '';

    if (data.blockchain_valid) {
        html = `
            <div class="verification-success">
                <h4>✅ Blockchain Valid</h4>
                <p>Total Blocks: ${data.total_blocks}</p>
                <p>Total Images: ${data.total_uploads}</p>
                <p>All blocks are properly linked and unmodified.</p>
            </div>
        `;
    } else {
        html = `
            <div class="verification-failure">
                <h4>❌ Blockchain Invalid</h4>
                <p>${data.blockchain_error}</p>
            </div>
        `;
    }

    statusDiv.innerHTML = html;
}

// ====================================================================
// UTILITY FUNCTIONS
// ====================================================================

/**
 * Show status message with appropriate styling
 * @param {string} elementId - ID of element to show message in
 * @param {string} message - Message to display
 * @param {string} type - Type: 'success', 'error', 'loading', 'warning'
 */
function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message;
    element.className = `status-message ${type}`;
    element.style.display = 'block';
}

/**
 * Escape HTML special characters to prevent XSS attacks
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format bytes to human readable format
 * @param {number} bytes - Number of bytes
 * @returns {string} - Formatted string
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format timestamp to readable date
 * @param {string} isoString - ISO timestamp string
 * @returns {string} - Formatted date string
 */
function formatDate(isoString) {
    return new Date(isoString).toLocaleString();
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show brief notification
        const msg = document.createElement('div');
        msg.textContent = '✓ Copied!';
        msg.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--secondary-color);
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(msg);
        setTimeout(() => msg.remove(), 2000);
    });
}

// ====================================================================
// HASH DISPLAY HELPER
// ====================================================================

/**
 * Make hash values clickable to copy
 * Add this to any page that displays hashes
 */
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'CODE' && e.target.textContent.length > 20) {
        copyToClipboard(e.target.textContent);
    }
});

// ====================================================================
// FILE INPUT ENHANCEMENT
// ====================================================================

document.addEventListener('change', function(e) {
    // Update label when file is selected
    if (e.target.type === 'file') {
        const wrapper = e.target.closest('.file-input-wrapper');
        if (wrapper) {
            const label = wrapper.querySelector('.file-label');
            if (e.target.files.length > 0) {
                label.textContent = `📁 Selected: ${e.target.files[0].name}`;
            } else {
                label.textContent = 'Choose an image...';
            }
        }
    }
});

// ====================================================================
// NAVIGATION ACTIVE STATE
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Get current page
    const path = window.location.pathname;

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });
});

// ====================================================================
// KEYBOARD SHORTCUTS
// ====================================================================

/**
 * Keyboard shortcuts:
 * Ctrl+U: Focus upload form
 * Ctrl+V: Focus verify form
 */
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey) {
        if (e.key === 'u') {
            e.preventDefault();
            const uploadForm = document.getElementById('uploadForm');
            if (uploadForm) uploadForm.focus();
        }
        if (e.key === 'v') {
            e.preventDefault();
            const verifyForm = document.getElementById('verifyForm');
            if (verifyForm) verifyForm.focus();
        }
    }
});

// ====================================================================
// DARK MODE SUPPORT (Optional)
// ====================================================================

/**
 * Check system preference for dark mode and apply if available
 */
function initDarkModeSupport() {
    // This is optional - the current CSS doesn't have dark mode
    // But this function is here for future enhancement

    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        // System prefers dark mode
        // Could add data-theme="dark" to body here
    }

    // Listen for changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        // Handle theme change
    });
}

// ====================================================================
// AUTO-REFRESH FUNCTIONALITY
// ====================================================================

let autoRefreshEnabled = true;

/**
 * Enable/disable auto-refresh of data
 */
function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;
    if (autoRefreshEnabled) {
        loadUploadsList();
    }
}

/**
 * Manual refresh function
 */
function manualRefresh() {
    loadUploadsList();
    const msg = document.createElement('div');
    msg.textContent = '🔄 Refreshing...';
    msg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--primary-color);
        color: white;
        padding: 10px 20px;
        border-radius: 4px;
        z-index: 1000;
    `;
    document.body.appendChild(msg);
    setTimeout(() => msg.remove(), 1500);
}

// ====================================================================
// ERROR HANDLING
// ====================================================================

/**
 * Global error handler
 */
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    // Optionally show user-friendly error message
});

/**
 * Unhandled promise rejection handler
 */
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled rejection:', event.reason);
    // Optionally show user-friendly error message
});

// ====================================================================
// INITIALIZATION
// ====================================================================

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('TrustLens Frontend Initialized');
    initDarkModeSupport();
});

console.log('TrustLens Frontend Scripts Loaded');
