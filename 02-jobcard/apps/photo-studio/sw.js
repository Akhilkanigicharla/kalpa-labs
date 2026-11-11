// Offline shell for Kalpa Photo Studio. Caches only the app's own files; photos are never cached or sent.
const CACHE = 'kalpa-photo-studio-v1';
const SHELL = ['./', 'index.html', 'styles.css', 'tokens.css', 'app.js', 'core.mjs', 'specs.json', 'manifest.webmanifest', 'icons/icon.svg',
  'fonts/rozha-one-latin-400-normal.woff', 'fonts/anek-latin-latin-600-normal.woff', 'fonts/anek-latin-latin-700-normal.woff'];
self.addEventListener('install', e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys()
  .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return;
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)));
});
