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
        const modalElement = document.getElementById('loadingModal');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
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
    showToast: function (message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const toastId = 'toast-' + Date.now();
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
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();

        toastElement.addEventListener('hidden.bs.toast', function () {
            toastElement.remove();
        });
    },

    // AJAX helper with CSRF token
    ajax: function (url, options = {}) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };

        if (mergedOptions.headers) {
            mergedOptions.headers = { ...defaultOptions.headers, ...options.headers };
        }

        return fetch(url, mergedOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('AJAX Error:', error);
                this.showToast('An error occurred. Please try again.', 'error');
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
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(form);
            const url = form.action;
            const method = form.method.toUpperCase();

            VaitikanApp.showLoading('Submitting...');

            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    VaitikanApp.hideLoading();
                    if (data.success) {
                        VaitikanApp.showToast(data.message || 'Operation successful!', 'success');
                        if (data.redirect) {
                            setTimeout(() => window.location.href = data.redirect, 1000);
                        }
                    } else {
                        VaitikanApp.showToast(data.message || 'Operation failed!', 'error');
                    }
                })
                .catch(error => {
                    VaitikanApp.hideLoading();
                    VaitikanApp.showToast('An error occurred. Please try again.', 'error');
                    console.error('Form submission error:', error);
                });
        });
    });
});

// Export for use in other scripts
window.VaitikanApp = VaitikanApp;
