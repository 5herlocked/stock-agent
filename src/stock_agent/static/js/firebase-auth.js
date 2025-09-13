/**
 * Firebase Authentication Module for Stock Agent
 * Handles Firebase Auth integration and service worker communication
 */

import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-app.js';
import { 
    getAuth, 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword,
    signOut, 
    onAuthStateChanged,
    updateProfile
} from 'https://www.gstatic.com/firebasejs/12.1.0/firebase-auth.js';

class FirebaseAuthManager {
    constructor() {
        this.app = null;
        this.auth = null;
        this.currentUser = null;
        this.serviceWorkerRegistration = null;
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
                throw new Error('Failed to load Firebase config');
            }
            
            const firebaseConfig = await response.json();
            
            // Initialize Firebase
            this.app = initializeApp(firebaseConfig);
            this.auth = getAuth(this.app);
            
            // Set up auth state listener
            onAuthStateChanged(this.auth, (user) => {
                this.currentUser = user;
                this.handleAuthStateChange(user);
            });
            
            // Register service worker
            await this.registerServiceWorker();
            
            this.initialized = true;
            console.log('Firebase Auth initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize Firebase Auth:', error);
            throw error;
        }
    }

    /**
     * Register Firebase Auth service worker
     */
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                this.serviceWorkerRegistration = await navigator.serviceWorker.register('/firebase-auth-sw.js');
                console.log('Firebase Auth Service Worker registered successfully');
                
                // Wait for service worker to be ready
                await navigator.serviceWorker.ready;
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    /**
     * Handle authentication state changes
     */
    handleAuthStateChange(user) {
        if (user) {
            console.log('User signed in:', user.email);
            this.updateUIForSignedInUser(user);
        } else {
            console.log('User signed out');
            this.updateUIForSignedOutUser();
        }
    }

    /**
     * Sign in with email and password
     */
    async signIn(email, password) {
        try {
            const userCredential = await signInWithEmailAndPassword(this.auth, email, password);
            return userCredential.user;
        } catch (error) {
            console.error('Sign in error:', error);
            throw this.getReadableError(error);
        }
    }

    /**
     * Create account with email and password
     */
    async createAccount(email, password, displayName = '') {
        try {
            const userCredential = await createUserWithEmailAndPassword(this.auth, email, password);
            
            // Update display name if provided
            if (displayName) {
                await updateProfile(userCredential.user, {
                    displayName: displayName
                });
            }
            
            return userCredential.user;
        } catch (error) {
            console.error('Account creation error:', error);
            throw this.getReadableError(error);
        }
    }

    /**
     * Sign out current user
     */
    async signOut() {
        try {
            await signOut(this.auth);
        } catch (error) {
            console.error('Sign out error:', error);
            throw error;
        }
    }

    /**
     * Get current user's ID token
     */
    async getIdToken() {
        if (this.currentUser) {
            try {
                return await this.currentUser.getIdToken();
            } catch (error) {
                console.error('Error getting ID token:', error);
                return null;
            }
        }
        return null;
    }

    /**
     * Check if user is signed in
     */
    isSignedIn() {
        return this.currentUser !== null;
    }

    /**
     * Get current user info
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Update UI for signed in user
     */
    updateUIForSignedInUser(user) {
        // Update user info display
        const userInfoElements = document.querySelectorAll('.user-info');
        userInfoElements.forEach(element => {
            const displayName = user.displayName || user.email.split('@')[0];
            element.innerHTML = `
                Welcome, ${displayName}!
                <button onclick="firebaseAuth.signOut()" class="logout-btn">Logout</button>
            `;
        });

        // Hide login forms
        const loginForms = document.querySelectorAll('.login-form');
        loginForms.forEach(form => form.style.display = 'none');

        // Show authenticated content
        const authContent = document.querySelectorAll('.auth-content');
        authContent.forEach(content => content.style.display = 'block');

        // Update page title if on login page
        if (window.location.pathname === '/login') {
            document.title = 'Welcome - Stock Agent';
        }
    }

    /**
     * Update UI for signed out user
     */
    updateUIForSignedOutUser() {
        // Clear user info
        const userInfoElements = document.querySelectorAll('.user-info');
        userInfoElements.forEach(element => {
            element.innerHTML = '';
        });

        // Show login forms
        const loginForms = document.querySelectorAll('.login-form');
        loginForms.forEach(form => form.style.display = 'block');

        // Hide authenticated content
        const authContent = document.querySelectorAll('.auth-content');
        authContent.forEach(content => content.style.display = 'none');

        // Redirect to login if on protected page
        if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
            window.location.href = '/login';
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

    /**
     * Make authenticated API request
     */
    async makeAuthenticatedRequest(url, options = {}) {
        const idToken = await this.getIdToken();
        
        if (!idToken) {
            throw new Error('No authentication token available');
        }

        const headers = {
            'Authorization': `Bearer ${idToken}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        return fetch(url, {
            ...options,
            headers
        });
    }
}

// Create global instance
window.firebaseAuth = new FirebaseAuthManager();

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.firebaseAuth.initialize();
    } catch (error) {
        console.error('Failed to initialize Firebase Auth:', error);
        // Fallback to legacy authentication if Firebase fails
        console.log('Falling back to legacy authentication');
    }
});

// Export for module usage
export default FirebaseAuthManager;