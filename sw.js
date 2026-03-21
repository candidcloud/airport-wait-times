const CACHE_NAME = 'wait-times-cache-v2';
const ASSETS_TO_CACHE = [
  './index.html',
  './manifest.json',
  'https://placehold.co/192x192/0263e0/ffffff.png?text=✈️',
  'https://placehold.co/512x512/0263e0/ffffff.png?text=✈️'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('data.json')) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});