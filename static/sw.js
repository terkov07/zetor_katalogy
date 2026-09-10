const CACHE_NAME = "zetorcat-shell-v1";
const SHELL_FILES = [
  "/static/css/app.css",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

// Caches only the app "shell" (styling, icons, manifest) — deliberately NOT
// trying to intercept and manage individual catalogue/section PDFs here.
// Those are handled as plain browser downloads instead (see the "stiahnuť"
// links in catalogue_detail.html) — far simpler and less likely to break
// than a service worker trying to guess which large PDFs to cache and when
// to evict them.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
});

self.addEventListener("fetch", (event) => {
  if (SHELL_FILES.includes(new URL(event.request.url).pathname)) {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
});