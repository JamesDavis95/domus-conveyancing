// Domus Professional Platform Service Worker
// Version 1.0.0 - Mobile Optimization & PWA Support

const CACHE_NAME = 'domus-platform-v1';
const OFFLINE_URL = '/offline';

// Resources to cache for offline functionality
const CACHE_RESOURCES = [
  '/',
  '/dashboard',
  '/projects',
  '/planning-ai',
  '/communications',
  '/documents',
  '/tasks',
  '/reporting-analytics',
  '/integration-ecosystem',
  '/offline',
  '/static/style.css',
  '        // Domus Planning Platform - Service Worker
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

console.log('[SW] Service worker script loaded');',
  // Core JavaScript files
  '/static/js/app.js',
  '/static/js/offline.js',
  '/static/js/notifications.js',
  // Essential icons
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  // Fonts and external resources
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/chart.js',
  // API endpoints for offline data
  '/api/dashboard',
  '/api/projects',
  '/api/notifications'
];

// Install event - cache essential resources
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching essential resources');
        return cache.addAll(CACHE_RESOURCES);
      })
      .then(() => {
        console.log('Service Worker: Installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker: Activation complete');
      return self.clients.claim();
    })
  );
});

// Fetch event - handle network requests with cache-first strategy
self.addEventListener('fetch', event => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension requests
  if (event.request.url.startsWith('chrome-extension://')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Return cached version if available
        if (cachedResponse) {
          // Update cache in background for dynamic content
          if (isDynamicContent(event.request.url)) {
            updateCacheInBackground(event.request);
          }
          return cachedResponse;
        }

        // Fetch from network for new requests
        return fetch(event.request)
          .then(networkResponse => {
            // Cache successful responses
            if (networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME)
                .then(cache => {
                  cache.put(event.request, responseClone);
                });
            }
            return networkResponse;
          })
          .catch(error => {
            console.log('Service Worker: Network request failed', error);
            
            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
            
            // Return cached fallback for other requests
            return getCachedFallback(event.request);
          });
      })
  );
});

// Push notification event
self.addEventListener('push', event => {
  console.log('Service Worker: Push notification received');
  
  const defaultOptions = {
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/static/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/static/icons/action-dismiss.png'
      }
    ],
    requireInteraction: true,
    silent: false
  };

  let notificationData = {};
  
  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (error) {
      console.error('Service Worker: Error parsing push data', error);
      notificationData = {
        title: 'Domus Notification',
        body: event.data.text() || 'You have a new notification'
      };
    }
  }

  const options = Object.assign({}, defaultOptions, notificationData);

  event.waitUntil(
    self.registration.showNotification(notificationData.title || 'Domus Notification', options)
  );
});

// Notification click event
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification clicked', event);
  
  event.notification.close();
  
  const action = event.action;
  const notification = event.notification;
  const data = notification.data || {};
  
  if (action === 'dismiss') {
    return;
  }
  
  // Determine URL based on notification type
  let targetUrl = '/dashboard';
  
  if (data.type) {
    switch (data.type) {
      case 'project_update':
        targetUrl = `/projects/${data.projectId || ''}`;
        break;
      case 'task_assignment':
        targetUrl = `/tasks/${data.taskId || ''}`;
        break;
      case 'document_approval':
        targetUrl = `/documents/${data.documentId || ''}`;
        break;
      case 'planning_status':
        targetUrl = `/planning-ai/${data.analysisId || ''}`;
        break;
      case 'communication':
        targetUrl = `/communications/${data.messageId || ''}`;
        break;
      default:
        targetUrl = '/dashboard';
    }
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clientList => {
        // Check if there's already a window/tab open with the target URL
        for (const client of clientList) {
          if (client.url.includes(targetUrl) && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Check if there's any window/tab open
        if (clientList.length > 0) {
          const client = clientList[0];
          if ('navigate' in client) {
            return client.navigate(targetUrl).then(client => client.focus());
          } else {
            return client.focus();
          }
        }
        
        // Open new window/tab
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
  );
});

// Background sync event
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync triggered', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(syncPendingData());
  }
});

// Message event for communication with main thread
self.addEventListener('message', event => {
  console.log('Service Worker: Message received', event.data);
  
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
      case 'GET_VERSION':
        event.ports[0].postMessage({ version: CACHE_NAME });
        break;
      case 'CLEAR_CACHE':
        clearAllCaches().then(() => {
          event.ports[0].postMessage({ success: true });
        });
        break;
      case 'UPDATE_CACHE':
        updateSpecificCache(event.data.urls).then(() => {
          event.ports[0].postMessage({ success: true });
        });
        break;
    }
  }
});

// Helper functions
function isDynamicContent(url) {
  const dynamicPatterns = [
    '/api/',
    '/dashboard',
    '/projects',
    '/tasks',
    '/communications'
  ];
  return dynamicPatterns.some(pattern => url.includes(pattern));
}

function updateCacheInBackground(request) {
  fetch(request)
    .then(response => {
      if (response.status === 200) {
        caches.open(CACHE_NAME)
          .then(cache => {
            cache.put(request, response);
          });
      }
    })
    .catch(error => {
      console.log('Service Worker: Background update failed', error);
    });
}

function getCachedFallback(request) {
  // Return appropriate fallback based on request type
  if (request.url.includes('/api/')) {
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'This feature requires an internet connection',
        offline: true
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
  }
  
  // Return generic offline response
  return new Response(
    'Content not available offline',
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: {
        'Content-Type': 'text/plain'
      }
    }
  );
}

async function syncPendingData() {
  try {
    // Get pending data from IndexedDB
    const pendingData = await getPendingData();
    
    for (const item of pendingData) {
      try {
        await fetch(item.url, {
          method: item.method,
          headers: item.headers,
          body: item.body
        });
        
        // Remove from pending queue on success
        await removePendingData(item.id);
        
      } catch (error) {
        console.log('Service Worker: Sync failed for item', item.id, error);
      }
    }
    
  } catch (error) {
    console.error('Service Worker: Background sync failed', error);
  }
}

async function getPendingData() {
  // This would integrate with IndexedDB to get pending sync data
  // For now, return empty array
  return [];
}

async function removePendingData(id) {
  // This would remove the item from IndexedDB
  console.log('Service Worker: Removing pending data', id);
}

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames.map(cacheName => caches.delete(cacheName))
  );
}

async function updateSpecificCache(urls) {
  const cache = await caches.open(CACHE_NAME);
  await Promise.all(
    urls.map(url => {
      return fetch(url).then(response => {
        if (response.status === 200) {
          return cache.put(url, response);
        }
      }).catch(error => {
        console.log('Service Worker: Failed to update cache for', url, error);
      });
    })
  );
}

console.log('Service Worker: Script loaded successfully');