/**
 * Form Validation Module
 * Provides comprehensive form validation with error display
 * 
 * Requirements: 4.1, 4.2, 4.3, 5.5
 */

const FormValidation = (function () {
    'use strict';

    /**
     * Validation rules
     */
    const validationRules = {
        required: {
            validate: (value) => value !== null && value !== undefined && value.toString().trim() !== '',
            message: 'This field is required'
        },
        email: {
            validate: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            message: 'Please enter a valid email address'
        },
        phone: {
            validate: (value) => /^[0-9]{10}$/.test(value.replace(/[\s\-\(\)]/g, '')),
            message: 'Please enter a valid 10-digit phone number'
        },
        minLength: {
            validate: (value, min) => value.length >= min,
            message: (min) => `Must be at least ${min} characters`
        },
        maxLength: {
            validate: (value, max) => value.length <= max,
            message: (max) => `Must be no more than ${max} characters`
        },
        min: {
            validate: (value, min) => parseFloat(value) >= min,
            message: (min) => `Must be at least ${min}`
        },
        max: {
            validate: (value, max) => parseFloat(value) <= max,
            message: (max) => `Must be no more than ${max}`
        },
        number: {
            validate: (value) => !isNaN(parseFloat(value)) && isFinite(value),
            message: 'Please enter a valid number'
        },
        integer: {
            validate: (value) => Number.isInteger(parseFloat(value)),
            message: 'Please enter a whole number'
        },
        positive: {
            validate: (value) => parseFloat(value) > 0,
            message: 'Must be a positive number'
        },
        url: {
            validate: (value) => {
                try {
                    new URL(value);
                    return true;
                } catch {
                    return false;
                }
            },
            message: 'Please enter a valid URL'
        },
        pattern: {
            validate: (value, pattern) => new RegExp(pattern).test(value),
            message: 'Invalid format'
        },
        match: {
            validate: (value, matchFieldId) => {
                const matchField = document.getElementById(matchFieldId);
                return matchField && value === matchField.value;
            },
            message: 'Fields do not match'
        }
    };

    /**
     * Display error message for a field
     * @param {HTMLElement} field - Input field element
     * @param {string} message - Error message
     */
    function showError(field, message) {
        // Remove existing error
        clearError(field);

        // Add error class to field
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');

        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        errorDiv.setAttribute('data-validation-error', 'true');

        // Insert error message after field
        field.parentNode.insertBefore(errorDiv, field.nextSibling);

        // Add aria-invalid attribute
        field.setAttribute('aria-invalid', 'true');
    }

    /**
     * Clear error message for a field
     * @param {HTMLElement} field - Input field element
     */
    function clearError(field) {
        field.classList.remove('is-invalid');
        field.setAttribute('aria-invalid', 'false');

        // Remove error message
        const errorDiv = field.parentNode.querySelector('[data-validation-error="true"]');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * Show success state for a field
     * @param {HTMLElement} field - Input field element
     */
    function showSuccess(field) {
        clearError(field);
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
    }

    /**
     * Validate a single field
     * @param {HTMLElement} field - Input field element
     * @returns {boolean} Validation result
     */
    function validateField(field) {
        const value = field.value;
        let isValid = true;

        // Check required
        if (field.hasAttribute('required') || field.hasAttribute('data-required')) {
            if (!validationRules.required.validate(value)) {
                showError(field, validationRules.required.message);
                return false;
            }
        }

        // If field is empty and not required, skip other validations
        if (value.trim() === '' && !field.hasAttribute('required')) {
            clearError(field);
            return true;
        }

        // Check type-specific validations
        const type = field.type || field.getAttribute('data-type');

        switch (type) {
            case 'email':
                if (!validationRules.email.validate(value)) {
                    showError(field, validationRules.email.message);
                    return false;
                }
                break;

            case 'tel':
                if (field.hasAttribute('data-validate-phone')) {
                    if (!validationRules.phone.validate(value)) {
                        showError(field, validationRules.phone.message);
                        return false;
                    }
                }
                break;

            case 'number':
                if (!validationRules.number.validate(value)) {
                    showError(field, validationRules.number.message);
                    return false;
                }
                break;

            case 'url':
                if (!validationRules.url.validate(value)) {
                    showError(field, validationRules.url.message);
                    return false;
                }
                break;
        }

        // Check min/max length
        const minLength = field.getAttribute('minlength') || field.getAttribute('data-minlength');
        if (minLength && !validationRules.minLength.validate(value, parseInt(minLength))) {
            showError(field, validationRules.minLength.message(minLength));
            return false;
        }

        const maxLength = field.getAttribute('maxlength') || field.getAttribute('data-maxlength');
        if (maxLength && !validationRules.maxLength.validate(value, parseInt(maxLength))) {
            showError(field, validationRules.maxLength.message(maxLength));
            return false;
        }

        // Check min/max value
        const min = field.getAttribute('min') || field.getAttribute('data-min');
        if (min && !validationRules.min.validate(value, parseFloat(min))) {
            showError(field, validationRules.min.message(min));
            return false;
        }

        const max = field.getAttribute('max') || field.getAttribute('data-max');
        if (max && !validationRules.max.validate(value, parseFloat(max))) {
            showError(field, validationRules.max.message(max));
            return false;
        }

        // Check pattern
        const pattern = field.getAttribute('pattern') || field.getAttribute('data-pattern');
        if (pattern && !validationRules.pattern.validate(value, pattern)) {
            const patternMessage = field.getAttribute('data-pattern-message') || validationRules.pattern.message;
            showError(field, patternMessage);
            return false;
        }

        // Check match (for password confirmation, etc.)
        const matchField = field.getAttribute('data-match');
        if (matchField && !validationRules.match.validate(value, matchField)) {
            const matchMessage = field.getAttribute('data-match-message') || validationRules.match.message;
            showError(field, matchMessage);
            return false;
        }

        // Check custom validation
        const customValidation = field.getAttribute('data-custom-validation');
        if (customValidation && window[customValidation]) {
            const result = window[customValidation](value, field);
            if (result !== true) {
                showError(field, result || 'Invalid value');
                return false;
            }
        }

        // All validations passed
        if (isValid) {
            showSuccess(field);
        }

        return isValid;
    }

    /**
     * Validate entire form
     * @param {HTMLFormElement} form - Form element
     * @returns {boolean} Validation result
     */
    function validateForm(form) {
        let isValid = true;
        const fields = form.querySelectorAll('input, select, textarea');

        fields.forEach(field => {
            // Skip disabled and hidden fields
            if (field.disabled || field.type === 'hidden') {
                return;
            }

            if (!validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Initialize form validation
     * @param {HTMLFormElement} form - Form element
     * @param {object} options - Configuration options
     */
    function initializeForm(form, options = {}) {
        const config = {
            validateOnBlur: true,
            validateOnInput: false,
            showSuccessState: true,
            scrollToError: true,
            ...options
        };

        const fields = form.querySelectorAll('input, select, textarea');

        // Add event listeners to fields
        fields.forEach(field => {
            // Skip disabled and hidden fields
            if (field.disabled || field.type === 'hidden') {
                return;
            }

            // Validate on blur
            if (config.validateOnBlur) {
                field.addEventListener('blur', function () {
                    validateField(this);
                });
            }

            // Validate on input (with debounce)
            if (config.validateOnInput) {
                let timeout;
                field.addEventListener('input', function () {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        validateField(this);
                    }, 500);
                });
            }

            // Clear error on focus
            field.addEventListener('focus', function () {
                if (this.classList.contains('is-invalid')) {
                    clearError(this);
                }
            });
        });

        // Handle form submission
        form.addEventListener('submit', function (e) {
            if (!validateForm(form)) {
                e.preventDefault();

                // Scroll to first error
                if (config.scrollToError) {
                    const firstError = form.querySelector('.is-invalid');
                    if (firstError) {
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        firstError.focus();
                    }
                }

                // Show toast notification
                if (window.VaitikanApp) {
                    window.VaitikanApp.showToast('Please correct the errors in the form', 'error');
                }

                return false;
            }

            // Form is valid, allow submission
            return true;
        });
    }

    /**
     * Add custom validation rule
     * @param {string} name - Rule name
     * @param {function} validateFn - Validation function
     * @param {string|function} message - Error message
     */
    function addCustomRule(name, validateFn, message) {
        validationRules[name] = {
            validate: validateFn,
            message: message
        };
    }

    /**
     * Reset form validation state
     * @param {HTMLFormElement} form - Form element
     */
    function resetForm(form) {
        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            clearError(field);
            field.classList.remove('is-valid');
        });
    }

    // Public API
    return {
        validateField: validateField,
        validateForm: validateForm,
        initializeForm: initializeForm,
        showError: showError,
        clearError: clearError,
        showSuccess: showSuccess,
        addCustomRule: addCustomRule,
        resetForm: resetForm
    };
})();

// Export for use in other scripts
window.FormValidation = FormValidation;

// Auto-initialize forms with data-validate attribute
document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        const options = {
            validateOnBlur: form.getAttribute('data-validate-on-blur') !== 'false',
            validateOnInput: form.getAttribute('data-validate-on-input') === 'true',
            showSuccessState: form.getAttribute('data-show-success') !== 'false',
            scrollToError: form.getAttribute('data-scroll-to-error') !== 'false'
        };
        FormValidation.initializeForm(form, options);
    });
});
