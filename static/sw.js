// Domus Planning Platform - Service Worker
// Progressive Web App functionality with offline support

const CACHE_NAME = 'domus-platform-v1.0.0';
const STATIC_CACHE = 'domus-static-v1.0.0';
const API_CACHE = 'domus-api-v1.0.0';
const IMAGE_CACHE = 'domus-images-v1.0.0';

// Core files to cache for offline functionality
const CORE_FILES = [
    '/',
    '/offline',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/manifest.json'
];

// Extended files for comprehensive offline experience
const EXTENDED_FILES = [
    '/projects',
    '/tasks', 
    '/planning-ai',
    '/communications',
    '/documents',
    '/reporting',
    '/mobile-optimization'
];

// API endpoints to cache
const API_ENDPOINTS = [
    '/api/dashboard/analytics',
    '/api/projects/list',
    '/api/tasks/list',
    '/api/notifications/list'
];

// Install event - cache core resources
self.addEventListener('install', event => {
    console.log('[SW] Installing service worker');
    
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache => {
                console.log('[SW] Caching core files');
                return cache.addAll(CORE_FILES);
            }),
            caches.open(CACHE_NAME).then(cache => {
                console.log('[SW] Caching extended files');
                return cache.addAll(EXTENDED_FILES);
            })
        ]).then(() => {
            console.log('[SW] Installation complete');
            return self.skipWaiting();
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[SW] Activating service worker');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && 
                        cacheName !== STATIC_CACHE && 
                        cacheName !== API_CACHE && 
                        cacheName !== IMAGE_CACHE) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Activation complete');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Handle API requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            caches.open(API_CACHE).then(cache => {
                return fetch(request).then(response => {
                    // Cache successful API responses
                    if (response.status === 200) {
                        cache.put(request, response.clone());
                    }
                    return response;
                }).catch(() => {
                    // Return cached API response if available
                    return cache.match(request).then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // Return offline API response
                        return new Response(JSON.stringify({
                            error: 'Offline',
                            message: 'This data is not available offline'
                        }), {
                            status: 503,
                            headers: { 'Content-Type': 'application/json' }
                        });
                    });
                });
            })
        );
        return;
    }
    
    // Handle image requests
    if (request.destination === 'image') {
        event.respondWith(
            caches.open(IMAGE_CACHE).then(cache => {
                return cache.match(request).then(cachedResponse => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    
                    return fetch(request).then(response => {
                        if (response.status === 200) {
                            cache.put(request, response.clone());
                        }
                        return response;
                    }).catch(() => {
                        // Return placeholder image for offline
                        return new Response(`
                            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
                                <rect width="200" height="200" fill="#f3f4f6"/>
                                <text x="100" y="100" text-anchor="middle" dy=".3em" fill="#9ca3af">Offline</text>
                            </svg>
                        `, {
                            headers: { 'Content-Type': 'image/svg+xml' }
                        });
                    });
                });
            })
        );
        return;
    }
    
    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(() => {
                // Check if we have the page cached
                return caches.match(request).then(cachedResponse => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // Return offline page
                    return caches.match('/offline');
                });
            })
        );
        return;
    }
    
    // Handle other requests with cache-first strategy
    event.respondWith(
        caches.match(request).then(cachedResponse => {
            if (cachedResponse) {
                return cachedResponse;
            }
            
            return fetch(request).then(response => {
                // Cache successful responses
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(STATIC_CACHE).then(cache => {
                        cache.put(request, responseClone);
                    });
                }
                return response;
            });
        })
    );
});

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('[SW] Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

function doBackgroundSync() {
    return new Promise((resolve) => {
        // Get pending actions from IndexedDB or localStorage
        // Process offline actions when connection is restored
        console.log('[SW] Processing background sync');
        resolve();
    });
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('[SW] Push notification received');
    
    const options = {
        body: 'You have new updates in your Domus Planning Platform',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            timestamp: Date.now(),
            url: '/'
        },
        actions: [
            {
                action: 'open',
                title: 'Open App',
                icon: '/static/icons/icon-192x192.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/icons/icon-192x192.png'
            }
        ]
    };
    
    if (event.data) {
        const payload = event.data.json();
        options.body = payload.body || options.body;
        options.title = payload.title || 'Domus Planning Platform';
        options.data = { ...options.data, ...payload.data };
    }
    
    event.waitUntil(
        self.registration.showNotification('Domus Planning Platform', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    console.log('[SW] Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'close') {
        return;
    }
    
    // Open or focus the app
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(clientList => {
            // Check if app is already open
            for (const client of clientList) {
                if (client.url.includes(self.location.origin) && 'focus' in client) {
                    return client.focus();
                }
            }
            // Open new window if app is not open
            if (clients.openWindow) {
                const url = event.notification.data?.url || '/';
                return clients.openWindow(url);
            }
        })
    );
});

// Message handling for communication with main thread
self.addEventListener('message', event => {
    console.log('[SW] Message received:', event.data);
    
    if (event.data && event.data.type) {
        switch (event.data.type) {
            case 'SKIP_WAITING':
                self.skipWaiting();
                break;
            case 'CACHE_URLS':
                event.waitUntil(
                    caches.open(CACHE_NAME).then(cache => {
                        return cache.addAll(event.data.urls);
                    })
                );
                break;
            case 'CLEAR_CACHE':
                event.waitUntil(
                    caches.keys().then(cacheNames => {
                        return Promise.all(
                            cacheNames.map(cacheName => caches.delete(cacheName))
                        );
                    })
                );
                break;
            case 'GET_CACHE_INFO':
                getCacheInfo().then(info => {
                    event.ports[0].postMessage(info);
                });
                break;
        }
    }
});

// Get cache information
async function getCacheInfo() {
    const cacheNames = await caches.keys();
    const cacheInfo = {};
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        cacheInfo[cacheName] = {
            size: keys.length,
            urls: keys.map(request => request.url)
        };
    }
    
    return cacheInfo;
}

// Periodic background sync (if supported)
if ('serviceWorker' in navigator && 'periodicSync' in window.ServiceWorkerRegistration.prototype) {
    self.addEventListener('periodicsync', event => {
        console.log('[SW] Periodic sync triggered:', event.tag);
        
        if (event.tag === 'content-sync') {
            event.waitUntil(syncContent());
        }
    });
}

function syncContent() {
    return fetch('/api/sync/content')
        .then(response => response.json())
        .then(data => {
            console.log('[SW] Content synced:', data);
            return caches.open(API_CACHE).then(cache => {
                return cache.put('/api/sync/content', new Response(JSON.stringify(data)));
            });
        })
        .catch(error => {
            console.error('[SW] Content sync failed:', error);
        });
}

console.log('[SW] Service worker script loaded');