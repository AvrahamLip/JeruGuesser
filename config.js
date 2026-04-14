/* Override before this file in HTML: <script>window.JG_CONFIG = { API_BASE_URL: "..." };</script>
 * Production: https://jeruguesser.getbetter.games/ — אחסון סטטי דרך Git (לא Cloudflare). ה-API לניקוד נשאר על host נפרד (API_BASE_URL).
 * Release version: bump APP_VERSION here and in package.json "version" together. */
(function () {
  var g = typeof window !== 'undefined' ? window : globalThis;
  g.JG_CONFIG = Object.assign(
    {
      API_BASE_URL: 'https://151.145.89.228.sslip.io',
      APP_VERSION: '2.4.2',
      /** Service Worker cache bucket prefix (full name = prefix + APP_VERSION). */
      CACHE_ID_PREFIX: 'jeruguesser-v',
      GEOJSON_FILENAME: 'jerusalem_neighborhoods.geojson',
      LEAFLET_CSS_URL: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
      LEAFLET_JS_URL: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
      LUCIDE_VENDOR_URL: 'https://unpkg.com/lucide@0.469.0/dist/umd/lucide.min.js'
    },
    g.JG_CONFIG && typeof g.JG_CONFIG === 'object' ? g.JG_CONFIG : {}
  );
})();
