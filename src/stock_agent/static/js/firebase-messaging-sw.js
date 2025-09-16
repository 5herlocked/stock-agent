// Firebase Cloud Messaging Service Worker
// Simplified version following Firebase documentation

// Import Firebase scripts (compat version for service workers)
importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-messaging-compat.js');

// Initialize Firebase with config from server
let messaging = null;

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
    
    // Get messaging instance
    messaging = firebase.messaging();
    
    console.log('[firebase-messaging-sw.js] Firebase initialized successfully');
    return messaging;
  } catch (error) {
    console.error('[firebase-messaging-sw.js] Failed to initialize Firebase:', error);
    return null;
  }
}

// Initialize Firebase when service worker starts
initializeFirebaseMessaging();

// Set up background message handler after initialization
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

// Service worker lifecycle events
self.addEventListener('install', (event) => {
  console.log('[firebase-messaging-sw.js] Service worker installing.');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[firebase-messaging-sw.js] Service worker activating.');
  event.waitUntil(self.clients.claim());
});