/**
 * HTMX Firebase Authentication - Minimal JavaScript following HTMX patterns
 * Based on: https://htmx.org/examples/async-auth/
 */

// Firebase imports
import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.2.1/firebase-app.js';
import { 
    getAuth, 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword,
    signOut, 
    onAuthStateChanged
} from 'https://www.gstatic.com/firebasejs/12.2.1/firebase-auth.js';

// Global auth state
let authToken = null;
let firebaseAuth = null;
let authPromise = null;

// Initialize Firebase and create auth promise
async function initializeFirebaseAuth() {
    try {
        // Get Firebase config
        const response = await fetch('/api/firebase-config-public');
        const firebaseConfig = await response.json();
        
        // Initialize Firebase
        const app = initializeApp(firebaseConfig);
        firebaseAuth = getAuth(app);
        
        // Create auth promise that resolves when we have a token or confirm no user
        authPromise = new Promise((resolve) => {
            onAuthStateChanged(firebaseAuth, async (user) => {
                if (user) {
                    try {
                        authToken = await user.getIdToken();
                        console.log('Firebase auth token obtained');
                        resolve(authToken);
                    } catch (error) {
                        console.error('Error getting ID token:', error);
                        authToken = null;
                        resolve(null);
                    }
                } else {
                    authToken = null;
                    resolve(null);
                }
            });
        });
        
        console.log('Firebase Auth initialized');
        return authPromise;
        
    } catch (error) {
        console.error('Firebase initialization failed:', error);
        authPromise = Promise.resolve(null);
        return authPromise;
    }
}

// HTMX Integration following the async auth pattern
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Firebase
    initializeFirebaseAuth();
    
    // Gate HTMX requests on the auth token (HTMX pattern)
    htmx.on("htmx:confirm", (e) => {
        // If there is no auth token and we need authentication
        if (authToken == null && !e.target.hasAttribute('data-no-auth')) {
            // Stop the regular request from being issued
            e.preventDefault();
            // Only issue it once the auth promise has resolved
            authPromise.then(() => {
                if (authToken) {
                    e.detail.issueRequest();
                } else {
                    // No auth token available, redirect to login
                    window.location.href = '/login';
                }
            });
        }
    });

    // Add the auth token to requests as a header (HTMX pattern)
    htmx.on("htmx:configRequest", (e) => {
        if (authToken && !e.target.hasAttribute('data-no-auth')) {
            e.detail.headers["Authorization"] = `Bearer ${authToken}`;
        }
    });

    // Handle auth state changes for UI updates
    if (authPromise) {
        authPromise.then((token) => {
            updateAuthUI(token !== null);
        });
    }
});

// Simple UI updates
function updateAuthUI(isAuthenticated) {
    // Update user info sections
    const userInfoElements = document.querySelectorAll('.user-info');
    userInfoElements.forEach(element => {
        if (isAuthenticated && firebaseAuth.currentUser) {
            const displayName = firebaseAuth.currentUser.displayName || 
                               firebaseAuth.currentUser.email.split('@')[0];
            element.innerHTML = `
                Welcome, ${displayName}!
                <button onclick="signOutUser()" class="logout-btn">Logout</button>
            `;
        } else {
            element.innerHTML = '';
        }
    });

    // Handle page-specific logic
    const currentPath = window.location.pathname;
    
    if (currentPath === '/login' && isAuthenticated) {
        // Redirect authenticated users away from login page
        window.location.href = '/';
    } else if (currentPath !== '/login' && !isAuthenticated) {
        // Redirect unauthenticated users to login
        window.location.href = '/login';
    }
}

// Global functions for forms
window.signInUser = async function(email, password) {
    try {
        await signInWithEmailAndPassword(firebaseAuth, email, password);
        return { success: true };
    } catch (error) {
        return { success: false, error: getReadableError(error) };
    }
};

window.createUserAccount = async function(email, password) {
    try {
        await createUserWithEmailAndPassword(firebaseAuth, email, password);
        return { success: true };
    } catch (error) {
        return { success: false, error: getReadableError(error) };
    }
};

window.signOutUser = async function() {
    try {
        await signOut(firebaseAuth);
        authToken = null;
        window.location.href = '/login';
    } catch (error) {
        console.error('Sign out error:', error);
    }
};

// Helper function for readable errors
function getReadableError(error) {
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