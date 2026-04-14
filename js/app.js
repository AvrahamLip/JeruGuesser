var APP_VERSION = (window.JG_CONFIG && window.JG_CONFIG.APP_VERSION) || '';
var CONFIG = {
  API_BASE_URL: (window.JG_CONFIG && window.JG_CONFIG.API_BASE_URL) || ''
};

function trackEvent(name, detail) {
  try {
    if (typeof window.JG_ANALYTICS === 'function') window.JG_ANALYTICS(name, detail || {});
  } catch (_) {}
}

// ============================================================
// DATA PREPARATION
// ============================================================
window._geoJSON = null;
var dataLoaded = false;
var geoLoadPromise = null;

function haversine(lat1, lon1, lat2, lon2) {
  return window.JGGameUtils.haversine(lat1, lon1, lat2, lon2);
}

/** GeoJSON is parsed on the main thread; if low-end devices show jank, measure and consider a Web Worker. */
async function ensureGeoJSONReady() {
  if (window._geoJSON && dataLoaded) return;
  if (geoLoadPromise) {
    await geoLoadPromise;
    return;
  }
  geoLoadPromise = (async function () {
    if (!APP_VERSION) throw new Error('JG_CONFIG.APP_VERSION missing (config.js must load before the game bundle).');
    var geoBase = (window.JG_CONFIG && window.JG_CONFIG.GEOJSON_FILENAME) || 'jerusalem_neighborhoods.geojson';
    var url = geoBase + '?v=' + encodeURIComponent(APP_VERSION);
    var res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load neighborhoods');
    window._geoJSON = await res.json();
    dataLoaded = true;
  })();
  try {
    await geoLoadPromise;
  } catch (e) {
    geoLoadPromise = null;
    throw e;
  }
}

const ALL_DATA = TABLE_DATA.filter(r =>
  r['שם רחוב'] && r['שכונה עירונית'] && r['קו רוחב'] && r['קו אורך']
);

// Build neighborhood list with centroid
const neighMap = {};
ALL_DATA.forEach(r => {
  const n = r['שכונה עירונית'];
  if (!neighMap[n]) neighMap[n] = { name:n, lats:[], lngs:[] };
  neighMap[n].lats.push(r['קו רוחב']);
  neighMap[n].lngs.push(r['קו אורך']);
});
const NEIGHBORHOODS = Object.values(neighMap)
  .filter(n => n.lats.length >= 5)
  .map(n => ({
    name: n.name,
    lat: n.lats.reduce((a,b)=>a+b,0)/n.lats.length,
    lng: n.lngs.reduce((a,b)=>a+b,0)/n.lngs.length
  }));

// Filter streets usable in stage 3 (have coords)
const VALID_STREETS = ALL_DATA.filter(r => {
  const n = NEIGHBORHOODS.find(x=>x.name===r['שכונה עירונית']);
  return !!n;
});

function shuffle(arr) {
  return window.JGGameUtils.shuffle(arr);
}
function pick(arr, n) {
  return window.JGGameUtils.pick(arr, n);
}

// ============================================================
// GAME STATE
// ============================================================
let state = {
  mode: 'jeru', // 'jeru', 'trivia', or 'practice'
  level: 1,
  round: 0,
  score: 0,
  lives: 3,
  maxLives: 3,
  targetScore: 3000,
  questionsInLevel: 9,
  questions: [],
  scores: [0,0,0,0], // legacy compat for result screen
  scoreAtLevelStart: 0, // jeru: total score when current level began
  jeruPostLevelBonus: false, // jeru: street mini-game after hitting level target on map
  jeruBonusPerfect: false // jeru bonus: both s2 and s3 answered correctly this level
};

function refreshLucideIcons() {
  if (window.lucide && typeof lucide.createIcons === 'function') {
    try { lucide.createIcons(); } catch (_) {}
  }
}

function updateHearts() {
  const container = document.getElementById('s' + state.stage + 'Hearts');
  if(!container) return;
  container.innerHTML = '';
  for(let i=0; i<state.maxLives; i++) {
    const s = document.createElement('span');
    s.className = 'heart' + (i >= state.lives ? ' lost' : '');
    s.setAttribute('aria-hidden', 'true');
    s.innerHTML = '<i data-lucide="heart" class="heart-svg"></i>';
    container.appendChild(s);
  }
  refreshLucideIcons();
}

function updateGlobalNavScore() {
  const el = document.getElementById('globalNavScore');
  if (!el) return;
  const active = document.querySelector('.screen.active');
  const sid = active ? active.id : '';
  if (sid === 'leaderboard' || sid === 'home' || sid === 'results') {
    el.style.display = 'none';
    el.textContent = '';
    return;
  }
  // Unified rail (stages 0–3) already shows score + context; hide nav score strip to avoid duplicate «header» + «progress» feel.
  if (sid === 'stage0' || sid === 'stage1' || sid === 'stage2' || sid === 'stage3') {
    el.style.display = 'none';
    el.textContent = '';
    return;
  }
  el.style.display = 'flex';
  const w = typeof window !== 'undefined' ? window.innerWidth : 800;
  const compact = w <= 560;
  const tiny = w <= 400;
  if (state.mode === 'jeru' && state.jeruPostLevelBonus) {
    el.textContent = compact ? `${state.score} נק׳ · בונוס` : `ניקוד ${state.score} · בונוס סיום רמה (רחובות)`;
    return;
  }
  if (state.mode === 'jeru') {
    const earned = state.score - state.scoreAtLevelStart;
    if (tiny) {
      el.textContent = `רמה ${state.level}: ${earned}/${state.targetScore} · ${state.score} נק׳`;
    } else if (compact) {
      el.textContent = `רמה ${state.level}: ${earned}/${state.targetScore} · סה״כ ${state.score} נק׳`;
    } else {
      el.textContent = `ניקוד ${state.score} · ברמה ${state.level}: ${earned}/${state.targetScore} · ${state.questionsInLevel} שכונות`;
    }
  } else {
    el.textContent = compact ? `${state.score} נק׳` : `ניקוד ${state.score}`;
  }
}

let _globalNavScoreResizeTimer = 0;
window.addEventListener('resize', () => {
  clearTimeout(_globalNavScoreResizeTimer);
  _globalNavScoreResizeTimer = setTimeout(() => updateGlobalNavScore(), 120);
});

// Maps
let map0=null, map1=null, map3=null;
let guessMarker=null, correctMarker=null, line=null;

function getTileUrl() {
  const isLight = document.body.classList.contains('light-theme');
  // Carto CDN: no API key; terms are attribution-only for typical web maps.
  // No-labels + no @2x keeps tiles small (no neighborhood name hints on zoom).
  return isLight
    ? 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png'
    : 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png';
}

const MAP_TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

function baseMapTileLayerOptions() {
  return {
    attribution: MAP_TILE_ATTRIBUTION,
    maxZoom: 19,
    subdomains: 'abcd',
    detectRetina: false,
    keepBuffer: 1
  };
}

// ============================================================
// SCREEN MANAGEMENT
// ============================================================
function showScreen(id) {
  if (id === 'home') {
    state.jeruPostLevelBonus = false;
    state.jeruBonusPerfect = false;
  }
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.body.classList.toggle('map-stage-active', ['stage0', 'stage1', 'stage3'].includes(id));
  document.body.classList.toggle('game-rail-screens', ['stage0', 'stage1', 'stage2', 'stage3'].includes(id));
  const gNav = document.getElementById('globalNav');
  if(gNav) gNav.style.display = (id === 'home' || id === 'results') ? 'none' : 'flex';
  window.scrollTo(0,0);
  updateGlobalNavScore();
  refreshLucideIcons();
}

// ============================================================
// INIT GAME
// ============================================================
function beginJeruSession() {
  state.mode = 'jeru';
  state.level = 1;
  state.score = 0;
  state.lives = 3;
  state.maxLives = 3;
  state.targetScore = 3000;
  state.questionsInLevel = 9;
  state.stage = 1;
  state.scores = [0,0,0,0];
  state.jeruPostLevelBonus = false;
  state.jeruBonusPerfect = false;
  loadJeruLevel();
}

async function startJeru() {
  trackEvent('game_start', { mode: 'jeru' });
  const btn = document.getElementById('startJeruBtn');
  const label = btn && btn.querySelector('span');
  const prevText = label ? label.textContent : '';
  try {
    if (btn) btn.disabled = true;
    if (label) label.textContent = 'טוען מפה...';
    await ensureGeoJSONReady();
    beginJeruSession();
  } catch (err) {
    console.error(err);
    alert('שגיאה בטעינת נתוני המפה. נסו לרענן את הדף או לנסות שוב.');
  } finally {
    if (btn) btn.disabled = false;
    if (label) label.textContent = prevText || 'התחל JeruGuesser';
    refreshLucideIcons();
  }
}

function startTrivia() {
  return;
}

function beginPracticeSession() {
  state.mode = 'practice';
  state.stage = 0;
  state.round = 0;
  state.score = 0;
  state.scores = [0,0,0,0];
  state.lives = 999;
  state.jeruPostLevelBonus = false;
  state.jeruBonusPerfect = false;
  state.questions = pick(NEIGHBORHOODS, 100);
  startStage0();
}

async function startPractice() {
  trackEvent('game_start', { mode: 'practice' });
  const btn = document.getElementById('startPracticeBtn');
  const label = btn && btn.querySelector('span');
  const prevText = label ? label.textContent : '';
  try {
    if (btn) btn.disabled = true;
    if (label) label.textContent = 'טוען מפה...';
    await ensureGeoJSONReady();
    beginPracticeSession();
  } catch (err) {
    console.error(err);
    alert('שגיאה בטעינת נתוני המפה. נסו לרענן את הדף או לנסות שוב.');
  } finally {
    if (btn) btn.disabled = false;
    if (label) label.textContent = prevText || 'תרגול חופשי';
    refreshLucideIcons();
  }
}

function loadJeruLevel() {
  state.round = 0;
  state.scoreAtLevelStart = state.score;
  // Every 2 levels reset lives
  if (state.level > 1 && state.level % 2 === 1) {
    state.lives = 3;
  }
  // Questions count: 9 + floor((level-1)/3)
  state.questionsInLevel = 9 + Math.floor((state.level - 1) / 3);
  state.questions = pick(NEIGHBORHOODS, state.questionsInLevel);
  
  // Points required in this level only (level 1: 3000; level n≥2: 2000 + n×1000)
  if (state.level === 1) state.targetScore = 3000;
  else state.targetScore = 2000 + state.level * 1000;
  
  startStage1();
}

function loadTriviaRound() {
  state.questions = pick(VALID_STREETS, 1);
  // Randomly pick between Stage 2 (Card) or Stage 3 (Map)
  state.stage = Math.random() > 0.5 ? 2 : 3;
  if (state.stage === 2) startStage2();
  else startStage3();
}

// ============================================================
// STAGES 0 & 1 - FIND NEIGHBORHOOD (INTERACTIVE POLYGON MAP)
// ============================================================
let geoLayer = null;       // full geojson layer
let geoAnswered = false;   // prevent double click
let selectedGeoLayer = null;
let selectedGeoName = null;

let currentMap = null;     // pointer to the active leaflete map

function drawGeoStage(stageNum, mapId, q, showNames) {
  const theMap = stageNum === 0 ? map0 : map1;
  if (!theMap) { console.error("Map not initialized for stage", stageNum); return; }

  // Cleanup existing layers
  if (geoLayer) {
    console.log("Removing existing geoLayer...");
    map0 && map0.removeLayer(geoLayer);
    map1 && map1.removeLayer(geoLayer);
    geoLayer = null;
  }
  
  geoAnswered = false;
  selectedGeoLayer = null;
  selectedGeoName = null;
  const confirmBtn = document.getElementById('s'+stageNum+'Confirm');
  if(confirmBtn) confirmBtn.style.display = 'none';
  
  if(!window._geoJSON) { console.error("GeoJSON not loaded"); return; }

  console.log("Drawing GeoJSON for stage", stageNum, "showNames:", showNames);
  geoLayer = L.geoJSON(window._geoJSON, {
    style: feature => sGeoStyle(false),
    onEachFeature: (feature, layer) => {
      const name = feature.properties.SCHN_NAME || feature.properties.name || "Unknown";
      
      if(showNames) {
        layer.bindTooltip(name, {
          permanent: false,
          direction: 'center',
          className: 'neigh-tooltip'
        });
      }
      
      layer.on('click', (e) => {
        console.log("Neighborhood clicked:", name);
        L.DomEvent.stopPropagation(e); // Prevent map click if applicable
        
        if(geoAnswered) return;
        if(selectedGeoLayer && selectedGeoLayer !== layer) {
          selectedGeoLayer.setStyle(sGeoStyle(false));
        }
        selectedGeoLayer = layer;
        selectedGeoName = name;
        layer.setStyle({ fillColor: '#6ee7b7', fillOpacity: 0.5, color: '#10b981', weight: 3 });
        layer.bringToFront();
        
        const btn = document.getElementById('s'+stageNum+'Confirm');
        if(btn) {
          btn.style.display = 'block';
          btn.onclick = () => {
            btn.style.display = 'none';
            geoAnswerGeo(stageNum, selectedGeoName, selectedGeoLayer, q, theMap);
          };
        }
      });
      
      layer.on('mouseover', function() {
        if(geoAnswered || selectedGeoLayer === this) return;
        this.setStyle({ fillOpacity:0.4, fillColor:'#60a5fa', weight: 2 });
      });
      
      layer.on('mouseout', function() {
        if(geoAnswered || selectedGeoLayer === this) return;
        this.setStyle(sGeoStyle(false));
      });
    }
  }).addTo(theMap);

  theMap.setView([31.78, 35.22], 12);
  updateSUI(stageNum);
}

function startStage0() {
  state.stage=0; state.round=0;
  showScreen('stage0');
  updateSUI(0);

  if(!map0) {
    setTimeout(()=>{
      map0 = L.map('map0', {
        zoomControl: true,
        doubleClickZoom: false,
        touchZoom: true,
        scrollWheelZoom: false,
        dragging: true,
        tap: false
      }).setView([31.78,35.22],12);
      L.tileLayer(getTileUrl(), baseMapTileLayerOptions()).addTo(map0);
      ensureGeoJSON(()=>loadS0Round());
    },100);
  } else {
    setTimeout(()=>{ map0.invalidateSize(); loadS0Round(); },100);
  }
}

function loadS0Round() {
  const q = state.questions[state.round];
  document.getElementById('s0TargetName').textContent = q.name;
  drawGeoStage(0, 'map0', q, true); // true = show tooltips
}

function startStage1() {
  state.stage=1; state.round=0;
  showScreen('stage1');
  updateSUI(1);

  if(!map1) {
    setTimeout(()=>{
      map1 = L.map('map1', {
        zoomControl: true,
        doubleClickZoom: false,
        touchZoom: true,
        scrollWheelZoom: false,
        dragging: true,
        tap: false
      }).setView([31.78,35.22],12);
      L.tileLayer(getTileUrl(), baseMapTileLayerOptions()).addTo(map1);
      ensureGeoJSON(()=>loadS1Round());
    },100);
  } else {
    setTimeout(()=>{ map1.invalidateSize(); loadS1Round(); },100);
  }
}

function loadS1Round() {
  const q = state.questions[state.round];
  document.getElementById('s1TargetName').textContent = q.name;
  document.getElementById('s1Score').textContent = state.score;
  drawGeoStage(1, 'map1', q, false); // false = hide tooltips
}

function ensureGeoJSON(cb) {
  if (window._geoJSON && dataLoaded) return cb();
  ensureGeoJSONReady()
    .then(function () { cb(); })
    .catch(function (err) {
      console.error(err);
      alert('שגיאה בטעינת שכונות למפה');
    });
}

function sGeoStyle(isTarget) {
  return { fillColor: isTarget ? '#f5c518' : '#3b82f6', fillOpacity: isTarget ? 0.35 : 0.12, color: isTarget ? '#f5c518' : '#60a5fa', weight: isTarget ? 2.5 : 1 };
}
function sGeoPulseStyle() {
  return { fillColor:'#f5c518', fillOpacity:0.55, color:'#fde68a', weight:3 };
}

function geoAnswerGeo(stageNum, clickedName, clickedLayer, q, theMap) {
  geoAnswered = true;
  const isCorrect = (clickedName === q.name);
  let correctGeoLayer = null;
  if (!isCorrect) {
    geoLayer.eachLayer(lyr => {
      if (lyr.feature && lyr.feature.properties.SCHN_NAME === q.name) correctGeoLayer = lyr;
    });
  }

  // Style the clicked polygon
  clickedLayer.setStyle({
    fillColor: isCorrect ? '#10b981' : '#ef4444', fillOpacity: 0.6,
    color: isCorrect ? '#6ee7b7' : '#fca5a5', weight: 3,
  });

  if(!isCorrect) {
    if (correctGeoLayer) {
      correctGeoLayer.setStyle(sGeoPulseStyle());
      correctGeoLayer.unbindTooltip();
      correctGeoLayer.bindTooltip(q.name, {permanent: true, direction: 'center', className: 'neigh-tooltip highlight'}).openTooltip();
      // Show both wrong pick and correct neighborhood in frame (card at top — keep padding)
      const bothBounds = clickedLayer.getBounds().extend(correctGeoLayer.getBounds());
      theMap.fitBounds(bothBounds, { paddingTopLeft: [18, 220], paddingBottomRight: [18, 56], maxZoom: 15 });
    } else {
      theMap.fitBounds(clickedLayer.getBounds(), { paddingTopLeft: [18, 220], paddingBottomRight: [18, 56], maxZoom: 15 });
    }
  } else {
    clickedLayer.unbindTooltip();
    clickedLayer.bindTooltip(q.name, {permanent: true, direction: 'center', className: 'neigh-tooltip correct-hit'}).openTooltip();
    theMap.fitBounds(clickedLayer.getBounds(), { paddingTopLeft: [18, 220], paddingBottomRight: [18, 56], maxZoom: 15 });
  }

  let distText = '';
  let pts = 0;

  if (stageNum === 0) {
    pts = isCorrect ? 200 : 0;
  } else {
    // JeruGuesser logic
    if (isCorrect) {
      pts = 500;
    } else if (correctGeoLayer) {
      const c1 = clickedLayer.getBounds().getCenter();
      const c2 = correctGeoLayer.getBounds().getCenter();
      const dist = haversine(c1.lat, c1.lng, c2.lat, c2.lng);
      pts = window.JGGameUtils.neighborhoodMissPoints(dist, state.level);
      distText = `מרחק פגיעה: ${dist < 1 ? Math.round(dist*1000)+' מטר' : dist.toFixed(1)+' ק\u05F4מ'}`;
    }
  }

  state.score += pts;
  state.scores[stageNum] += pts; // for final screen stats
  document.getElementById('s'+stageNum+'Score').textContent = state.score;
  updateHearts();
  updateGlobalNavScore();
  
  const nextFn = () => { 
    if(state.mode === 'trivia' && state.lives <= 0) { showResults(); return; }
    stageNum === 0 ? s0Next() : s1Next(); 
  };
  showFeedback(isCorrect, q.name, pts, nextFn, distText);
}

function s0Next() {
  state.round++;
  // Infinite questions handling
  if(state.round >= state.questions.length) {
    state.questions.push(...pick(NEIGHBORHOODS, 10));
  }
  loadS0Round();
}

function s1Next() {
  state.round++;
  if(state.round >= state.questionsInLevel) {
    const earnedThisLevel = state.score - state.scoreAtLevelStart;
    if(earnedThisLevel >= state.targetScore) {
      state.jeruPostLevelBonus = true;
      state.jeruBonusPerfect = true;
      state.questions = pick(VALID_STREETS, 1);
      startStage2();
    } else {
      showResults();
    }
    return;
  }
  loadS1Round();
}

/** Short task line for unified rail (layout A). */
function syncRailKicker(stageNum) {
  const el = document.getElementById('s' + stageNum + 'ContextKicker');
  if (!el) return;
  if (state.mode === 'practice' && stageNum === 0) {
    el.textContent = 'תרגול · מפה עם שמות שכונות';
    return;
  }
  if (state.mode === 'trivia') {
    if (stageNum === 2) el.textContent = 'טריוויה · שיוך רחוב לשכונה';
    else if (stageNum === 3) el.textContent = 'טריוויה · מיקום במפה';
    else el.textContent = 'טריוויה';
    return;
  }
  if (state.mode === 'jeru') {
    if (state.jeruPostLevelBonus) {
      if (stageNum === 2) el.textContent = 'שיוך רחוב · בונוס סיום רמה';
      else if (stageNum === 3) el.textContent = 'מיקום במפה · בונוס סיום רמה';
      else if (stageNum === 1) el.textContent = 'איתור שכונה · ללא שמות';
    } else if (stageNum === 1) {
      el.textContent = 'איתור שכונה · ללא שמות';
    } else if (stageNum === 2) {
      el.textContent = 'שיוך רחוב לשכונה';
    } else if (stageNum === 3) {
      el.textContent = 'מיקום רחוב במפה';
    }
  }
}

function setRailDetail(stageNum, text) {
  const el = document.getElementById('s' + stageNum + 'RailDetail');
  if (!el) return;
  if (text) {
    el.textContent = text;
    el.hidden = false;
  } else {
    el.textContent = '';
    el.hidden = true;
  }
}

function setRailProgressVisible(stageNum, visible) {
  const wrap = document.getElementById('s' + stageNum + 'ProgressWrap');
  if (!wrap) return;
  wrap.style.display = visible ? '' : 'none';
}

function updateSUI(stageNum) {
  syncRailKicker(stageNum);

  if (stageNum === 0) {
    document.getElementById('s0ContextMain').textContent = 'שאלה ' + (state.round + 1);
    setRailProgressVisible(0, false);
    document.getElementById('s0Hearts').style.display = 'none';
    setRailDetail(0, '');
  } else if (state.mode === 'jeru') {
    if (state.jeruPostLevelBonus && (stageNum === 2 || stageNum === 3)) {
      document.getElementById('s' + stageNum + 'ContextMain').textContent =
        'רמה ' + state.level + ' · בונוס סיום רמה';
      document.getElementById('s' + stageNum + 'Progress').style.width = '100%';
      setRailProgressVisible(stageNum, true);
      var perkLine =
        state.level % 3 === 0
          ? ' ברמה המתחלקת ב־3: מענה מושלם בשני שלבי הבונוס = +300 נק׳ ואיפוס חיים.'
          : '';
      var tips =
        stageNum === 2
          ? 'בחרו את השכונה שבה נמצא הרחוב (אותו רחוב בשלב הבא במפה).' + perkLine
          : 'סמנו במפה את מיקום הרחוב. לאחר מכן תעברו לרמה הבאה.' + perkLine;
      setRailDetail(stageNum, tips);
      document.getElementById('s' + stageNum + 'Hearts').style.display = 'none';
    } else if (stageNum === 1) {
      document.getElementById('s1ContextMain').textContent =
        'רמה ' + state.level + ' – שאלה ' + (state.round + 1) + '/' + state.questionsInLevel;
      var pct = (state.round / state.questionsInLevel) * 100;
      document.getElementById('s1Progress').style.width = pct + '%';
      setRailProgressVisible(1, true);
      var earned = state.score - state.scoreAtLevelStart;
      setRailDetail(
        1,
        'ניקוד כולל: ' +
          state.score +
          ' · ברמה זו: ' +
          earned +
          '/' +
          state.targetScore +
          ' נק׳ · ' +
          state.questionsInLevel +
          ' שכונות'
      );
      document.getElementById('s1Hearts').style.display = 'none';
    } else {
      document.getElementById('s' + stageNum + 'ContextMain').textContent = 'שאלה ' + (state.round + 1);
      document.getElementById('s' + stageNum + 'Progress').style.width = '0%';
      setRailProgressVisible(stageNum, true);
      document.getElementById('s' + stageNum + 'Hearts').style.display = 'flex';
      setRailDetail(stageNum, '');
    }
  } else {
    document.getElementById('s' + stageNum + 'ContextMain').textContent = 'שאלה ' + (state.round + 1);
    document.getElementById('s' + stageNum + 'Progress').style.width = '0%';
    setRailProgressVisible(stageNum, true);
    document.getElementById('s' + stageNum + 'Hearts').style.display = 'flex';
    setRailDetail(stageNum, '');
  }
  updateHearts();
  updateGlobalNavScore();
}


// ============================================================
// STAGE 2 - MATCH STREET TO NEIGHBORHOOD
// ============================================================
function startStage2() {
  state.stage=2; state.round=0;
  showScreen('stage2');
  loadS2Round();
}

function loadS2Round() {
  const q = state.questions[0];
  document.getElementById('s2StreetName').textContent = q['שם רחוב'];
  updateSUI(2);
  document.getElementById('s2Score').textContent = state.score;

  const correct = q['שכונה עירונית'];
  const others = shuffle(NEIGHBORHOODS.filter(n=>n.name!==correct)).slice(0,3).map(n=>n.name);
  const options = shuffle([correct,...others]);

  const grid = document.getElementById('s2Options');
  grid.innerHTML='';
  options.forEach(o=>{
    const btn=document.createElement('button');
    btn.type='button';
    btn.className='option-btn';
    btn.textContent=o;
    btn.onclick=()=>s2Guess(o, correct, btn, grid);
    grid.appendChild(btn);
  });
}

function s2Guess(chosen, correct, btn, grid) {
  grid.querySelectorAll('.option-btn').forEach(b=>b.disabled=true);
  const isCorrect=chosen===correct;
  btn.classList.add(isCorrect?'correct':'wrong');
  if(!isCorrect) {
    grid.querySelectorAll('.option-btn').forEach(b=>{
      if(b.textContent===correct) b.classList.add('correct');
    });
    if (!(state.mode === 'jeru' && state.jeruPostLevelBonus)) state.lives--;
    if (state.mode === 'jeru' && state.jeruPostLevelBonus) state.jeruBonusPerfect = false;
  }
  const pts = isCorrect ? (state.mode === 'trivia' ? 10 : 200) : 0;
  state.score += pts;
  state.scores[2] += pts;
  document.getElementById('s2Score').textContent = state.score;
  updateHearts();
  updateGlobalNavScore();
  
  const nextFn = () => {
    if(state.lives <= 0) { showResults(); return; }
    s2Next();
  };
  showFeedback(isCorrect, correct, pts, nextFn);
}

function s2Next() {
  if (state.mode === 'jeru' && state.jeruPostLevelBonus) {
    startStage3();
    return;
  }
  state.round++;
  if(state.mode === 'trivia') { loadTriviaRound(); return; }
  loadS2Round();
}

// ============================================================
// STAGE 3 - LOCATE STREET ON MAP
// ============================================================
function startStage3() {
  state.stage=3; state.round=0;
  showScreen('stage3');
  // Always destroy & recreate map3 so it renders in the now-visible container
  if(map3){ map3.remove(); map3=null; }
  if(guessMarker){ guessMarker=null; }
  if(correctMarker){ correctMarker=null; }
  if(line){ line=null; }
  setTimeout(()=>{
    map3=L.map('map3', {
      zoomControl: true,
      doubleClickZoom: false,
      touchZoom: true,
      scrollWheelZoom: false,
      dragging: true,
      tap: false
    }).setView([31.78,35.22],12);
    L.tileLayer(getTileUrl(), baseMapTileLayerOptions()).addTo(map3);
    map3.on('click',onMap3Click);
    loadS3Round();
  },150);
}

function loadS3Round() {
  if(guessMarker){guessMarker.remove();guessMarker=null;}
  if(correctMarker){correctMarker.remove();correctMarker=null;}
  if(line){line.remove();line=null;}
  document.getElementById('confirmGuess').style.display='none';
  var hintT = document.getElementById('s3HintText');
  if (hintT) hintT.textContent = 'לחצ/י על מיקום הרחוב במפה';
  refreshLucideIcons();

  const q=state.questions[0];
  document.getElementById('s3StreetName').textContent=q['שם רחוב'];
  document.getElementById('s3NeighName').textContent=`שכונה: ${q['שכונה עירונית']}`;
  updateSUI(3);
  document.getElementById('s3Score').textContent=state.score;
  map3.setView([31.78,35.22],12);
}

function onMap3Click(e) {
  if(guessMarker) guessMarker.remove();
  const gIcon=L.divIcon({className:'',html:'<div class="guess-marker-ripple"></div>',iconSize:[20,20],iconAnchor:[10,10]});
  guessMarker=L.marker(e.latlng,{icon:gIcon}).addTo(map3);
  document.getElementById('confirmGuess').style.display='block';
  var hintT2 = document.getElementById('s3HintText');
  if (hintT2) hintT2.textContent = 'לחצ/י "אשר ניחוש" או שנה מיקום';
  refreshLucideIcons();
  document.getElementById('confirmGuess').onclick=()=>s3Confirm(e.latlng);
}

function s3Confirm(guessLatLng) {
  map3.off('click',onMap3Click);
  const q=state.questions[0];
  const cLat=q['קו רוחב'], cLng=q['קו אורך'];
  const dist=haversine(guessLatLng.lat,guessLatLng.lng,cLat,cLng);
  
  let pts = 0;
  let isCorrect = false;
  
  if (state.mode === 'trivia') {
    // In Trivia, "correct" is within 300m
    isCorrect = dist < 0.3;
    pts = isCorrect ? 10 : 0;
    if(!isCorrect) state.lives--;
  } else {
    const sm = window.JGGameUtils.streetMapGuessFromDistKm(dist);
    pts = sm.pts;
    isCorrect = sm.isCorrect;
    if (state.mode === 'jeru' && state.jeruPostLevelBonus && !isCorrect) {
      state.jeruBonusPerfect = false;
    }
  }
  
  state.score += pts;
  state.scores[3] += pts;
  document.getElementById('s3Score').textContent = state.score;
  document.getElementById('confirmGuess').style.display = 'none';
  updateHearts();
  updateGlobalNavScore();

  // show correct
  const cIcon=L.divIcon({className:'',html:'<div style="width:22px;height:22px;background:#10b981;border:3px solid #fff;border-radius:50%;box-shadow:0 0 10px #10b981"></div>',iconSize:[22,22],iconAnchor:[11,11]});
  correctMarker=L.marker([cLat,cLng],{icon:cIcon}).addTo(map3).bindPopup(q['שם רחוב']).openPopup();
  line=L.polyline([guessLatLng,[cLat,cLng]],{color:'#f5c518',weight:2,dashArray:'6,4'}).addTo(map3);
  map3.fitBounds([[guessLatLng.lat,guessLatLng.lng],[cLat,cLng]], {
    paddingTopLeft: [36, 220],
    paddingBottomRight: [36, 72],
    maxZoom: 15
  });

  const distText=dist<1?`${Math.round(dist*1000)} מטר`:`${dist.toFixed(1)} ק\u05F4מ`;
  
  const nextFn = () => {
    if(state.lives <= 0) { showResults(); return; }
    s3Next();
  };
  showFeedback(isCorrect, q['שם רחוב'], pts, nextFn, `מרחק מהמיקום הנכון: ${distText}`);
  // re-enable click after
  setTimeout(()=>map3.on('click',onMap3Click),100);
}

function s3Next() {
  if (state.mode === 'jeru' && state.jeruPostLevelBonus) {
    const completedLevel = state.level;
    if (state.jeruBonusPerfect && completedLevel % 3 === 0) {
      state.score += 300;
      state.lives = state.maxLives;
      trackEvent('jeru_bonus_perk', { level: completedLevel });
      updateHearts();
      updateGlobalNavScore();
      showJeruPerkToast();
    }
    state.jeruPostLevelBonus = false;
    state.jeruBonusPerfect = false;
    state.level++;
    loadJeruLevel();
    return;
  }
  state.round++;
  if(state.mode === 'trivia') { loadTriviaRound(); return; }
  loadS3Round();
}

// ============================================================
// FEEDBACK
// ============================================================
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function showFeedback(isCorrect, detail, pts, onNext, distText) {
  var fbIcon = document.getElementById('fbIcon');
  if (fbIcon) {
    fbIcon.className = 'feedback-icon ' + (isCorrect ? 'is-correct' : 'is-wrong');
    fbIcon.innerHTML = '<i data-lucide="' + (isCorrect ? 'circle-check' : 'circle-x') + '" aria-hidden="true"></i>';
    refreshLucideIcons();
  }
  document.getElementById('fbTitle').textContent=isCorrect?'נכון!':'לא נכון';
  document.getElementById('fbTitle').className='feedback-title '+(isCorrect?'correct':'wrong');
  
  if (isCorrect) {
    document.getElementById('fbDetail').innerHTML = detail;
  } else {
    document.getElementById('fbDetail').innerHTML =
      `<span class="fb-answer-label">התשובה הנכונה:</span><span class="fb-answer-value">${escapeHtml(detail)}</span>`;
  }

  const readBtn = document.getElementById('fbReadabilityBtn');
  const night = !document.body.classList.contains('light-theme');
  if (!isCorrect && night) {
    readBtn.classList.add('is-visible');
    readBtn.onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      document.body.classList.add('light-theme');
      readBtn.classList.remove('is-visible');
      readBtn.onclick = null;
    };
  } else {
    readBtn.classList.remove('is-visible');
    readBtn.onclick = null;
  }
  
  document.getElementById('fbPoints').textContent=`+${pts} נקודות`;
  const dEl=document.getElementById('fbDistance');
  if(distText){dEl.style.display='block';dEl.textContent=distText;}
  else{dEl.style.display='none';}
  const overlay=document.getElementById('feedbackOverlay');
  const mapFeedbackStages = [0, 1, 3];
  overlay.classList.toggle('feedback-at-top', mapFeedbackStages.includes(state.stage));
  document.body.classList.add('feedback-open');
  overlay.classList.add('show');
  const fbCard = overlay.querySelector('.feedback-card');
  if (fbCard) fbCard.scrollTop = 0;
  const fbNextBtn = document.getElementById('fbNext');
  if (fbNextBtn) {
    requestAnimationFrame(function () {
      try {
        fbNextBtn.focus();
      } catch (_) {}
    });
  }
  document.getElementById('fbNext').onclick=()=>{
    overlay.classList.remove('show', 'feedback-at-top');
    document.body.classList.remove('feedback-open');
    updateGlobalNavScore();
    onNext();
  };
  requestAnimationFrame(() => {
    const detailEl = document.getElementById('fbDetail');
    if (detailEl && window.innerWidth <= 560) {
      detailEl.scrollIntoView({ block: 'nearest', behavior: 'auto' });
    }
  });
}

// ============================================================
// RESULTS
// ============================================================
function setResultBreakdownLabels(a, b, c, d) {
  var ids = ['s0BreakdownLbl', 's1BreakdownLbl', 's2BreakdownLbl', 's3BreakdownLbl'];
  var vals = [a, b, c, d];
  for (var i = 0; i < 4; i++) {
    var el = document.getElementById(ids[i]);
    if (el) el.textContent = vals[i];
  }
}

function showJeruPerkToast() {
  var el = document.getElementById('jgPerkToast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'jgPerkToast';
    el.className = 'jg-perk-toast';
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    document.body.appendChild(el);
  }
  el.textContent = '+300 נקודות בונוס! החיים אופסו לרמה מלאה.';
  el.classList.add('show');
  clearTimeout(showJeruPerkToast._t);
  showJeruPerkToast._t = setTimeout(function () {
    el.classList.remove('show');
  }, 4500);
}

function showResults() {
  state.jeruPostLevelBonus = false;
  state.jeruBonusPerfect = false;
  trackEvent('game_end', { mode: state.mode, score: state.score });
  showScreen('results');
  setResultBreakdownLabels('שלב 0', 'שלב 1', 'שלב 2', 'שלב 3');
  document.getElementById('finalScore').textContent = state.score;
  document.getElementById('s0Total').textContent=`${state.scores[0]} נק\u05F3 תרגול`;
  document.getElementById('s1Total').textContent=state.scores[1];
  document.getElementById('s2Total').textContent=state.scores[2];
  document.getElementById('s3Total').textContent=state.scores[3];
  const pct = state.mode === 'jeru' ? (state.level / 10) : (state.score / 500);
  var tier = pct > 0.8 ? 'gold' : pct > 0.4 ? 'silver' : 'bronze';
  var trophyEl = document.getElementById('resultsTrophy');
  if (trophyEl) {
    trophyEl.dataset.tier = tier;
    var iconName = tier === 'gold' ? 'trophy' : 'medal';
    trophyEl.innerHTML = '<i data-lucide="' + iconName + '" class="results-trophy-svg"></i>';
    refreshLucideIcons();
  }
  
  if (state.mode === 'practice') {
      document.getElementById('scoreSubmitArea').style.display = 'none';
  } else {
      document.getElementById('scoreSubmitArea').style.display = 'block';
  }
  
  document.getElementById('saveScoreMsg').style.display='none';
  document.getElementById('playerName').value='';
  document.getElementById('saveScoreBtn').disabled=false;
  document.getElementById('saveScoreBtn').textContent = 'שמור וצפה בטבלה';

  // Update breakdown labels/values if needed, or hide them
  if (state.mode === 'jeru') {
      setResultBreakdownLabels('רמה', 'איתור שכונות', 'בונוס: שיוך רחוב', 'בונוס: מפה');
      document.getElementById('s0Total').textContent = `רמה ${state.level}`;
      document.getElementById('s1Total').textContent = String(state.scores[1]);
      document.getElementById('s2Total').textContent = String(state.scores[2]);
      document.getElementById('s3Total').textContent = String(state.scores[3]);
  } else if (state.mode === 'trivia') {
      setResultBreakdownLabels('מסלול', '-', '-', 'ניקוד');
      document.getElementById('s0Total').textContent = `טריוויה`;
      document.getElementById('s1Total').textContent = '-';
      document.getElementById('s2Total').textContent = '-';
      document.getElementById('s3Total').textContent = state.score;
  }
}

// ============================================================
// EVENT LISTENERS
// ============================================================
function initHomeScreen() {
  var bar = document.getElementById('appVersionBar');
  if (bar && window.JG_CONFIG && window.JG_CONFIG.APP_VERSION) {
    bar.textContent = 'JeruGuesser v' + window.JG_CONFIG.APP_VERSION;
  }
  document.querySelectorAll('.btn-leaderboard').forEach(function (b) {
    b.disabled = false;
    b.style.opacity = '1';
  });
  var jeru = document.getElementById('startJeruBtn');
  var pr = document.getElementById('startPracticeBtn');
  if (jeru) {
    jeru.disabled = false;
    jeru.style.opacity = '1';
  }
  if (pr) {
    pr.disabled = false;
    pr.style.opacity = '1';
  }
  refreshLucideIcons();
  trackEvent('app_home_ready');
}

document.getElementById('startJeruBtn').onclick = function () {
  startJeru();
};
document.getElementById('startPracticeBtn').onclick = function () {
  startPractice();
};
document.getElementById('playAgain').onclick = () => showScreen('home');
document.getElementById('s0Back').onclick=()=>showScreen('home');
document.getElementById('s1Back').onclick=()=>showScreen('home');
document.getElementById('s2Back').onclick=()=>showScreen('home');
document.getElementById('s3Back').onclick=()=>showScreen('home');

document.getElementById('themeToggle').onclick = () => {
  document.body.classList.toggle('light-theme');
  refreshLucideIcons();
};

// LEADERBOARD LOGIC
document.getElementById('leaderboardBtn').onclick = () => showLeaderboard();
document.getElementById('lbBack').onclick = () => showScreen('home');

document.getElementById('saveScoreBtn').onclick = async () => {
  const name = document.getElementById('playerName').value.trim().slice(0, 40);
  if(!name) { alert('אנא הכנס/י שם בשביל לשמור את השיא'); return; }
  
  const totalPlay = state.scores[1]+state.scores[2]+state.scores[3];
  
  const btn = document.getElementById('saveScoreBtn');
  const msg = document.getElementById('saveScoreMsg');
  btn.disabled = true;
  btn.textContent = 'שומר...';
  
  try {
    const params = new URLSearchParams();
    const gName = state.mode === 'trivia' ? 'Jerusalem_Trivia' : 'JeruGuesser';
    params.append('gamename', gName);
    params.append('playerName', name);
    params.append('score', state.score);

    // Server-side (recommended): rate limiting, max name length, profanity filter, optional signed scores.
    const res = await fetch(`${CONFIG.API_BASE_URL}/webhook/add/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params
    });

    if (res.ok) {
      msg.style.display = 'block';
      msg.style.color = 'var(--green)';
      msg.textContent = 'התוצאה נשמרה בהצלחה!';
      trackEvent('leaderboard_save_ok', { gamename: gName });
      setTimeout(()=>showLeaderboard(), 1000);
    } else {
      throw new Error('Server error');
    }
  } catch(e) {
    msg.style.display = 'block';
    msg.style.color = 'var(--red)';
    msg.textContent = 'שגיאה בשמירה... אנא נסה/נסי שוב.';
    btn.disabled = false;
    btn.textContent = 'שמור וצפה בטבלה';
  }
};

async function showLeaderboard() {
  showScreen('leaderboard');
  const gName = state.mode === 'trivia' ? 'Jerusalem_Trivia' : 'JeruGuesser';
  document.getElementById('lbLoading').style.display = 'block';
  document.getElementById('lbLoading').textContent = `טוען נתונים עבור ${state.mode === 'trivia'?'טריוויה':'JeruGuesser'}...`;
  document.getElementById('lbCard').style.display = 'none';
  const tbody = document.getElementById('lbTableBody');
  tbody.innerHTML = '';
  
  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/webhook/gameScore?gamename=${gName}`);
    let data;
    if(res.ok) {
       const text = await res.text();
       try {
         data = text ? JSON.parse(text) : [];
       } catch (err) {
         console.warn('Failed to parse leaderboard JSON:', err);
         data = [];
       }
    } else {
       if (res.status === 500) {
         document.getElementById('lbLoading').textContent = 'שגיאת שרת (500) - ייתכן שישנה בעיה באוטומציה שניגשת למסד הנתונים.';
         return;
       }
       throw new Error('Network response was not ok');
    }
    
    if(Array.isArray(data)) {
        // filter out nulls/empties and sort descending by score
        data = data.filter(d => d && d.playerName);
        data.sort((a,b) => (Number(b.score)||0) - (Number(a.score)||0));
    } else if (data && data.playerName) {
        data = [data]; // If simple object
    } else {
        data = []; // Fallback 
    }
    
    document.getElementById('lbLoading').style.display = 'none';
    document.getElementById('lbCard').style.display = 'block';
    
    if(data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:1.5rem; color:var(--muted)">אין תוצאות עדיין... הראה להם מי הבוס!</td></tr>';
      return;
    }
    
    data.slice(0, 30).forEach((row, i) => { // show top 30
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
      
      const rank = document.createElement('td');
      rank.style.padding = '1rem 0.5rem';
      rank.textContent = String(i + 1);
      rank.className = 'lb-rank' + (i < 3 ? ' lb-rank-' + (i + 1) : '');
      
      const pName = document.createElement('td');
      pName.style.padding = '1rem 0.5rem';
      pName.style.fontWeight = 'bold';
      pName.textContent = row.playerName;
      
      const pScore = document.createElement('td');
      pScore.style.padding = '1rem 0.5rem';
      pScore.style.color = 'var(--gold)';
      pScore.style.fontWeight = '900';
      pScore.style.textAlign = 'left';
      pScore.textContent = row.score || 0;
      
      tr.appendChild(rank);
      tr.appendChild(pName);
      tr.appendChild(pScore);
      tbody.appendChild(tr);
    });
    
  } catch(e) {
    document.getElementById('lbLoading').textContent = 'שגיאה בגישה לשרת. בדוק/י את חיבור הרשת.';
  }
}
// ============================================================
// PWA SERVICE WORKER
// ============================================================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('sw.js', { updateViaCache: 'none' })
      .catch(err => {
        console.log('SW registration failed: ', err);
      });
  });
}

// Installation Logic
let deferredPrompt;
const installBtn = document.getElementById('installAppBtn');
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (installBtn) {
    installBtn.style.display = 'flex';
    refreshLucideIcons();
  }
});

if (installBtn) {
  installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to prompt: ${outcome}`);
    deferredPrompt = null;
    installBtn.style.display = 'none';
  });
}

window.addEventListener('appinstalled', () => {
  console.log('App installed');
  if (installBtn) installBtn.style.display = 'none';
});

window.showScreen = showScreen;
window.showLeaderboard = showLeaderboard;
window.startJeru = startJeru;
window.startPractice = startPractice;

initHomeScreen();

try {
  if (new URLSearchParams(window.location.search).get('screen') === 'leaderboard') {
    showLeaderboard();
  }
} catch (_) {}