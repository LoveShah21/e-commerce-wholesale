/**
 * Loading States Module
 * Provides loading indicators for async operations
 * 
 * Requirements: All error handling requirements
 */

const LoadingStates = (function () {
    'use strict';

    /**
     * Show loading spinner on button
     * @param {HTMLElement} button - Button element
     * @param {string} loadingText - Text to display while loading
     * @returns {function} Function to restore button state
     */
    function showButtonLoading(button, loadingText = 'Loading...') {
        if (!button) return () => { };

        // Store original state
        const originalHTML = button.innerHTML;
        const originalDisabled = button.disabled;

        // Set loading state
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${loadingText}
        `;
        button.classList.add('loading');

        // Return restore function
        return function restore() {
            button.innerHTML = originalHTML;
            button.disabled = originalDisabled;
            button.classList.remove('loading');
        };
    }

    /**
     * Show loading overlay on element
     * @param {HTMLElement} element - Target element
     * @param {string} message - Loading message
     * @returns {function} Function to hide loading overlay
     */
    function showElementLoading(element, message = 'Loading...') {
        if (!element) return () => { };

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mb-0">${message}</p>
            </div>
        `;

        // Add styles if not already present
        if (!document.getElementById('loading-overlay-styles')) {
            const style = document.createElement('style');
            style.id = 'loading-overlay-styles';
            style.textContent = `
                .loading-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    border-radius: inherit;
                }
                .loading-content {
                    text-align: center;
                }
                .loading-overlay .spinner-border {
                    width: 3rem;
                    height: 3rem;
                }
            `;
            document.head.appendChild(style);
        }

        // Make element position relative if not already
        const originalPosition = element.style.position;
        if (!originalPosition || originalPosition === 'static') {
            element.style.position = 'relative';
        }

        // Add overlay
        element.appendChild(overlay);

        // Return hide function
        return function hide() {
            overlay.remove();
            if (!originalPosition || originalPosition === 'static') {
                element.style.position = '';
            }
        };
    }

    /**
     * Show loading skeleton for content
     * @param {HTMLElement} element - Target element
     * @param {number} lines - Number of skeleton lines
     * @returns {function} Function to hide skeleton
     */
    function showSkeleton(element, lines = 3) {
        if (!element) return () => { };

        // Store original content
        const originalContent = element.innerHTML;

        // Create skeleton
        let skeletonHTML = '<div class="skeleton-loader">';
        for (let i = 0; i < lines; i++) {
            const width = 70 + Math.random() * 30; // Random width between 70-100%
            skeletonHTML += `
                <div class="skeleton-line" style="width: ${width}%;"></div>
            `;
        }
        skeletonHTML += '</div>';

        // Add styles if not already present
        if (!document.getElementById('skeleton-loader-styles')) {
            const style = document.createElement('style');
            style.id = 'skeleton-loader-styles';
            style.textContent = `
                .skeleton-loader {
                    padding: 1rem 0;
                }
                .skeleton-line {
                    height: 1rem;
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: skeleton-loading 1.5s ease-in-out infinite;
                    border-radius: 4px;
                    margin-bottom: 0.75rem;
                }
                .skeleton-line:last-child {
                    margin-bottom: 0;
                }
                @keyframes skeleton-loading {
                    0% {
                        background-position: 200% 0;
                    }
                    100% {
                        background-position: -200% 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        // Set skeleton content
        element.innerHTML = skeletonHTML;

        // Return restore function
        return function restore() {
            element.innerHTML = originalContent;
        };
    }

    /**
     * Show inline loading spinner
     * @param {HTMLElement} element - Target element
     * @param {string} size - Spinner size ('sm', 'md', 'lg')
     * @returns {function} Function to hide spinner
     */
    function showInlineSpinner(element, size = 'sm') {
        if (!element) return () => { };

        const sizeClass = size === 'sm' ? 'spinner-border-sm' : '';
        const spinner = document.createElement('span');
        spinner.className = `spinner-border ${sizeClass} text-primary ms-2`;
        spinner.setAttribute('role', 'status');
        spinner.setAttribute('aria-hidden', 'true');
        spinner.setAttribute('data-inline-spinner', 'true');

        element.appendChild(spinner);

        return function hide() {
            spinner.remove();
        };
    }

    /**
     * Show progress bar
     * @param {HTMLElement} element - Target element
     * @param {number} progress - Progress percentage (0-100)
     * @param {string} label - Progress label
     */
    function showProgress(element, progress = 0, label = '') {
        if (!element) return;

        let progressBar = element.querySelector('.progress-bar-container');

        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.className = 'progress-bar-container mb-3';
            progressBar.innerHTML = `
                <div class="d-flex justify-content-between mb-1">
                    <span class="progress-label">${label}</span>
                    <span class="progress-percentage">0%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" 
                         style="width: 0%"
                         aria-valuenow="0" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                    </div>
                </div>
            `;
            element.insertBefore(progressBar, element.firstChild);
        }

        // Update progress
        const bar = progressBar.querySelector('.progress-bar');
        const percentage = progressBar.querySelector('.progress-percentage');
        const labelElement = progressBar.querySelector('.progress-label');

        bar.style.width = `${progress}%`;
        bar.setAttribute('aria-valuenow', progress);
        percentage.textContent = `${Math.round(progress)}%`;

        if (label) {
            labelElement.textContent = label;
        }

        // Remove animation when complete
        if (progress >= 100) {
            bar.classList.remove('progress-bar-animated');
            bar.classList.add('bg-success');
        }
    }

    /**
     * Hide progress bar
     * @param {HTMLElement} element - Target element
     */
    function hideProgress(element) {
        if (!element) return;

        const progressBar = element.querySelector('.progress-bar-container');
        if (progressBar) {
            progressBar.remove();
        }
    }

    /**
     * Wrap async function with loading state
     * @param {function} asyncFn - Async function to wrap
     * @param {object} options - Loading options
     * @returns {function} Wrapped function
     */
    function withLoading(asyncFn, options = {}) {
        const config = {
            button: null,
            element: null,
            loadingText: 'Loading...',
            showGlobalLoading: false,
            ...options
        };

        return async function (...args) {
            let restoreButton = null;
            let hideElementLoading = null;

            try {
                // Show loading states
                if (config.button) {
                    restoreButton = showButtonLoading(config.button, config.loadingText);
                }

                if (config.element) {
                    hideElementLoading = showElementLoading(config.element, config.loadingText);
                }

                if (config.showGlobalLoading && window.VaitikanApp) {
                    window.VaitikanApp.showLoading(config.loadingText);
                }

                // Execute async function
                const result = await asyncFn.apply(this, args);

                return result;
            } finally {
                // Hide loading states
                if (restoreButton) {
                    restoreButton();
                }

                if (hideElementLoading) {
                    hideElementLoading();
                }

                if (config.showGlobalLoading && window.VaitikanApp) {
                    window.VaitikanApp.hideLoading();
                }
            }
        };
    }

    /**
     * Create loading state manager for multiple operations
     * @returns {object} Loading state manager
     */
    function createLoadingManager() {
        let activeOperations = 0;
        let callbacks = [];

        return {
            start: function () {
                activeOperations++;
                this.notify();
            },
            finish: function () {
                activeOperations = Math.max(0, activeOperations - 1);
                this.notify();
            },
            isLoading: function () {
                return activeOperations > 0;
            },
            onChange: function (callback) {
                callbacks.push(callback);
            },
            notify: function () {
                callbacks.forEach(cb => cb(this.isLoading()));
            }
        };
    }

    // Public API
    return {
        showButtonLoading,
        showElementLoading,
        showSkeleton,
        showInlineSpinner,
        showProgress,
        hideProgress,
        withLoading,
        createLoadingManager
    };
})();

// Export for use in other scripts
window.LoadingStates = LoadingStates;

// Auto-handle loading states for forms with data-loading attribute
document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('form[data-loading]');

    forms.forEach(form => {
        const submitButton = form.querySelector('[type="submit"]');
        const loadingText = form.getAttribute('data-loading-text') || 'Processing...';

        form.addEventListener('submit', function () {
            if (submitButton) {
                LoadingStates.showButtonLoading(submitButton, loadingText);
            }
        });
    });
});
