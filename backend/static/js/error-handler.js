/**
 * Error Handler Module
 * Provides comprehensive error handling for API calls and user feedback
 * 
 * Requirements: All error handling requirements
 */

const ErrorHandler = (function () {
    'use strict';

    /**
     * Error type constants
     */
    const ErrorTypes = {
        NETWORK: 'network',
        AUTHENTICATION: 'authentication',
        AUTHORIZATION: 'authorization',
        VALIDATION: 'validation',
        NOT_FOUND: 'not_found',
        CONFLICT: 'conflict',
        SERVER: 'server',
        UNKNOWN: 'unknown'
    };

    /**
     * User-friendly error messages
     */
    const ErrorMessages = {
        [ErrorTypes.NETWORK]: 'Unable to connect to the server. Please check your internet connection.',
        [ErrorTypes.AUTHENTICATION]: 'Your session has expired. Please log in again.',
        [ErrorTypes.AUTHORIZATION]: 'You don\'t have permission to perform this action.',
        [ErrorTypes.VALIDATION]: 'Please check your input and try again.',
        [ErrorTypes.NOT_FOUND]: 'The requested resource was not found.',
        [ErrorTypes.CONFLICT]: 'This action conflicts with existing data.',
        [ErrorTypes.SERVER]: 'An unexpected error occurred. Please try again later.',
        [ErrorTypes.UNKNOWN]: 'Something went wrong. Please try again.'
    };

    /**
     * Determine error type from HTTP status code
     * @param {number} status - HTTP status code
     * @returns {string} Error type
     */
    function getErrorType(status) {
        if (status === 0 || !navigator.onLine) {
            return ErrorTypes.NETWORK;
        } else if (status === 401) {
            return ErrorTypes.AUTHENTICATION;
        } else if (status === 403) {
            return ErrorTypes.AUTHORIZATION;
        } else if (status === 400 || status === 422) {
            return ErrorTypes.VALIDATION;
        } else if (status === 404) {
            return ErrorTypes.NOT_FOUND;
        } else if (status === 409) {
            return ErrorTypes.CONFLICT;
        } else if (status >= 500) {
            return ErrorTypes.SERVER;
        } else {
            return ErrorTypes.UNKNOWN;
        }
    }

    /**
     * Parse error response from API
     * @param {Response} response - Fetch API response
     * @returns {Promise<object>} Parsed error object
     */
    async function parseErrorResponse(response) {
        const errorType = getErrorType(response.status);
        let errorData = {
            type: errorType,
            status: response.status,
            message: ErrorMessages[errorType],
            details: null,
            fieldErrors: {}
        };

        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();

                // Handle Django REST Framework error format
                if (data.detail) {
                    errorData.message = data.detail;
                } else if (data.error) {
                    errorData.message = data.error;
                } else if (data.message) {
                    errorData.message = data.message;
                }

                // Handle field-specific errors
                if (typeof data === 'object' && !data.detail && !data.error && !data.message) {
                    errorData.fieldErrors = data;
                    errorData.message = 'Please correct the errors in the form.';
                }

                errorData.details = data;
            } else {
                const text = await response.text();
                if (text) {
                    errorData.details = text;
                }
            }
        } catch (parseError) {
            console.error('Error parsing error response:', parseError);
        }

        return errorData;
    }

    /**
     * Display error message to user
     * @param {object} error - Error object
     * @param {object} options - Display options
     */
    function displayError(error, options = {}) {
        const config = {
            showToast: true,
            showModal: false,
            showInline: false,
            targetElement: null,
            duration: 5000,
            ...options
        };

        // Show toast notification
        if (config.showToast && window.VaitikanApp) {
            const toastType = error.type === ErrorTypes.VALIDATION ? 'warning' : 'error';
            window.VaitikanApp.showToast(error.message, toastType, config.duration);
        }

        // Show modal
        if (config.showModal && window.VaitikanApp) {
            let modalContent = `<p>${error.message}</p>`;

            if (error.fieldErrors && Object.keys(error.fieldErrors).length > 0) {
                modalContent += '<ul class="list-unstyled mt-3">';
                for (const [field, errors] of Object.entries(error.fieldErrors)) {
                    const errorList = Array.isArray(errors) ? errors : [errors];
                    errorList.forEach(err => {
                        modalContent += `<li><strong>${field}:</strong> ${err}</li>`;
                    });
                }
                modalContent += '</ul>';
            }

            window.VaitikanApp.showInfo(modalContent, 'Error');
        }

        // Show inline error
        if (config.showInline && config.targetElement) {
            displayInlineError(config.targetElement, error);
        }

        // Handle authentication errors
        if (error.type === ErrorTypes.AUTHENTICATION) {
            setTimeout(() => {
                window.location.href = '/users/login/?next=' + encodeURIComponent(window.location.pathname);
            }, 2000);
        }

        // Handle authorization errors
        if (error.type === ErrorTypes.AUTHORIZATION && !config.showModal) {
            setTimeout(() => {
                window.location.href = '/403/';
            }, 2000);
        }
    }

    /**
     * Display inline error message
     * @param {HTMLElement} element - Target element
     * @param {object} error - Error object
     */
    function displayInlineError(element, error) {
        // Remove existing error
        const existingError = element.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        // Create error element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show error-message mt-3';
        errorDiv.setAttribute('role', 'alert');

        let errorHTML = `
            <i class="bi bi-exclamation-triangle me-2"></i>
            <strong>Error:</strong> ${error.message}
        `;

        if (error.fieldErrors && Object.keys(error.fieldErrors).length > 0) {
            errorHTML += '<ul class="mb-0 mt-2">';
            for (const [field, errors] of Object.entries(error.fieldErrors)) {
                const errorList = Array.isArray(errors) ? errors : [errors];
                errorList.forEach(err => {
                    errorHTML += `<li><strong>${field}:</strong> ${err}</li>`;
                });
            }
            errorHTML += '</ul>';
        }

        errorHTML += `
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        errorDiv.innerHTML = errorHTML;
        element.insertBefore(errorDiv, element.firstChild);

        // Scroll to error
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    /**
     * Display field-specific errors in a form
     * @param {HTMLFormElement} form - Form element
     * @param {object} fieldErrors - Field error object
     */
    function displayFieldErrors(form, fieldErrors) {
        // Clear existing errors
        const existingErrors = form.querySelectorAll('.invalid-feedback[data-api-error="true"]');
        existingErrors.forEach(error => error.remove());

        const invalidFields = form.querySelectorAll('.is-invalid');
        invalidFields.forEach(field => {
            field.classList.remove('is-invalid');
            field.setAttribute('aria-invalid', 'false');
        });

        // Display new errors
        for (const [fieldName, errors] of Object.entries(fieldErrors)) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const errorList = Array.isArray(errors) ? errors : [errors];
                const errorMessage = errorList.join(', ');

                // Add error class
                field.classList.add('is-invalid');
                field.setAttribute('aria-invalid', 'true');

                // Create error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.setAttribute('data-api-error', 'true');
                errorDiv.textContent = errorMessage;

                // Insert error message
                field.parentNode.insertBefore(errorDiv, field.nextSibling);
            }
        }

        // Scroll to first error
        const firstError = form.querySelector('.is-invalid');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
    }

    /**
     * Enhanced fetch wrapper with error handling
     * @param {string} url - Request URL
     * @param {object} options - Fetch options
     * @returns {Promise} Fetch promise with error handling
     */
    async function fetchWithErrorHandling(url, options = {}) {
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

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                const error = await parseErrorResponse(response);
                throw error;
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            // If error is already parsed, throw it
            if (error.type) {
                throw error;
            }

            // Handle network errors
            if (error instanceof TypeError && error.message.includes('fetch')) {
                throw {
                    type: ErrorTypes.NETWORK,
                    message: ErrorMessages[ErrorTypes.NETWORK],
                    details: error.message
                };
            }

            // Unknown error
            throw {
                type: ErrorTypes.UNKNOWN,
                message: ErrorMessages[ErrorTypes.UNKNOWN],
                details: error.message
            };
        }
    }

    /**
     * Log error for debugging
     * @param {object} error - Error object
     * @param {string} context - Error context
     */
    function logError(error, context = '') {
        const timestamp = new Date().toISOString();
        const logMessage = {
            timestamp,
            context,
            type: error.type,
            status: error.status,
            message: error.message,
            details: error.details,
            url: window.location.href,
            userAgent: navigator.userAgent
        };

        console.error('Error Log:', logMessage);

        // Send to server logging endpoint if available
        if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            try {
                fetch('/api/logs/client-error/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(logMessage)
                }).catch(() => {
                    // Silently fail if logging endpoint is not available
                });
            } catch (e) {
                // Silently fail
            }
        }
    }

    // Public API
    return {
        ErrorTypes,
        ErrorMessages,
        parseErrorResponse,
        displayError,
        displayInlineError,
        displayFieldErrors,
        fetchWithErrorHandling,
        logError,
        getErrorType
    };
})();

// Export for use in other scripts
window.ErrorHandler = ErrorHandler;

// Global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', function (event) {
    console.error('Unhandled promise rejection:', event.reason);
    ErrorHandler.logError({
        type: ErrorHandler.ErrorTypes.UNKNOWN,
        message: 'Unhandled promise rejection',
        details: event.reason
    }, 'unhandledrejection');
});

// Global error handler for JavaScript errors
window.addEventListener('error', function (event) {
    console.error('JavaScript error:', event.error);
    ErrorHandler.logError({
        type: ErrorHandler.ErrorTypes.UNKNOWN,
        message: event.message,
        details: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            error: event.error
        }
    }, 'javascript_error');
});
