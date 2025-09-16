// Firebase Cloud Messaging Service Worker
// Simplified version following Firebase documentation

// Import Firebase scripts (compat version for service workers)
importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-auth-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-messaging-compat.js');

// Initialize Firebase with config from server
let messaging = null;
let auth = null;

// Fetch Firebase config and initialize
async function initializeFirebaseMessaging() {
  try {
    // Fetch Firebase config from public endpoint
    const response = await fetch('/api/firebase-config-public');
    if (!response.ok) {
      throw new Error('Failed to fetch Firebase config');
    }
    
    const firebaseConfig = await response.json();
    
    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    
    // Get messaging and auth instances
    messaging = firebase.messaging();
    auth = firebase.auth();
    
    console.log('[firebase-messaging-sw.js] Firebase initialized successfully');
    return messaging;
  } catch (error) {
    console.error('[firebase-messaging-sw.js] Failed to initialize Firebase:', error);
    return null;
  }
}

// Initialize Firebase when service worker starts
initializeFirebaseMessaging();

// Function to get device token and subscribe to notifications
async function subscribeToNotifications(messaging) {
  try {
    // Get VAPID key from server if available
    let vapidKey = null;
    try {
      const vapidResponse = await fetch('/api/firebase-config-public');
      if (vapidResponse.ok) {
        const config = await vapidResponse.json();
        // VAPID key would be in environment, but for now proceed without it
        console.log('[firebase-messaging-sw.js] Firebase config loaded');
      }
    } catch (error) {
      console.log('[firebase-messaging-sw.js] Could not get Firebase config');
    }
    
    // Get registration token (without VAPID key for now)
    const token = await messaging.getToken();
    
    if (token) {
      console.log('[firebase-messaging-sw.js] Registration token obtained:', token);
      
      // Subscribe to stock_update topic
      // The fetch will be intercepted by our request interceptor which adds auth headers
      const response = await fetch('/api/notifications/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token: token })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('[firebase-messaging-sw.js] Successfully subscribed to notifications:', result);
      } else {
        console.error('[firebase-messaging-sw.js] Failed to subscribe to notifications:', response.status);
        const errorText = await response.text();
        console.error('[firebase-messaging-sw.js] Error details:', errorText);
      }
    } else {
      console.log('[firebase-messaging-sw.js] No registration token available');
    }
  } catch (error) {
    console.error('[firebase-messaging-sw.js] Error getting token or subscribing:', error);
  }
}

// Set up background message handler and token subscription after initialization
initializeFirebaseMessaging().then((messaging) => {
  if (messaging) {
    // Handle background messages
    messaging.onBackgroundMessage((payload) => {
      console.log('[firebase-messaging-sw.js] Received background message ', payload);
      
      // Customize notification here
      const notificationTitle = payload.notification?.title || 'Stock Agent';
      const notificationOptions = {
        body: payload.notification?.body || 'You have a new stock update',
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/notification-badge.png',
        data: payload.data || {},
        tag: payload.data?.type || 'stock-alert',
        requireInteraction: false
      };

      self.registration.showNotification(notificationTitle, notificationOptions);
    });
    
    // Subscribe to notifications when service worker is ready
    subscribeToNotifications(messaging);
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[firebase-messaging-sw.js] Notification click received.');

  event.notification.close();

  // Handle click action
  const clickAction = event.notification.data?.clickAction || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Check if there's already a window/tab open with the target URL
        for (const client of windowClients) {
          if (client.url === clickAction && 'focus' in client) {
            return client.focus();
          }
        }
        // If not, open a new window/tab with the target URL
        if (clients.openWindow) {
          return clients.openWindow(clickAction);
        }
      })
  );
});

// Firebase service worker sessions pattern - intercept requests and add auth headers
self.addEventListener('fetch', (event) => {
  const { origin, pathname } = new URL(event.request.url);
  
  // Only intercept same-origin requests to API endpoints
  if (origin !== self.location.origin || !pathname.startsWith('/api/')) {
    return;
  }
  
  event.respondWith(
    (async () => {
      try {
        // Get current Firebase user and ID token
        let idToken = null;
        if (auth && auth.currentUser) {
          idToken = await auth.currentUser.getIdToken();
        }
        
        // Clone the request and add Authorization header if we have a token
        const modifiedRequest = new Request(event.request, {
          headers: {
            ...Object.fromEntries(event.request.headers.entries()),
            ...(idToken && { 'Authorization': `Bearer ${idToken}` })
          }
        });
        
        return fetch(modifiedRequest);
      } catch (error) {
        console.error('[firebase-messaging-sw.js] Error in fetch interceptor:', error);
        // Fall back to original request
        return fetch(event.request);
      }
    })()
  );
});

// Service worker lifecycle events
self.addEventListener('install', (event) => {
  console.log('[firebase-messaging-sw.js] Service worker installing.');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[firebase-messaging-sw.js] Service worker activating.');
  event.waitUntil(self.clients.claim());
});