/**
 * Payment Integration JavaScript
 * Handles Razorpay payment integration and payment-related UI interactions
 */

/**
 * Get CSRF token from cookie
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

const csrftoken = getCookie('csrftoken');

/**
 * Show loading spinner
 */
function showLoading(message = 'Processing...') {
    const loadingHtml = `
        <div id="payment-loading" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" 
             style="background: rgba(0,0,0,0.5); z-index: 9999;">
            <div class="card text-center p-4">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mb-0">${message}</p>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    const loading = document.getElementById('payment-loading');
    if (loading) {
        loading.remove();
    }
}

/**
 * Show error message
 */
function showError(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" 
             role="alert" style="z-index: 10000; min-width: 300px;">
            <i class="bi bi-exclamation-triangle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', alertHtml);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Show success message
 */
function showSuccess(message) {
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3" 
             role="alert" style="z-index: 10000; min-width: 300px;">
            <i class="bi bi-check-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', alertHtml);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 3000);
}

/**
 * Initiate payment for an order
 * @param {number} orderId - The order ID
 * @param {string} paymentType - 'advance' or 'final'
 * @param {string} paymentMethod - Payment method (default: 'upi')
 */
async function initiatePayment(orderId, paymentType, paymentMethod = 'upi') {
    showLoading('Creating payment order...');

    try {
        // Create payment order
        const response = await fetch('/api/payments/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                order_id: orderId,
                payment_type: paymentType,
                payment_method: paymentMethod
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to create payment order');
        }

        hideLoading();

        // Open Razorpay checkout
        openRazorpayCheckout(data, orderId);

    } catch (error) {
        hideLoading();
        showError(error.message);
        console.error('Payment initiation error:', error);
    }
}

/**
 * Open Razorpay checkout modal
 * @param {object} paymentData - Payment data from API
 * @param {number} orderId - The order ID
 */
function openRazorpayCheckout(paymentData, orderId) {
    const options = {
        key: paymentData.razorpay_key_id,
        amount: paymentData.amount,
        currency: paymentData.currency,
        name: 'Vaitikan City',
        description: `${paymentData.payment.payment_type_display} Payment for Order #${orderId}`,
        order_id: paymentData.razorpay_order_id,
        handler: function (response) {
            // Payment successful
            verifyPayment(
                paymentData.payment.id,
                response.razorpay_payment_id,
                response.razorpay_signature,
                orderId
            );
        },
        prefill: {
            name: '',
            email: '',
            contact: ''
        },
        theme: {
            color: '#0d6efd'
        },
        modal: {
            ondismiss: function () {
                // Payment cancelled by user
                console.log('Payment cancelled by user');
            }
        }
    };

    const rzp = new Razorpay(options);

    rzp.on('payment.failed', function (response) {
        // Payment failed
        handlePaymentFailure(
            paymentData.payment.id,
            response.error.description,
            orderId
        );
    });

    rzp.open();
}

/**
 * Verify payment signature
 * @param {number} paymentId - Payment ID
 * @param {string} razorpayPaymentId - Razorpay payment ID
 * @param {string} razorpaySignature - Razorpay signature
 * @param {number} orderId - Order ID
 */
async function verifyPayment(paymentId, razorpayPaymentId, razorpaySignature, orderId) {
    showLoading('Verifying payment...');

    try {
        const response = await fetch('/api/payments/verify/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                payment_id: paymentId,
                razorpay_payment_id: razorpayPaymentId,
                razorpay_signature: razorpaySignature
            })
        });

        const data = await response.json();

        hideLoading();

        if (!response.ok) {
            throw new Error(data.error || 'Payment verification failed');
        }

        // Redirect to success page
        window.location.href = `/payments/success/?payment_id=${paymentId}&order_id=${orderId}`;

    } catch (error) {
        hideLoading();
        showError(error.message);
        console.error('Payment verification error:', error);

        // Redirect to failure page
        setTimeout(() => {
            window.location.href = `/payments/failure/?payment_id=${paymentId}&order_id=${orderId}&error=${encodeURIComponent(error.message)}`;
        }, 2000);
    }
}

/**
 * Handle payment failure
 * @param {number} paymentId - Payment ID
 * @param {string} failureReason - Failure reason
 * @param {number} orderId - Order ID
 */
async function handlePaymentFailure(paymentId, failureReason, orderId) {
    showLoading('Recording payment failure...');

    try {
        const response = await fetch('/api/payments/failure/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                payment_id: paymentId,
                failure_reason: failureReason
            })
        });

        const data = await response.json();

        hideLoading();

        if (!response.ok) {
            console.error('Failed to record payment failure:', data.error);
        }

        // Redirect to failure page
        window.location.href = `/payments/failure/?payment_id=${paymentId}&order_id=${orderId}&error=${encodeURIComponent(failureReason)}`;

    } catch (error) {
        hideLoading();
        console.error('Payment failure handling error:', error);

        // Still redirect to failure page
        window.location.href = `/payments/failure/?payment_id=${paymentId}&order_id=${orderId}&error=${encodeURIComponent(failureReason)}`;
    }
}

/**
 * Retry a failed payment
 * @param {number} orderId - Order ID
 * @param {string} paymentType - 'advance' or 'final'
 */
async function retryPayment(orderId, paymentType) {
    showLoading('Retrying payment...');

    try {
        const response = await fetch('/api/payments/retry/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                order_id: orderId,
                payment_type: paymentType
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to retry payment');
        }

        hideLoading();

        // Open Razorpay checkout
        openRazorpayCheckout(data, orderId);

    } catch (error) {
        hideLoading();
        showError(error.message);
        console.error('Payment retry error:', error);
    }
}

/**
 * Get payment status for an order
 * @param {number} orderId - Order ID
 * @returns {Promise<object>} Payment status
 */
async function getPaymentStatus(orderId) {
    try {
        const response = await fetch(`/api/payments/status/${orderId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to get payment status');
        }

        return data;

    } catch (error) {
        console.error('Payment status error:', error);
        throw error;
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initiatePayment,
        retryPayment,
        getPaymentStatus
    };
}
