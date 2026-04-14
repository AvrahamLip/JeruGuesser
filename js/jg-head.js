/**
 * Loads Leaflet + Lucide + app stylesheet from JG_CONFIG (set by config.js).
 * config.js must be loaded immediately before this script in <head>.
 */
(function () {
  var cfg = globalThis.JG_CONFIG;
  if (!cfg || !cfg.APP_VERSION) return;
  var v = cfg.APP_VERSION;
  var q = '?v=' + encodeURIComponent(v);
  globalThis.__JG_ASSET_QUERY = q;

  function addLink(rel, href) {
    var l = document.createElement('link');
    l.rel = rel;
    l.href = href;
    document.head.appendChild(l);
  }
  function addScript(src) {
    var s = document.createElement('script');
    s.src = src;
    s.async = false;
    document.head.appendChild(s);
  }

  addLink('stylesheet', cfg.LEAFLET_CSS_URL);
  addLink('stylesheet', 'styles.css' + q);
  addScript(cfg.LEAFLET_JS_URL);
  addScript(cfg.LUCIDE_VENDOR_URL);

  var meta = document.querySelector('meta[name="app-version"]');
  if (meta) meta.setAttribute('content', v);
})();
