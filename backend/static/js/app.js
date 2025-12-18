// Vaitikan City - Main Application JavaScript

// Global utility functions
const VaitikanApp = {
    // Show loading overlay
    showLoading: function (message = 'Loading...') {
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        document.getElementById('loadingModalText').textContent = message;
        modal.show();
    },

    // Hide loading overlay
    hideLoading: function () {
        console.log('🔄 hideLoading called');

        const modalElement = document.getElementById('loadingModal');
        if (!modalElement) {
            console.log('❌ No loading modal element found');
            return;
        }

        console.log('🔧 Force hiding modal with aggressive approach');

        // Immediately force hide the modal
        modalElement.style.setProperty('display', 'none', 'important');
        modalElement.style.setProperty('visibility', 'hidden', 'important');
        modalElement.classList.remove('show', 'fade', 'd-block');
        modalElement.setAttribute('aria-hidden', 'true');
        modalElement.removeAttribute('aria-modal');
        modalElement.removeAttribute('role');

        // Remove all possible backdrops
        const backdrops = document.querySelectorAll('.modal-backdrop, .fade.show');
        backdrops.forEach(backdrop => backdrop.remove());

        // Reset body completely
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        document.body.style.marginRight = '';

        // Try Bootstrap hide as well (but don't rely on it)
        try {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        } catch (e) {
            console.log('Bootstrap modal hide failed, but forced hide should work');
        }

        console.log('✅ Aggressive modal hide completed');
    },

    // Show confirmation modal
    showConfirm: function (message, onConfirm, title = 'Confirm Action') {
        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        document.getElementById('confirmModalLabel').textContent = title;
        document.getElementById('confirmModalBody').textContent = message;

        const confirmBtn = document.getElementById('confirmModalAction');
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

        newConfirmBtn.addEventListener('click', function () {
            modal.hide();
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
        });

        modal.show();
    },

    // Show delete confirmation modal
    showDeleteConfirm: function (message, onConfirm, title = 'Confirm Delete') {
        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        document.getElementById('deleteModalLabel').innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>' + title;
        document.getElementById('deleteModalBody').textContent = message;

        const deleteBtn = document.getElementById('deleteModalAction');
        const newDeleteBtn = deleteBtn.cloneNode(true);
        deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);

        newDeleteBtn.addEventListener('click', function () {
            modal.hide();
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
        });

        modal.show();
    },

    // Show info modal
    showInfo: function (content, title = 'Information') {
        const modal = new bootstrap.Modal(document.getElementById('infoModal'));
        document.getElementById('infoModalLabel').textContent = title;
        document.getElementById('infoModalBody').innerHTML = content;
        modal.show();
    },

    // Show toast notification
    showToast: function (message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const iconMap = {
            'success': 'check-circle-fill',
            'error': 'exclamation-triangle-fill',
            'warning': 'exclamation-circle-fill',
            'info': 'info-circle-fill'
        };
        const bgMap = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        };

        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgMap[type] || 'bg-secondary'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi bi-${iconMap[type] || 'info-circle-fill'} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        document.getElementById('toastContainer').insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration, autohide: true });
        toast.show();

        toastElement.addEventListener('hidden.bs.toast', function () {
            toastElement.remove();
        });

        return toastId;
    },

    // AJAX helper with CSRF token and error handling
    ajax: function (url, options = {}) {
        const displayOptions = options.errorDisplay || {};
        delete options.errorDisplay;

        return window.ErrorHandler.fetchWithErrorHandling(url, options)
            .catch(error => {
                window.ErrorHandler.displayError(error, displayOptions);
                window.ErrorHandler.logError(error, `AJAX: ${url}`);
                throw error;
            });
    },

    // Format currency
    formatCurrency: function (amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount);
    },

    // Format date
    formatDate: function (dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        }).format(date);
    },

    // Debounce function
    debounce: function (func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Test function for debugging loading modal
    testLoading: function () {
        console.log('🧪 Testing loading modal');
        this.showLoading('Test loading...');
        setTimeout(() => {
            console.log('🧪 Attempting to hide loading after 2 seconds');
            this.hideLoading();
        }, 2000);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function () {
    // Initialize all tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Active navigation highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Confirm before form submission for delete actions
    const deleteForms = document.querySelectorAll('form[data-confirm-delete]');
    deleteForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const message = form.getAttribute('data-confirm-message') || 'Are you sure you want to delete this item?';
            VaitikanApp.showDeleteConfirm(message, function () {
                form.submit();
            });
        });
    });

    // Handle AJAX form submissions
    const ajaxForms = document.querySelectorAll('form[data-ajax]');
    ajaxForms.forEach(function (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const formData = new FormData(form);
            const url = form.action;
            const method = form.method.toUpperCase();
            const submitButton = form.querySelector('[type="submit"]');

            const restoreButton = submitButton ?
                window.LoadingStates.showButtonLoading(submitButton, 'Submitting...') : null;

            try {
                const response = await fetch(url, {
                    method: method,
                    body: formData,
                    headers: {
                        'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                    }
                });

                if (!response.ok) {
                    const error = await window.ErrorHandler.parseErrorResponse(response);

                    // Display field errors if present
                    if (error.fieldErrors && Object.keys(error.fieldErrors).length > 0) {
                        window.ErrorHandler.displayFieldErrors(form, error.fieldErrors);
                    }

                    window.ErrorHandler.displayError(error, {
                        showToast: true,
                        showInline: false
                    });

                    throw error;
                }

                const data = await response.json();

                if (data.success !== false) {
                    VaitikanApp.showToast(data.message || 'Operation successful!', 'success');
                    if (data.redirect) {
                        setTimeout(() => window.location.href = data.redirect, 1000);
                    } else if (form.hasAttribute('data-reset-on-success')) {
                        form.reset();
                        if (window.FormValidation) {
                            window.FormValidation.resetForm(form);
                        }
                    }
                } else {
                    VaitikanApp.showToast(data.message || 'Operation failed!', 'error');
                }
            } catch (error) {
                if (!error.type) {
                    // Network or unknown error
                    window.ErrorHandler.displayError({
                        type: window.ErrorHandler.ErrorTypes.NETWORK,
                        message: 'Unable to submit form. Please check your connection.',
                        details: error.message
                    });
                }
                window.ErrorHandler.logError(error, `Form submission: ${url}`);
            } finally {
                if (restoreButton) {
                    restoreButton();
                }
            }
        });
    });
});

// Export for use in other scripts
window.VaitikanApp = VaitikanApp;
