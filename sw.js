// Service Worker Simples para PWA
const CACHE_NAME = 'hypertips-v1';
const urlsToCache = [
    './',
    './index.html',
    './style.css',
    './app.js',
    './favicon.png'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
