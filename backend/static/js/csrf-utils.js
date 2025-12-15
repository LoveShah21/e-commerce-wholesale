/**
 * CSRF Token Utilities
 * 
 * Provides functions for handling CSRF tokens in AJAX requests.
 */

/**
 * Get CSRF token from cookie
 * @returns {string|null} CSRF token or null if not found
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Get CSRF token from meta tag or cookie
 * @returns {string|null} CSRF token or null if not found
 */
function getCSRFToken() {
    // Try to get from meta tag first
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }

    // Fallback to cookie
    return getCookie('csrftoken');
}

/**
 * Setup CSRF token for all AJAX requests
 * Call this once when the page loads
 */
function setupCSRF() {
    const csrftoken = getCSRFToken();

    if (!csrftoken) {
        console.warn('CSRF token not found');
        return;
    }

    // Add CSRF token to all fetch requests
    const originalFetch = window.fetch;
    window.fetch = function (url, options = {}) {
        // Only add CSRF token for same-origin requests
        if (!url.startsWith('http') || url.startsWith(window.location.origin)) {
            // Only add for methods that require CSRF protection
            const method = (options.method || 'GET').toUpperCase();
            if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
                options.headers = options.headers || {};
                if (options.headers instanceof Headers) {
                    options.headers.append('X-CSRFToken', csrftoken);
                } else {
                    options.headers['X-CSRFToken'] = csrftoken;
                }
            }
        }
        return originalFetch(url, options);
    };

    // Add CSRF token to all XMLHttpRequest requests
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, async, user, password) {
        this._method = method;
        this._url = url;
        return originalOpen.apply(this, arguments);
    };

    const originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function (data) {
        // Only add CSRF token for same-origin requests
        if (!this._url.startsWith('http') || this._url.startsWith(window.location.origin)) {
            // Only add for methods that require CSRF protection
            const method = (this._method || 'GET').toUpperCase();
            if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
                this.setRequestHeader('X-CSRFToken', csrftoken);
            }
        }
        return originalSend.apply(this, arguments);
    };
}

// Setup CSRF protection when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupCSRF);
} else {
    setupCSRF();
}

// Export functions for use in other scripts
window.getCookie = getCookie;
window.getCSRFToken = getCSRFToken;
window.setupCSRF = setupCSRF;
