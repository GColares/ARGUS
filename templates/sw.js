const CACHE_NAME = 'argus-static-v1';
const OFFLINE_URL = '/offline/';
const STATIC_ASSETS = [
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    '/static/css/argus-design-system.css',
    '/static/css/style.css',
    '/static/vendor/fontawesome/css/all.min.css',
    '/static/img/logo-inova-para-fundo-branco-editado.png',
    '/static/img/ARGUS1-LOGO-editado.png',
    '/static/img/nova_identidade/argus_profile_192x192.jpg',
    '/static/img/nova_identidade/argus_profile_512x512.jpg',
    OFFLINE_URL
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            await Promise.all(STATIC_ASSETS.map(async asset => {
                const response = await fetch(asset, { mode: 'no-cors' });
                if (response.ok || response.type === 'opaque') {
                    await cache.put(asset, response);
                }
            }));
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => Promise.all(
            cacheNames
                .filter(cacheName => (
                    cacheName.startsWith('argus-static-') &&
                    cacheName !== CACHE_NAME
                ))
                .map(cacheName => caches.delete(cacheName))
        ))
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    const request = event.request;

    if (request.method !== 'GET') {
        return;
    }

    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(error => {
                if (error instanceof TypeError) {
                    return caches.match(OFFLINE_URL);
                }
                throw error;
            })
        );
        return;
    }

    event.respondWith(fetch(request));
});
