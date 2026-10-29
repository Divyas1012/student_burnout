/**
 * sw.js - Service Worker for MindPulse AI Progressive Web App
 * Provides offline caching, resilient asset delivery, and PWA install capabilities.
 */

const CACHE_NAME = "mindpulse-pwa-v1";

const PRECACHE_ASSETS = [
  "/",
  "/manifest.json",
  "/offline.html",
  "/static/css/styles.css",
  "/static/js/api.js",
  "/static/js/app.js",
  "/static/js/charts.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/icon-maskable-192.png",
  "/static/icons/icon-maskable-512.png",
  "/static/icons/icon.svg",
  "/static/icons/apple-touch-icon.png",
  "/static/icons/favicon-32.png"
];

// Install Event - Pre-cache critical app shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[ServiceWorker] Pre-caching app shell");
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn("[ServiceWorker] Pre-cache warning:", err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate Event - Clean up outdated caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[ServiceWorker] Removing old cache:", key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event - Stale-while-revalidate for static assets, network-first for navigation
self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Ignore non-GET requests or browser-extension schemes
  if (req.method !== "GET" || !url.protocol.startsWith("http")) {
    return;
  }

  // API calls: Network-first, fallback to offline response if offline
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(req).catch(() => {
        return new Response(
          JSON.stringify({
            error: "offline",
            message: "You are currently offline. Synced data will refresh once connection is restored."
          }),
          {
            status: 503,
            headers: { "Content-Type": "application/json" }
          }
        );
      })
    );
    return;
  }

  // HTML Navigation requests: Network first with offline fallback
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, responseClone));
          }
          return networkResponse;
        })
        .catch(async () => {
          const cachedResponse = await caches.match(req);
          if (cachedResponse) return cachedResponse;
          return caches.match("/offline.html");
        })
    );
    return;
  }

  // Static Assets (CSS, JS, Fonts, Images): Cache First with background update
  event.respondWith(
    caches.match(req).then((cachedResponse) => {
      const fetchPromise = fetch(req)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, responseClone));
          }
          return networkResponse;
        })
        .catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
