// JobCard PWA service worker (generated from sw.template.js by build.mjs). Shell = cache-first; data = network only.
const CACHE = "jobcard-__VERSION__";
const SHELL = __SHELL__;
self.addEventListener("install", (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", (e) => e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return; // Supabase calls go straight to the network
  if (e.request.mode === "navigate") { e.respondWith(fetch(e.request).catch(() => caches.match("/index.html"))); return; }
  e.respondWith(caches.match(u.pathname).then((hit) => hit || fetch(e.request)));
});
