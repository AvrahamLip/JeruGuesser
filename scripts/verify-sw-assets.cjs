'use strict';
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const configPath = path.join(root, 'config.js');

function readConfigString(key) {
  const t = fs.readFileSync(configPath, 'utf8');
  const re = new RegExp(key + ':\\s*\'([^\']+)\'');
  const m = t.match(re);
  return m ? m[1] : '';
}

const V = readConfigString('APP_VERSION');
if (!V) {
  console.error('Could not read APP_VERSION from config.js');
  process.exit(1);
}
const Q = '?v=' + encodeURIComponent(V);
const GEO = readConfigString('GEOJSON_FILENAME') || 'jerusalem_neighborhoods.geojson';

const files = [
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

const missing = [];
for (var i = 0; i < files.length; i++) {
  var fp = path.join(root, files[i].split('?')[0]);
  if (!fs.existsSync(fp)) missing.push(files[i].split('?')[0]);
}
if (missing.length) {
  console.error('SW cache: missing files:', missing);
  process.exit(1);
}
console.log('SW assets verify: OK (' + files.length + ' files, v' + V + ')');
