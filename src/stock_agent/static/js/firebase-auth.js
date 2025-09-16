/**
 * Firebase Authentication with HTMX Integration
 * Service worker handles its own Firebase Auth independently
 */

// Firebase imports using CDN
import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.2.1/firebase-app.js';
import { 
    getAuth, 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword,
    signOut, 
    onAuthStateChanged,
    updateProfile
} from 'https://www.gstatic.com/firebasejs/12.2.1/firebase-auth.js';

class FirebaseAuthManager {
    constructor() {
        this.app = null;
        this.auth = null;
        this.currentUser = null;
        this.currentIdToken = null;
        this.initialized = false;
    }

    /**
     * Initialize Firebase Auth
     */
    async initialize() {
        try {
            // Get Firebase config from server
            const response = await fetch('/api/firebase-config-public');
            if (!response.ok) {
                throw new Error(`Failed to fetch Firebase config: ${response.status}`);
            }
            const firebaseConfig = await response.json();

            // Initialize Firebase
            this.app = initializeApp(firebaseConfig);
            this.auth = getAuth(this.app);

            // Set up auth state listener
            this.setupAuthStateListener();

            // Configure HTMX for authenticated requests
            this.configureHTMXAuth();

            // Register service worker for messaging
            this.registerServiceWorker();

            this.initialized = true;
            console.log('Firebase Auth initialized successfully');
            return true;
        } catch (error) {
            console.error('Failed to initialize Firebase Auth:', error);
            return false;
        }
    }

    /**
     * Set up Firebase auth state listener
     */
    setupAuthStateListener() {
        onAuthStateChanged(this.auth, async (user) => {
            this.currentUser = user;
            
            if (user) {
                // User is signed in - get fresh ID token
                try {
                    this.currentIdToken = await user.getIdToken();
                    
                    // Store token in cookie for server-side access
                    this.setTokenCookie(this.currentIdToken);
                    
                    console.log('User signed in:', user.email);
                    
                } catch (error) {
                    console.error('Failed to get ID token:', error);
                }
            } else {
                // User is signed out
                this.currentIdToken = null;
                this.clearTokenCookie();
                console.log('User signed out');
            }

            // Handle page redirects
            this.handleAuthStateChange(user);
        });
    }

    /**
     * Handle authentication state changes
     */
    handleAuthStateChange(user) {
        const isAuthenticated = !!user;
        
        // Trigger custom event for other components
        const authEvent = new CustomEvent('auth-state-changed', {
            detail: { 
                authenticated: isAuthenticated,
                user: user ? {
                    email: user.email,
                    displayName: user.displayName,
                    uid: user.uid
                } : null
            }
        });
        document.dispatchEvent(authEvent);

        // Handle page redirects
        if (!isAuthenticated && this.isProtectedPage()) {
            window.location.href = '/login';
        } else if (isAuthenticated && window.location.pathname === '/login') {
            window.location.href = '/';
        }
    }

    /**
     * Check if current page requires authentication
     */
    isProtectedPage() {
        const protectedPaths = ['/', '/stocks', '/report', '/notifications'];
        return protectedPaths.includes(window.location.pathname);
    }

    /**
     * Set Firebase token as cookie for server access
     */
    setTokenCookie(token) {
        document.cookie = `firebase_token=${token}; Path=/; SameSite=Strict; Secure=${location.protocol === 'https:'}`;
    }

    /**
     * Clear Firebase token cookie
     */
    clearTokenCookie() {
        document.cookie = 'firebase_token=; Path=/; Max-Age=0';
    }



    /**
     * Configure HTMX for authentication error handling
     * Note: Service worker automatically adds Authorization headers
     */
    configureHTMXAuth() {
        if (!window.htmx) {
            console.warn('HTMX not loaded');
            return;
        }

        // Handle auth errors from HTMX requests
        document.body.addEventListener('htmx:responseError', (event) => {
            if (event.detail.xhr.status === 401) {
                console.log('Authentication required, refreshing token');
                this.handleAuthError();
            }
        });
    }

    /**
     * Handle authentication errors - try to refresh token
     */
    async handleAuthError() {
        try {
            if (this.currentUser) {
                // Try to refresh the token
                this.currentIdToken = await this.currentUser.getIdToken(true);
                this.setTokenCookie(this.currentIdToken);
                console.log('Token refreshed successfully');
                return;
            }
        } catch (error) {
            console.error('Failed to refresh token:', error);
        }

        // If refresh fails, sign out
        await this.signOut();
    }

    /**
     * Sign in with email and password
     */
    async signInWithEmail(email, password) {
        try {
            const userCredential = await signInWithEmailAndPassword(this.auth, email, password);
            console.log('Sign in successful:', userCredential.user.email);
            return { success: true, user: userCredential.user };
        } catch (error) {
            console.error('Sign in failed:', error);
            return { success: false, error: this.getReadableError(error) };
        }
    }

    /**
     * Sign out current user
     */
    async signOut() {
        try {
            await signOut(this.auth);
            console.log('Sign out successful');
            return { success: true };
        } catch (error) {
            console.error('Sign out failed:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Get current Firebase ID token
     */
    async getCurrentToken() {
        if (!this.currentUser) return null;
        
        try {
            return await this.currentUser.getIdToken();
        } catch (error) {
            console.error('Failed to get current token:', error);
            return null;
        }
    }

    /**
     * Check if user is currently authenticated
     */
    isAuthenticated() {
        return !!this.currentUser;
    }

    /**
     * Get current user info
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Register service worker for Firebase messaging
     */
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
                console.log('Service worker registered successfully:', registration);
                return registration;
            } catch (error) {
                console.error('Service worker registration failed:', error);
                return null;
            }
        } else {
            console.warn('Service workers not supported in this browser');
            return null;
        }
    }

    /**
     * Convert Firebase error to readable message
     */
    getReadableError(error) {
        switch (error.code) {
            case 'auth/user-not-found':
                return 'No account found with this email address.';
            case 'auth/wrong-password':
                return 'Incorrect password.';
            case 'auth/email-already-in-use':
                return 'An account with this email already exists.';
            case 'auth/weak-password':
                return 'Password should be at least 6 characters.';
            case 'auth/invalid-email':
                return 'Invalid email address.';
            case 'auth/too-many-requests':
                return 'Too many failed attempts. Please try again later.';
            default:
                return error.message || 'An error occurred during authentication.';
        }
    }
}

// Create global instance
window.firebaseAuth = new FirebaseAuthManager();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    await window.firebaseAuth.initialize();
});

// Login form handler
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const submitButton = loginForm.querySelector('button[type="submit"]');
            const errorDiv = document.getElementById('login-error');
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.textContent = 'Signing in...';
            if (errorDiv) errorDiv.style.display = 'none';
            
            try {
                const result = await window.firebaseAuth.signInWithEmail(email, password);
                
                if (result.success) {
                    // Send token to server for session creation
                    const token = await window.firebaseAuth.getCurrentToken();
                    const response = await fetch('/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ firebase_token: token })
                    });
                    
                    if (response.ok) {
                        console.log('Login successful');
                        // Redirect will happen automatically via auth state listener
                    } else {
                        throw new Error('Server authentication failed');
                    }
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                console.error('Login error:', error);
                if (errorDiv) {
                    errorDiv.textContent = error.message || 'Login failed. Please try again.';
                    errorDiv.style.display = 'block';
                }
            } finally {
                // Reset button state
                submitButton.disabled = false;
                submitButton.textContent = 'Sign In';
            }
        });
    }
});

// Logout handler
document.addEventListener('click', async (e) => {
    if (e.target.matches('[data-logout]')) {
        e.preventDefault();
        
        try {
            await window.firebaseAuth.signOut();
            
            // Also notify server
            await fetch('/logout', { method: 'POST' });
            
            // Redirect to login
            window.location.href = '/login';
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
});



// Export for use in other scripts
export default FirebaseAuthManager;