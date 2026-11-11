// Offline shell: cache our own files only, never anything cross-origin. Bump VERSION on change.
const VERSION = 'bhasha-kids-v1';
const SHELL = ['./', 'index.html', 'app.css', 'app.js', 'vendor/tokens.css', 'manifest.webmanifest', 'icon.svg',
  'src/srs.js', 'src/progress.js', 'src/lessons.js', 'src/gate.js', 'src/match.js', 'src/storage.js', 'src/speech.js',
  'data/te.json', 'data/hi.json',
  'fonts/rozha-one-latin-400-normal.woff', 'fonts/anek-latin-latin-600-normal.woff', 'fonts/anek-latin-latin-700-normal.woff',
  'fonts/anek-telugu-telugu-400-normal.woff', 'fonts/anek-telugu-telugu-700-normal.woff', 'fonts/anek-devanagari-devanagari-700-normal.woff'];
self.addEventListener('install', e => e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys()
  .then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== self.location.origin) return;
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
    if (r.ok) { const copy = r.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); }
    return r;
  }).catch(() => caches.match('index.html'))));
});
