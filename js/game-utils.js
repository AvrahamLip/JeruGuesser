(function (g) {
  'use strict';
  function haversine(lat1, lon1, lat2, lon2) {
    var R = 6371;
    var dLat = ((lat2 - lat1) * Math.PI) / 180;
    var dLon = ((lon2 - lon1) * Math.PI) / 180;
    var a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }
  /** Partial credit when wrong neighborhood chosen (same formula as geo game). */
  function neighborhoodMissPoints(distKm, level) {
    var penaltyPerKm = 100 + Math.floor((level - 1) / 3) * 50;
    return Math.max(0, Math.round(500 - distKm * penaltyPerKm));
  }
  /** Fisher–Yates shuffle (copy). */
  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i];
      a[i] = a[j];
      a[j] = t;
    }
    return a;
  }
  function pick(arr, n) {
    return shuffle(arr).slice(0, n);
  }
  /** Stage-3 non-trivia: distance in km between guess and correct point. */
  function streetMapGuessFromDistKm(distKm) {
    var pts = Math.max(0, Math.round(500 - distKm * 80));
    return { pts: pts, isCorrect: pts > 200 };
  }
  g.JGGameUtils = {
    haversine: haversine,
    neighborhoodMissPoints: neighborhoodMissPoints,
    shuffle: shuffle,
    pick: pick,
    streetMapGuessFromDistKm: streetMapGuessFromDistKm
  };
})(typeof window !== 'undefined' ? window : globalThis);
