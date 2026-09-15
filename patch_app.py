import sys

with open('js/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Map provider
# find `function getTileUrl() {`
tile_old = """function getTileUrl() {
  return document.body.classList.contains('light-theme')
    ? 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png'
    : 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png';
}"""
tile_new = """function getTileUrl() {
  return document.body.classList.contains('light-theme')
    ? 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'
    : 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
}"""
code = code.replace(tile_old, tile_new)

# 2. Translations
code = code.replace(
    "document.getElementById('s0TargetName').textContent = q.name;",
    "document.getElementById('s0TargetName').textContent = window.tZone(q.name);"
)
code = code.replace(
    "document.getElementById('s1TargetName').textContent = q.name;",
    "document.getElementById('s1TargetName').textContent = window.tZone(q.name);"
)
code = code.replace(
    "layer.bindTooltip(name, {",
    "layer.bindTooltip(window.tZone(name), {"
)
code = code.replace(
    "correctGeoLayer.bindTooltip(q.name, {permanent: true, direction: 'center', className: 'neigh-tooltip highlight'}).openTooltip();",
    "correctGeoLayer.bindTooltip(window.tZone(q.name), {permanent: true, direction: 'center', className: 'neigh-tooltip highlight'}).openTooltip();"
)
code = code.replace(
    "clickedLayer.bindTooltip(q.name, {permanent: true, direction: 'center', className: 'neigh-tooltip correct-hit'}).openTooltip();",
    "clickedLayer.bindTooltip(window.tZone(q.name), {permanent: true, direction: 'center', className: 'neigh-tooltip correct-hit'}).openTooltip();"
)
code = code.replace(
    "showFeedback(isCorrect, q.name, pts, nextFn, distText);",
    "showFeedback(isCorrect, window.tZone(q.name), pts, nextFn, distText);"
)
code = code.replace(
    "btn.textContent=o;",
    "btn.textContent=window.tZone(o);"
)

# 3. Form Webhook + Lang Toggle
append_code = """
// ============================================================
// CONTACT FORM / WEBHOOK LOGIC
// ============================================================
const contactBtn = document.getElementById('contactBtn');
const contactOverlay = document.getElementById('contactOverlay');
const contactCloseBtn = document.getElementById('contactCloseBtn');
const contactForm = document.getElementById('contactForm');
const contactStatus = document.getElementById('contactStatus');

if (contactBtn) {
  contactBtn.addEventListener('click', (e) => {
    e.preventDefault();
    contactOverlay.style.display = 'flex';
    contactStatus.textContent = '';
    contactForm.reset();
  });
}

if (contactCloseBtn) {
  contactCloseBtn.addEventListener('click', (e) => {
    e.preventDefault();
    contactOverlay.style.display = 'none';
  });
}

if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    contactStatus.textContent = 'שולח...';
    contactStatus.style.color = 'var(--text)';

    const formData = new FormData(contactForm);
    const payload = Object.fromEntries(formData.entries());

    try {
      const response = await fetch('http://151.145.89.228.sslip.io/webhook/form', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        contactStatus.textContent = 'ההודעה נשלחה בהצלחה!';
        contactStatus.style.color = '#10b981'; // Green
        setTimeout(() => {
          contactOverlay.style.display = 'none';
        }, 2000);
      } else {
        throw new Error('Server returned ' + response.status);
      }
    } catch (err) {
      console.error('Webhook error:', err);
      contactStatus.textContent = 'שגיאה בשליחת ההודעה, נסה שוב.';
      contactStatus.style.color = '#ef4444'; // Red
    }
  });
}

const langToggleBtn = document.getElementById('langToggleBtn');
if (langToggleBtn) {
  langToggleBtn.addEventListener('click', () => {
    window.currentLang = window.currentLang === 'he' ? 'en' : 'he';
    window.updateUIForLanguage();
    if (typeof state !== 'undefined' && state.mode === 'practice' && typeof geoLayer !== 'undefined' && geoLayer) {
      if (typeof practiceMap !== 'undefined' && practiceMap) practiceMap.removeLayer(geoLayer);
      drawGeoStage('practice', typeof practiceMap !== 'undefined' ? practiceMap : null, null, true);
    }
  });
}
if(typeof window.updateUIForLanguage === 'function') window.updateUIForLanguage();
"""

code += "\n" + append_code

with open('js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)
print("js/app.js patched successfully.")
