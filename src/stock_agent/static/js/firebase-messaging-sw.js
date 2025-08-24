// Enhanced Firebase Configuration Service Worker with Authentication Support

let sessionToken = null;
let firebaseConfig = null;
let messaging = null;

// Listen for messages from the main thread (for session token updates)
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "UPDATE_SESSION_TOKEN") {
    sessionToken = event.data.token;
    console.log("Service worker received updated session token");

    // If we don't have Firebase config yet, try to fetch it now that we have a token
    if (!firebaseConfig && sessionToken) {
      initializeMessaging();
    }
  } else if (event.data && event.data.type === "CLEAR_SESSION_TOKEN") {
    sessionToken = null;
    firebaseConfig = null;
    messaging = null;
    console.log("Service worker session token cleared");

    // Clear stored session token from IndexedDB
    clearStoredSessionToken().catch((error) => {
      console.error(
        "Failed to clear stored session token in service worker:",
        error,
      );
    });
  }
});

// Store session token in IndexedDB for persistence across service worker restarts
async function storeSessionToken(token) {
  try {
    const db = await openDB();
    const transaction = db.transaction(["auth"], "readwrite");
    const store = transaction.objectStore("auth");
    await store.put({ id: "session_token", value: token });
    sessionToken = token;
  } catch (error) {
    console.error("Failed to store session token:", error);
  }
}

// Retrieve session token from IndexedDB
async function getStoredSessionToken() {
  try {
    const db = await openDB();
    const transaction = db.transaction(["auth"], "readonly");
    const store = transaction.objectStore("auth");
    const result = await store.get("session_token");
    return result?.value || null;
  } catch (error) {
    console.error("Failed to retrieve session token:", error);
    return null;
  }
}

// Open IndexedDB for token storage
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("StockAgentAuth", 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains("auth")) {
        db.createObjectStore("auth", { keyPath: "id" });
      }
    };
  });
}

// Fetch Firebase configuration from the server with authentication
async function fetchFirebaseConfig() {
  try {
    // Try to get session token from memory first, then from IndexedDB
    let token = sessionToken;
    if (!token) {
      token = await getStoredSessionToken();
      sessionToken = token;
    }

    if (!token) {
      throw new Error("No session token available for authentication");
    }

    const response = await fetch("/api/firebase-config", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token might be expired, clear it
        sessionToken = null;
        await clearStoredSessionToken();
        throw new Error("Session token expired or invalid");
      }
      throw new Error(
        `Failed to fetch Firebase configuration: ${response.status}`,
      );
    }

    const config = await response.json();
    firebaseConfig = config;
    return config;
  } catch (error) {
    console.error("Error fetching Firebase configuration:", error);
    throw error;
  }
}

// Clear stored session token
async function clearStoredSessionToken() {
  try {
    const db = await openDB();
    const transaction = db.transaction(["auth"], "readwrite");
    const store = transaction.objectStore("auth");
    await store.delete("session_token");
  } catch (error) {
    console.error("Failed to clear session token:", error);
  }
}

// Fetch VAPID public key with authentication
async function fetchVapidPublicKey() {
  try {
    let token = sessionToken;
    if (!token) {
      token = await getStoredSessionToken();
      sessionToken = token;
    }

    if (!token) {
      throw new Error("No session token available for authentication");
    }

    const response = await fetch("/api/vapid-public-key", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionToken = null;
        await clearStoredSessionToken();
        throw new Error("Session token expired or invalid");
      }
      throw new Error(`Failed to fetch VAPID key: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching VAPID public key:", error);
    throw error;
  }
}

// Initialize Firebase and handle messaging after config is loaded
async function initializeMessaging() {
  try {
    // Import Firebase scripts dynamically
    importScripts(
      "https://www.gstatic.com/firebasejs/12.1.0/firebase-app-compat.js",
    );
    importScripts(
      "https://www.gstatic.com/firebasejs/12.1.0/firebase-messaging-compat.js",
    );

    // Fetch configuration from server with authentication
    if (!firebaseConfig) {
      firebaseConfig = await fetchFirebaseConfig();
    }

    // Initialize Firebase with fetched config
    firebase.initializeApp(firebaseConfig);

    // Get messaging instance
    messaging = firebase.messaging();

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

    console.log("Firebase messaging initialized successfully");
  } catch (error) {
    console.error("Failed to initialize Firebase messaging:", error);

    // If authentication failed, notify the main thread
    if (error.message.includes("token") || error.message.includes("401")) {
      // Broadcast to all clients that authentication is needed
      clients.matchAll().then((clientList) => {
        clientList.forEach((client) => {
          client.postMessage({
            type: "AUTH_REQUIRED",
            message: "Service worker authentication failed",
          });
        });
      });
    }
  }
}

// Handle service worker activation
self.addEventListener("activate", async (event) => {
  console.log("Service worker activated");

  // Try to load existing session token
  event.waitUntil(
    (async () => {
      const token = await getStoredSessionToken();
      if (token) {
        sessionToken = token;
        // Try to initialize messaging with existing token
        await initializeMessaging();
      }
    })(),
  );
});

// Handle service worker installation
self.addEventListener("install", (event) => {
  console.log("Service worker installed");
  self.skipWaiting();
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

// Periodic token refresh (optional - for long-running service workers)
setInterval(async () => {
  if (sessionToken) {
    try {
      // Test token validity with a simple API call
      const response = await fetch("/api/vapid-public-key", {
        headers: {
          Authorization: `Bearer ${sessionToken}`,
        },
      });

      if (response.status === 401) {
        // Token expired, clear it and notify clients
        sessionToken = null;
        await clearStoredSessionToken();

        clients.matchAll().then((clientList) => {
          clientList.forEach((client) => {
            client.postMessage({
              type: "AUTH_REQUIRED",
              message: "Session token expired",
            });
          });
        });
      }
    } catch (error) {
      console.error("Token validation error:", error);
    }
  }
}, 300000); // Check every 5 minutes
