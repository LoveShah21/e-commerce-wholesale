/**
 * Network Status Monitor
 * Monitors network connectivity and displays status to user
 */

(function () {
    'use strict';

    let statusIndicator = null;
    let isOnline = navigator.onLine;

    /**
     * Create status indicator element
     */
    function createStatusIndicator() {
        if (statusIndicator) {
            return statusIndicator;
        }

        statusIndicator = document.createElement('div');
        statusIndicator.className = 'network-status';
        statusIndicator.innerHTML = `
            <i class="bi bi-wifi-off me-2"></i>
            <span>No internet connection</span>
        `;
        document.body.appendChild(statusIndicator);

        return statusIndicator;
    }

    /**
     * Show offline status
     */
    function showOfflineStatus() {
        const indicator = createStatusIndicator();
        indicator.classList.remove('online');
        indicator.innerHTML = `
            <i class="bi bi-wifi-off me-2"></i>
            <span>No internet connection</span>
        `;
        indicator.style.display = 'block';

        // Show toast notification
        if (window.VaitikanApp) {
            window.VaitikanApp.showToast(
                'You are offline. Some features may not work.',
                'warning',
                5000
            );
        }
    }

    /**
     * Show online status
     */
    function showOnlineStatus() {
        const indicator = createStatusIndicator();
        indicator.classList.add('online');
        indicator.innerHTML = `
            <i class="bi bi-wifi me-2"></i>
            <span>Back online</span>
        `;
        indicator.style.display = 'block';

        // Show toast notification
        if (window.VaitikanApp) {
            window.VaitikanApp.showToast(
                'Connection restored',
                'success',
                3000
            );
        }

        // Hide indicator after 3 seconds
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 3000);
    }

    /**
     * Handle online event
     */
    function handleOnline() {
        if (!isOnline) {
            isOnline = true;
            showOnlineStatus();
            console.log('Network: Online');
        }
    }

    /**
     * Handle offline event
     */
    function handleOffline() {
        if (isOnline) {
            isOnline = false;
            showOfflineStatus();
            console.log('Network: Offline');
        }
    }

    /**
     * Check network status periodically
     */
    function checkNetworkStatus() {
        if (navigator.onLine !== isOnline) {
            if (navigator.onLine) {
                handleOnline();
            } else {
                handleOffline();
            }
        }
    }

    // Initialize
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check status every 5 seconds
    setInterval(checkNetworkStatus, 5000);

    // Show initial status if offline
    if (!navigator.onLine) {
        document.addEventListener('DOMContentLoaded', showOfflineStatus);
    }

    // Export status check function
    window.NetworkStatus = {
        isOnline: () => isOnline,
        check: checkNetworkStatus
    };
})();
