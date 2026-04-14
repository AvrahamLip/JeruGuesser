importScripts('config.js');

const JG = globalThis.JG_CONFIG;
const V = JG && JG.APP_VERSION;
const Q = '?v=' + encodeURIComponent(V);
const CACHE_NAME = (JG && JG.CACHE_ID_PREFIX ? JG.CACHE_ID_PREFIX : 'jeruguessr-v') + V;
const GEO = (JG && JG.GEOJSON_FILENAME) || 'jerusalem_neighborhoods.geojson';

const assets = [
  'game.html',
  'styles.css' + Q,
  'config.js' + Q,
  'js/jg-head.js',
  'js/game-utils.js' + Q,
  'js/app.js' + Q,
  'table_data.js' + Q,
  GEO + Q,
  'jerusalem_bg.png',
  'icon-192.png',
  'icon-512.png',
  'manifest.json'
];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.all(
        assets.map((url) =>
          cache.add(url).catch((err) => {
            console.warn('[SW] cache add failed:', url, err);
            return null;
          })
        )
      );
    })
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
