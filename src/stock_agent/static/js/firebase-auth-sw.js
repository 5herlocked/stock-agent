// Simplified Firebase Service Worker for HTMX Integration
// Handles Firebase messaging and minimal token management

// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-messaging-compat.js');

// Firebase configuration will be loaded dynamically
let firebaseConfig = null;
let messaging = null;

/**
 * Get the origin from a URL
 */
const getOriginFromUrl = (url) => {
  const pathArray = url.split('/');
  const protocol = pathArray[0];
  const host = pathArray[2];
  return protocol + '//' + host;
};

/**
 * Get underlying body if available. Works for text and json bodies.
 */
const getBodyContent = (req) => {
  return Promise.resolve().then(() => {
    if (req.method !== 'GET') {
      if (req.headers.get('Content-Type') && req.headers.get('Content-Type').indexOf('json') !== -1) {
        return req.json()
          .then((json) => {
            return JSON.stringify(json);
          });
      } else {
        return req.text();
      }
    }
  }).catch((error) => {
    // Ignore error.
    console.warn('Error reading request body:', error);
  });
};

/**
 * Check if we should append Firebase ID token to this request
 */
const shouldAppendToken = (requestUrl) => {
  // Only append token to same-origin requests
  const requestOrigin = getOriginFromUrl(requestUrl);
  const serviceWorkerOrigin = self.location.origin;
  
  // Must be same origin and HTTPS (or localhost)
  return requestOrigin === serviceWorkerOrigin && 
         (self.location.protocol === 'https:' || self.location.hostname === 'localhost');
};

/**
 * Clone request and add Firebase ID token to Authorization header
 */
const cloneRequestWithToken = (req, idToken) => {
  return getBodyContent(req).then((body) => {
    try {
      // Clone headers as request headers are immutable
      const headers = new Headers();
      req.headers.forEach((val, key) => {
        headers.append(key, val);
      });
      
      // Add Firebase ID token to header
      headers.append('Authorization', 'Bearer ' + idToken);
      
      // Create new request with token
      return new Request(req.url, {
        method: req.method,
        headers: headers,
        mode: 'same-origin',
        credentials: req.credentials,
        cache: req.cache,
        redirect: req.redirect,
        referrer: req.referrer,
        body: body
      });
    } catch (e) {
      console.warn('Failed to clone request with token:', e);
      // Return original request if cloning fails
      return req;
    }
  });
};

/**
 * Initialize Firebase with configuration
 */
const initializeFirebase = async () => {
  try {
    // Try to get Firebase config from a public endpoint (no auth required)
    const response = await fetch('/api/firebase-config-public');
    
    if (response.ok) {
      firebaseConfig = await response.json();
      
      // Initialize Firebase
      firebase.initializeApp(firebaseConfig);
      
      // Initialize messaging
      messaging = firebase.messaging();
      
      // Handle background messages
      messaging.onBackgroundMessage((payload) => {
        console.log('Received background message:', payload);
        
        const notificationTitle = payload.notification?.title || 'Stock Agent Notification';
        const notificationOptions = {
          body: payload.notification?.body || 'You have a new stock update',
          icon: '/static/images/notification-icon.png',
          badge: '/static/images/notification-badge.png',
          data: payload.data || {},
          vibrate: [200, 100, 200],
          tag: payload.data?.type || 'stock-alert',
          renotify: true,
        };
        
        return self.registration.showNotification(notificationTitle, notificationOptions);
      });
      
      console.log('Firebase initialized successfully in service worker');
    } else {
      console.warn('Failed to load Firebase config, will try with authenticated request later');
    }
  } catch (error) {
    console.warn('Failed to initialize Firebase:', error);
  }
};

// Main fetch event listener - Firebase's recommended pattern
self.addEventListener('fetch', (event) => {
  const requestProcessor = (idToken) => {
    let req = event.request;
    let processRequestPromise = Promise.resolve();
    
    // For same origin requests, append Firebase ID token if available
    if (shouldAppendToken(event.request.url) && idToken) {
      processRequestPromise = cloneRequestWithToken(req, idToken).then((newReq) => {
        req = newReq;
      });
    }
    
    return processRequestPromise.then(() => {
      return fetch(req);
    });
  };
  
  // Fetch the resource after checking for the ID token
  // This can also be integrated with existing logic to serve cached files in offline mode
  event.respondWith(getIdTokenPromise().then(requestProcessor, requestProcessor));
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  // Default to home page if no specific action
  const clickAction = event.notification.data?.clickAction || '/';
  
  // Open or focus the appropriate window
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        for (let client of windowClients) {
          if (client.url.includes(new URL(clickAction, self.location).pathname) && 'focus' in client) {
            return client.focus();
          }
        }
        return clients.openWindow(clickAction);
      })
  );
});

// Handle push events (backup in case onBackgroundMessage doesn't work)
self.addEventListener('push', (event) => {
  console.log('Received push event:', event);
  
  if (event.data) {
    try {
      const payload = event.data.json();
      
      const notificationTitle = payload.notification?.title || 'Stock Agent Notification';
      const notificationOptions = {
        body: payload.notification?.body || 'You have a new stock update',
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/notification-badge.png',
        data: payload.data || {},
        vibrate: [200, 100, 200],
        tag: payload.data?.type || 'stock-alert',
        renotify: true,
      };
      
      event.waitUntil(
        self.registration.showNotification(notificationTitle, notificationOptions)
      );
    } catch (error) {
      console.error('Error handling push event:', error);
      
      // Fallback notification
      event.waitUntil(
        self.registration.showNotification('Stock Agent', {
          body: 'You have a new notification',
          icon: '/static/images/notification-icon.png',
        })
      );
    }
  }
});

// Handle service worker activation
self.addEventListener('activate', async (event) => {
  console.log('Firebase Auth Service worker activated');
  
  // Initialize Firebase when service worker activates
  event.waitUntil(initializeFirebase());
});

// Handle service worker installation
self.addEventListener('install', (event) => {
  console.log('Firebase Auth Service worker installed');
  self.skipWaiting();
});

// Listen for messages from the main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'FIREBASE_CONFIG') {
    // Receive Firebase config from main thread if needed
    firebaseConfig = event.data.config;
    
    if (!firebase.apps.length) {
      firebase.initializeApp(firebaseConfig);
      messaging = firebase.messaging();
      console.log('Firebase initialized from main thread config');
    }
  }
});