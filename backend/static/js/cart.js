/**
 * Shopping Cart JavaScript Module
 * Handles all cart-related operations including AJAX cart operations,
 * real-time stock checking, form validation, and dynamic price calculation
 * 
 * Requirements: 4.1, 4.2, 4.3, 5.5
 */

const CartModule = (function () {
    'use strict';

    // Private variables
    let currentCart = null;
    let stockCheckInterval = null;

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

    /**
     * Validate quantity input
     * @param {number} quantity - Quantity to validate
     * @param {number} maxStock - Maximum available stock
     * @returns {object} Validation result with isValid and message
     */
    function validateQuantity(quantity, maxStock) {
        const qty = parseInt(quantity);

        if (isNaN(qty)) {
            return {
                isValid: false,
                message: 'Please enter a valid quantity'
            };
        }

        if (qty < 1) {
            return {
                isValid: false,
                message: 'Quantity must be at least 1'
            };
        }

        if (qty > maxStock) {
            return {
                isValid: false,
                message: `Only ${maxStock} items available in stock`
            };
        }

        return {
            isValid: true,
            message: 'Valid quantity'
        };
    }

    /**
     * Check real-time stock availability for a variant size
     * @param {number} variantSizeId - Variant size ID
     * @returns {Promise<object>} Stock information
     */
    async function checkStockAvailability(variantSizeId) {
        // Validate variantSizeId
        if (!variantSizeId || variantSizeId === 'undefined' || isNaN(variantSizeId)) {
            console.error('Invalid variant size ID:', variantSizeId);
            return {
                available: 0,
                inStock: 0,
                reserved: 0,
                error: 'Invalid variant size ID'
            };
        }

        try {
            const response = await fetch(`/api/products/sizes/${variantSizeId}/stock/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });

            if (!response.ok) {
                throw new Error('Failed to check stock availability');
            }

            const data = await response.json();
            return {
                available: data.quantity_available || 0,
                inStock: data.quantity_in_stock || 0,
                reserved: data.quantity_reserved || 0
            };
        } catch (error) {
            console.error('Stock check error:', error);
            return {
                available: 0,
                inStock: 0,
                reserved: 0,
                error: error.message
            };
        }
    }

    /**
     * Add item to cart with validation
     * @param {number} variantSizeId - Variant size ID
     * @param {number} quantity - Quantity to add
     * @returns {Promise<object>} Cart item data
     */
    async function addToCart(variantSizeId, quantity) {
        console.log('🚀 AddToCart started:', { variantSizeId, quantity });
        try {
            // Show loading
            if (window.VaitikanApp) {
                console.log('📱 Showing loading modal');
                window.VaitikanApp.showLoading('Adding to cart...');
            }

            const response = await fetch('/api/cart-items/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    variant_size_id: variantSizeId,
                    quantity: parseInt(quantity)
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('✅ Add to cart API success:', data);

            // Hide loading first
            if (window.VaitikanApp) {
                console.log('🔄 Attempting to hide loading modal');
                window.VaitikanApp.hideLoading();
                console.log('✨ Loading modal hide called, showing toast');
                window.VaitikanApp.showToast('Item added to cart successfully!', 'success');
            }

            // Update cart count (with error handling to not affect loading state)
            try {
                updateCartCount();
            } catch (countError) {
                console.error('Error updating cart count:', countError);
            }

            return data;
        } catch (error) {
            console.error('❌ Add to cart error:', error);
            if (window.VaitikanApp) {
                console.log('🔄 Hiding loading modal due to error');
                window.VaitikanApp.hideLoading();
                window.VaitikanApp.showToast(error.message || 'Failed to add item to cart', 'error');
            }
            throw error;
        }
    }

    /**
     * Update cart item quantity with validation
     * @param {number} itemId - Cart item ID
     * @param {number} newQuantity - New quantity
     * @param {number} maxStock - Maximum available stock
     * @returns {Promise<object>} Updated cart item data
     */
    async function updateCartItem(itemId, newQuantity, maxStock) {
        // Validate quantity
        const validation = validateQuantity(newQuantity, maxStock);
        if (!validation.isValid) {
            if (window.VaitikanApp) {
                window.VaitikanApp.showToast(validation.message, 'error');
            }
            throw new Error(validation.message);
        }

        try {
            const response = await fetch(`/api/cart-items/${itemId}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'same-origin',
                body: JSON.stringify({ quantity: parseInt(newQuantity) })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}`);
            }

            const data = await response.json();

            if (window.VaitikanApp) {
                window.VaitikanApp.showToast('Cart updated', 'success');
            }

            return data;
        } catch (error) {
            if (window.VaitikanApp) {
                window.VaitikanApp.showToast(error.message || 'Failed to update cart', 'error');
            }
            console.error('Update cart item error:', error);
            throw error;
        }
    }

    /**
     * Remove item from cart with confirmation
     * @param {number} itemId - Cart item ID
     * @param {boolean} skipConfirmation - Skip confirmation modal
     * @returns {Promise<boolean>} Success status
     */
    async function removeCartItem(itemId, skipConfirmation = false) {
        const performRemoval = async () => {
            try {
                const response = await fetch(`/api/cart-items/${itemId}/`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || errorData.error || 'Failed to remove item');
                }

                if (window.VaitikanApp) {
                    window.VaitikanApp.showToast('Item removed from cart', 'success');
                }

                // Update cart count
                updateCartCount();

                return true;
            } catch (error) {
                if (window.VaitikanApp) {
                    window.VaitikanApp.showToast(error.message || 'Failed to remove item', 'error');
                }
                console.error('Remove cart item error:', error);
                throw error;
            }
        };

        if (skipConfirmation) {
            return performRemoval();
        }

        // Show confirmation modal
        return new Promise((resolve) => {
            if (window.VaitikanApp && window.VaitikanApp.showDeleteConfirm) {
                window.VaitikanApp.showDeleteConfirm(
                    'Are you sure you want to remove this item from your cart?',
                    async () => {
                        const result = await performRemoval();
                        resolve(result);
                    },
                    'Remove Item'
                );
            } else {
                // Fallback to native confirm
                if (confirm('Are you sure you want to remove this item from your cart?')) {
                    performRemoval().then(resolve);
                } else {
                    resolve(false);
                }
            }
        });
    }

    /**
     * Clear entire cart with confirmation
     * @returns {Promise<boolean>} Success status
     */
    async function clearCart() {
        return new Promise((resolve) => {
            if (window.VaitikanApp && window.VaitikanApp.showDeleteConfirm) {
                window.VaitikanApp.showDeleteConfirm(
                    'Are you sure you want to clear your entire cart? This action cannot be undone.',
                    async () => {
                        try {
                            const response = await fetch('/api/cart/clear/', {
                                method: 'DELETE',
                                headers: {
                                    'X-CSRFToken': getCookie('csrftoken')
                                }
                            });

                            if (!response.ok) {
                                throw new Error('Failed to clear cart');
                            }

                            if (window.VaitikanApp) {
                                window.VaitikanApp.showToast('Cart cleared', 'success');
                            }

                            // Update cart count
                            updateCartCount();

                            resolve(true);
                        } catch (error) {
                            if (window.VaitikanApp) {
                                window.VaitikanApp.showToast('Failed to clear cart', 'error');
                            }
                            resolve(false);
                        }
                    },
                    'Clear Cart'
                );
            } else {
                resolve(false);
            }
        });
    }

    /**
     * Load cart data from API
     * @returns {Promise<object>} Cart data
     */
    async function loadCart() {
        try {
            const response = await fetch('/api/cart/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // User not authenticated, redirect to login
                    window.location.href = '/login/';
                    return;
                }
                throw new Error(`Failed to load cart: ${response.status}`);
            }

            const data = await response.json();
            currentCart = data;
            return data;
        } catch (error) {
            console.error('Error loading cart:', error);
            throw error;
        }
    }

    /**
     * Calculate cart totals with tax
     * @param {object} cart - Cart data
     * @returns {object} Calculated totals
     */
    function calculateCartTotals(cart) {
        const items = cart?.items || cart?.results || [];

        if (!items || items.length === 0) {
            return {
                subtotal: 0,
                tax: 0,
                taxRate: 0.18,
                total: 0,
                itemCount: 0
            };
        }

        const subtotal = items.reduce((sum, item) => {
            // Use the enhanced variant_details structure
            const price = parseFloat(item.variant_details?.final_price || 0);
            return sum + (price * item.quantity);
        }, 0);

        const taxRate = 0.18; // 18% GST
        const tax = subtotal * taxRate;
        const total = subtotal + tax;

        const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

        return {
            subtotal: subtotal,
            tax: tax,
            taxRate: taxRate,
            total: total,
            itemCount: itemCount
        };
    }

    /**
     * Update cart count badge in navigation
     */
    async function updateCartCount() {
        try {
            const response = await fetch('/api/cart/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // User not authenticated, hide cart badge
                    const cartBadge = document.getElementById('cartCount');
                    if (cartBadge) {
                        cartBadge.style.display = 'none';
                    }
                    return;
                }
                throw new Error(`Failed to load cart: ${response.status}`);
            }

            const cart = await response.json();
            const cartBadge = document.getElementById('cartCount');

            if (cartBadge) {
                const items = cart.items || cart.results || [];
                const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
                cartBadge.textContent = totalItems;
                cartBadge.style.display = totalItems > 0 ? 'inline' : 'none';
            }
        } catch (error) {
            console.error('Error updating cart count:', error);
        }
    }

    /**
     * Validate cart before checkout
     * @returns {Promise<object>} Validation result
     */
    async function validateCartForCheckout() {
        try {
            const cart = await loadCart();

            if (!cart.items || cart.items.length === 0) {
                return {
                    isValid: false,
                    message: 'Your cart is empty'
                };
            }

            // Check stock availability for all items
            const stockChecks = await Promise.all(
                cart.items.map(async (item) => {
                    // item.variant_size is the ID, item.variant_details has the full details
                    const variantSizeId = item.variant_size || item.variant_details?.id;
                    const stock = await checkStockAvailability(variantSizeId);
                    return {
                        item: item,
                        stock: stock,
                        isValid: item.quantity <= stock.available
                    };
                })
            );

            const invalidItems = stockChecks.filter(check => !check.isValid);

            if (invalidItems.length > 0) {
                const messages = invalidItems.map(check => {
                    // Get product name from enhanced variant_details
                    const productName = check.item.variant_details?.product_name || 'Product';
                    return `${productName}: Only ${check.stock.available} available (you have ${check.item.quantity} in cart)`;
                });

                return {
                    isValid: false,
                    message: 'Some items in your cart are no longer available in the requested quantity',
                    details: messages
                };
            }

            return {
                isValid: true,
                message: 'Cart is valid for checkout'
            };
        } catch (error) {
            return {
                isValid: false,
                message: 'Unable to validate cart',
                error: error.message
            };
        }
    }

    /**
     * Start periodic stock checking for cart items
     * @param {number} intervalMs - Check interval in milliseconds (default: 30000 = 30 seconds)
     */
    function startStockMonitoring(intervalMs = 30000) {
        if (stockCheckInterval) {
            clearInterval(stockCheckInterval);
        }

        stockCheckInterval = setInterval(async () => {
            if (!currentCart || !currentCart.items || currentCart.items.length === 0) {
                return;
            }

            // Check stock for all items
            for (const item of currentCart.items) {
                const variantSizeId = item.variant_size || item.variant_details?.id;
                const stock = await checkStockAvailability(variantSizeId);

                // If stock is less than cart quantity, show warning
                if (stock.available < item.quantity) {
                    const productName = item.variant_details?.product_name || 'Product';
                    if (window.VaitikanApp) {
                        window.VaitikanApp.showToast(
                            `Stock updated: ${productName} now has only ${stock.available} available`,
                            'warning'
                        );
                    }

                    // Trigger cart reload if on cart page
                    const cartContainer = document.getElementById('cartItemsContainer');
                    if (cartContainer) {
                        const event = new CustomEvent('stockUpdated', {
                            detail: { item: item, stock: stock }
                        });
                        document.dispatchEvent(event);
                    }
                }
            }
        }, intervalMs);
    }

    /**
     * Stop stock monitoring
     */
    function stopStockMonitoring() {
        if (stockCheckInterval) {
            clearInterval(stockCheckInterval);
            stockCheckInterval = null;
        }
    }

    /**
     * Format price as currency
     * @param {number} amount - Amount to format
     * @returns {string} Formatted currency string
     */
    function formatPrice(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    }

    // Public API
    return {
        addToCart: addToCart,
        updateCartItem: updateCartItem,
        removeCartItem: removeCartItem,
        clearCart: clearCart,
        loadCart: loadCart,
        calculateCartTotals: calculateCartTotals,
        updateCartCount: updateCartCount,
        validateCartForCheckout: validateCartForCheckout,
        checkStockAvailability: checkStockAvailability,
        validateQuantity: validateQuantity,
        startStockMonitoring: startStockMonitoring,
        stopStockMonitoring: stopStockMonitoring,
        formatPrice: formatPrice,
        getCurrentCart: () => currentCart
    };
})();

// Export for use in other scripts
window.CartModule = CartModule;

// Initialize cart count on page load
document.addEventListener('DOMContentLoaded', function () {
    CartModule.updateCartCount();
});
