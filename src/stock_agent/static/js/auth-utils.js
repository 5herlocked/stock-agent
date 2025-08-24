/**
 * Authentication Utilities for Stock Agent
 * Handles session token management and service worker authentication
 */

class AuthUtils {
    constructor() {
        this.sessionToken = null;
        this.serviceWorkerRegistration = null;
    }

    /**
     * Extract session token from cookies
     * @returns {string|null} Session token or null if not found
     */
    getSessionTokenFromCookie() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'session_token') {
                return value;
            }
        }
        return null;
    }

    /**
     * Store session token in localStorage for persistence
     * @param {string} token - Session token to store
     */
    storeSessionToken(token) {
        try {
            localStorage.setItem('stock_agent_session_token', token);
            this.sessionToken = token;
        } catch (error) {
            console.error('Failed to store session token:', error);
        }
    }

    /**
     * Get stored session token from localStorage
     * @returns {string|null} Stored session token or null
     */
    getStoredSessionToken() {
        try {
            return localStorage.getItem('stock_agent_session_token');
        } catch (error) {
            console.error('Failed to retrieve stored session token:', error);
            return null;
        }
    }

    /**
     * Clear stored session token
     */
    clearStoredSessionToken() {
        try {
            localStorage.removeItem('stock_agent_session_token');
            this.sessionToken = null;
        } catch (error) {
            console.error('Failed to clear stored session token:', error);
        }
    }

    /**
     * Get current valid session token (from cookie first, then localStorage)
     * @returns {string|null} Valid session token or null
     */
    getCurrentSessionToken() {
        // First try cookie (most current)
        let token = this.getSessionTokenFromCookie();

        if (token) {
            // Update stored token if cookie is newer
            const storedToken = this.getStoredSessionToken();
            if (token !== storedToken) {
                this.storeSessionToken(token);
            }
            return token;
        }

        // Fall back to stored token
        token = this.getStoredSessionToken();
        return token;
    }

    /**
     * Register service worker and setup authentication
     * @returns {Promise<ServiceWorkerRegistration|null>}
     */
    async setupServiceWorkerAuth() {
        if (!('serviceWorker' in navigator)) {
            console.warn('Service workers not supported');
            return null;
        }

        try {
            // Register service worker
            this.serviceWorkerRegistration = await navigator.serviceWorker.register(
                '/firebase-messaging-sw.js'
            );
            console.log('Service worker registered successfully');

            // Wait for service worker to be ready
            const sw = await navigator.serviceWorker.ready;

            // Get current session token
            const sessionToken = this.getCurrentSessionToken();

            if (sessionToken && sw.active) {
                // Send token to service worker
                sw.active.postMessage({
                    type: 'UPDATE_SESSION_TOKEN',
                    token: sessionToken
                });
                console.log('Session token sent to service worker');
            }

            // Setup service worker message listener
            this.setupServiceWorkerMessageListener();

            return this.serviceWorkerRegistration;
        } catch (error) {
            console.error('Service worker registration failed:', error);
            return null;
        }
    }

    /**
     * Setup listener for service worker messages
     */
    setupServiceWorkerMessageListener() {
        if (!('serviceWorker' in navigator)) return;

        navigator.serviceWorker.addEventListener('message', (event) => {
            if (event.data.type === 'AUTH_REQUIRED') {
                console.log('Service worker requires authentication:', event.data.message);
                this.handleAuthRequired();
            }
        });
    }

    /**
     * Handle authentication required by service worker
     */
    handleAuthRequired() {
        // Clear invalid tokens
        this.clearStoredSessionToken();

        // Show notification or redirect to login
        if (this.shouldRedirectToLogin()) {
            window.location.href = '/login';
        } else {
            console.warn('Authentication required but not redirecting');
        }
    }

    /**
     * Determine if we should redirect to login page
     * @returns {boolean} True if should redirect
     */
    shouldRedirectToLogin() {
        // Don't redirect if already on login page
        return !window.location.pathname.includes('/login');
    }

    /**
     * Update service worker with new session token
     * @param {string} token - New session token
     */
    async updateServiceWorkerToken(token) {
        if (!token) return;

        // Store the token
        this.storeSessionToken(token);

        // Send to service worker if available
        if ('serviceWorker' in navigator) {
            try {
                const sw = await navigator.serviceWorker.ready;
                if (sw.active) {
                    sw.active.postMessage({
                        type: 'UPDATE_SESSION_TOKEN',
                        token: token
                    });
                    console.log('Updated service worker with new session token');
                }
            } catch (error) {
                console.error('Failed to update service worker token:', error);
            }
        }
    }

    /**
     * Validate current session token by making a test API call
     * @returns {Promise<boolean>} True if token is valid
     */
    async validateSessionToken() {
        const token = this.getCurrentSessionToken();
        if (!token) return false;

        try {
            const response = await fetch('/api/vapid-public-key', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.status === 401) {
                // Token is invalid, clear it
                this.clearStoredSessionToken();
                return false;
            }

            return response.ok;
        } catch (error) {
            console.error('Token validation error:', error);
            return false;
        }
    }

    /**
     * Initialize authentication on page load
     * @returns {Promise<boolean>} True if authentication was successfully setup
     */
    async initialize() {
        try {
            // Get current session token
            const token = this.getCurrentSessionToken();

            if (!token) {
                console.warn('No session token found');
                return false;
            }

            // Validate token
            const isValid = await this.validateSessionToken();
            if (!isValid) {
                console.warn('Session token is invalid');
                return false;
            }

            // Setup service worker
            await this.setupServiceWorkerAuth();

            return true;
        } catch (error) {
            console.error('Authentication initialization failed:', error);
            return false;
        }
    }

    /**
     * Handle successful login
     * @param {string} sessionToken - New session token from login
     */
    async handleLoginSuccess(sessionToken) {
        if (!sessionToken) {
            console.error('No session token provided for login success');
            return;
        }

        // Store the new token
        this.storeSessionToken(sessionToken);

        // Setup or update service worker
        await this.updateServiceWorkerToken(sessionToken);
    }

    /**
     * Handle logout
     */
    handleLogout() {
        // Clear stored tokens
        this.clearStoredSessionToken();

        // Notify service worker if possible
        if ('serviceWorker' in navigator && this.serviceWorkerRegistration) {
            navigator.serviceWorker.ready.then(sw => {
                if (sw.active) {
                    sw.active.postMessage({
                        type: 'CLEAR_SESSION_TOKEN'
                    });
                }
            }).catch(error => {
                console.error('Failed to notify service worker of logout:', error);
            });
        }
    }
}

// Create global instance
window.authUtils = new AuthUtils();

// Auto-initialize on DOM content loaded if not on login page
document.addEventListener('DOMContentLoaded', () => {
    if (!window.location.pathname.includes('/login')) {
        window.authUtils.initialize();
    }
});
