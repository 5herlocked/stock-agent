// Dynamic Firebase Configuration Service Worker

// Fetch Firebase configuration from the server
async function fetchFirebaseConfig() {
  try {
    const response = await fetch("/api/firebase-config");
    if (!response.ok) {
      throw new Error("Failed to fetch Firebase configuration");
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching Firebase configuration:", error);
    throw error;
  }
}

// Initialize Firebase and handle messaging after config is loaded
async function initializeMessaging() {
  // Import Firebase scripts dynamically
  importScripts(
    "https://www.gstatic.com/firebasejs/12.1.0/firebase-app-compat.js",
  );
  importScripts(
    "https://www.gstatic.com/firebasejs/12.1.0/firebase-messaging-compat.js",
  );

  try {
    // Fetch configuration from server
    const firebaseConfig = await fetchFirebaseConfig();

    // Initialize Firebase with fetched config
    firebase.initializeApp(firebaseConfig);

    // Get messaging instance
    const messaging = firebase.messaging();

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
              if (client.url === clickAction && "focus" in client) {
                return client.focus();
              }
            }
            return clients.openWindow(clickAction);
          }),
      );
    });
  } catch (error) {
    console.error("Failed to initialize Firebase messaging:", error);
  }
}

// Start initialization
initializeMessaging();
