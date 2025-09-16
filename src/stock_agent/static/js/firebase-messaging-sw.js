// Firebase Service Worker with Authentication and Messaging
// Implements Firebase service worker sessions pattern

let firebaseApp = null;
let firebaseAuth = null;
let messaging = null;
let firebaseConfig = null;

/**
 * Returns a promise that resolves with an ID token if available.
 * @return {!Promise<?string>} The promise that resolves with an ID token if
 *     available. Otherwise, the promise resolves with null.
 */
const getIdTokenPromise = () => {
  return new Promise((resolve, reject) => {
    if (!firebaseAuth) {
      resolve(null);
      return;
    }
    
    const unsubscribe = firebaseAuth.onAuthStateChanged((user) => {
      unsubscribe();
      if (user) {
        user.getIdToken().then((idToken) => {
          resolve(idToken);
        }, (error) => {
          console.error('Error getting ID token:', error);
          resolve(null);
        });
      } else {
        resolve(null);
      }
    });
  });
};

// Fetch Firebase configuration from the public endpoint
async function fetchFirebaseConfig() {
  try {
    const response = await fetch("/api/firebase-config-public");
    
    if (!response.ok) {
      throw new Error(`Failed to fetch Firebase configuration: ${response.status}`);
    }

    const config = await response.json();
    firebaseConfig = config;
    return config;
  } catch (error) {
    console.error("Error fetching Firebase configuration:", error);
    throw error;
  }
}

// Helper functions for request processing
const getOriginFromUrl = (url) => {
  const pathArray = url.split('/');
  const protocol = pathArray[0];
  const host = pathArray[2];
  return protocol + '//' + host;
};

// Get underlying body if available. Works for text and json bodies.
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
  });
};

// Initialize Firebase Auth and Messaging
async function initializeFirebase() {
    // Import Firebase scripts (compat version for service workers)
  importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-app-compat.js');
  importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-auth-compat.js');
  importScripts('https://www.gstatic.com/firebasejs/12.2.1/firebase-messaging-compat.js');
  try {
    // Fetch configuration from server
    if (!firebaseConfig) {
      firebaseConfig = await fetchFirebaseConfig();
    }

    // Initialize Firebase with fetched config (only if not already initialized)
    if (!firebaseApp) {
      firebaseApp = firebase.initializeApp(firebaseConfig);
      firebaseAuth = firebase.auth();
      messaging = firebase.messaging();
    }

    // Handle background messages
    messaging.onBackgroundMessage((payload) => {
      console.log("Received background message:", payload);

      // Default notification options
      const notificationTitle =
        payload.notification?.title || "Stock Agent Notification";
      const notificationOptions = {
        body: payload.notification?.body || "You have a new stock update",
        icon: "/static/images/notification-icon.png",
        badge: "/static/images/notification-badge.png",
        data: payload.data || {},
        vibrate: [200, 100, 200],
        tag: payload.data?.type || "stock-alert",
        renotify: true,
      };

      // Show the notification
      return self.registration.showNotification(
        notificationTitle,
        notificationOptions,
      );
    });

    // Handle notification clicks
    self.addEventListener("notificationclick", (event) => {
      event.notification.close();

      // Default to home page if no specific action
      const clickAction = event.notification.data?.clickAction || "/";

      // Open or focus the appropriate window
      event.waitUntil(
        clients
          .matchAll({ type: "window", includeUncontrolled: true })
          .then((windowClients) => {
            for (let client of windowClients) {
              if (
                client.url.includes(
                  new URL(clickAction, self.location).pathname,
                ) &&
                "focus" in client
              ) {
                return client.focus();
              }
            }
            return clients.openWindow(clickAction);
          }),
      );
    });

    console.log("Firebase initialized successfully in service worker");
  } catch (error) {
    console.error("Failed to initialize Firebase:", error);
  }
}

// Fetch event listener for automatic auth header injection
self.addEventListener('fetch', (event) => {
  const requestProcessor = (idToken) => {
    let req = event.request;
    let processRequestPromise = Promise.resolve();
    
    // For same origin https requests, append idToken to header.
    if (self.location.origin == getOriginFromUrl(event.request.url) &&
        (self.location.protocol == 'https:' ||
         self.location.hostname == 'localhost') &&
        idToken) {
      // Clone headers as request headers are immutable.
      const headers = new Headers();
      req.headers.forEach((val, key) => {
        headers.append(key, val);
      });
      // Add ID token to header.
      headers.append('Authorization', 'Bearer ' + idToken);
      
      processRequestPromise = getBodyContent(req).then((body) => {
        try {
          req = new Request(req.url, {
            method: req.method,
            headers: headers,
            mode: 'same-origin',
            credentials: req.credentials,
            cache: req.cache,
            redirect: req.redirect,
            referrer: req.referrer,
            body,
          });
        } catch (e) {
          // This will fail for CORS requests. We just continue with the
          // fetch caching logic below and do not pass the ID token.
        }
      });
    }
    return processRequestPromise.then(() => {
      return fetch(req);
    });
  };
  
  // Fetch the resource after checking for the ID token.
  event.respondWith(getIdTokenPromise().then(requestProcessor, requestProcessor));
});

// Handle service worker activation
self.addEventListener("activate", async (event) => {
  console.log("Service worker activated");
  
  // Initialize Firebase
  event.waitUntil(initializeFirebase());
});

// Handle service worker installation
self.addEventListener("install", (event) => {
  console.log("Service worker installed");
  self.skipWaiting();
  
  // Initialize Firebase on install
  event.waitUntil(initializeFirebase());
});

// Handle push events (backup in case onBackgroundMessage doesn't work)
self.addEventListener("push", (event) => {
  console.log("Received push event:", event);

  if (event.data) {
    try {
      const payload = event.data.json();

      const notificationTitle =
        payload.notification?.title || "Stock Agent Notification";
      const notificationOptions = {
        body: payload.notification?.body || "You have a new stock update",
        icon: "/static/images/notification-icon.png",
        badge: "/static/images/notification-badge.png",
        data: payload.data || {},
        vibrate: [200, 100, 200],
        tag: payload.data?.type || "stock-alert",
        renotify: true,
      };

      event.waitUntil(
        self.registration.showNotification(
          notificationTitle,
          notificationOptions,
        ),
      );
    } catch (error) {
      console.error("Error handling push event:", error);

      // Fallback notification
      event.waitUntil(
        self.registration.showNotification("Stock Agent", {
          body: "You have a new notification",
          icon: "/static/images/notification-icon.png",
        }),
      );
    }
  }
});

// Listen for messages from main thread (for coordination if needed)
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "PING") {
    // Respond to ping from main thread
    event.ports[0].postMessage({
      type: "PONG",
      authenticated: !!firebaseAuth?.currentUser
    });
  }
});
