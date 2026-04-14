'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const utilsPath = path.join(__dirname, '..', 'js', 'game-utils.js');
const code = fs.readFileSync(utilsPath, 'utf8');
vm.runInThisContext(code, { filename: 'game-utils.js' });

const U = global.JGGameUtils;

assert.ok(U.haversine(31.78, 35.22, 31.78, 35.22) < 0.001);
const d = U.haversine(31.78, 35.22, 31.79, 35.23);
assert.ok(d > 0.5 && d < 20);

const pNear = U.neighborhoodMissPoints(0.5, 1);
const pFar = U.neighborhoodMissPoints(5, 1);
assert.ok(pNear > pFar);
assert.ok(U.neighborhoodMissPoints(10, 1) === 0);

const arr = [1, 2, 3, 4, 5];
const sh = U.shuffle(arr);
assert.strictEqual(sh.length, 5);
assert.deepStrictEqual(sh.slice().sort(function (a, b) { return a - b; }), [1, 2, 3, 4, 5]);

const picked = U.pick(['a', 'b', 'c', 'd'], 2);
assert.strictEqual(picked.length, 2);
picked.forEach(function (x) {
  assert.ok(['a', 'b', 'c', 'd'].indexOf(x) !== -1);
});

const perfect = U.streetMapGuessFromDistKm(0);
assert.strictEqual(perfect.pts, 500);
assert.strictEqual(perfect.isCorrect, true);

const mid = U.streetMapGuessFromDistKm(3.76);
assert.ok(mid.pts <= 200);
assert.strictEqual(mid.isCorrect, false);

console.log('jg-utils tests: ok');
