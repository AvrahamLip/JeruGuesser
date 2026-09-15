import re

with open('js/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Tile URL fix
tile_old = """function getTileUrl() {
  return document.body.classList.contains('light-theme')
    ? 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png'
    : 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png';
}"""
tile_new = """function getTileUrl() {
  return document.body.classList.contains('light-theme')
    ? 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}'
    : 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
}"""
code = code.replace(tile_old, tile_new)

# 2. Rail Detail translations
code = code.replace(
    "var perkLine =\n          state.level % 3 === 0\n            ? ' ברמה המתחלקת ב־3: מענה נכון בבונוס = +300 נק׳.'\n            : '';",
    "var perkLine = state.level % 3 === 0 ? (window.currentLang === 'en' ? ' Level multiple of 3: Correct bonus = +300 pts.' : ' ברמה המתחלקת ב־3: מענה נכון בבונוס = +300 נק׳.') : '';"
)

code = code.replace(
    "var tips = 'בחרו את השכונה שבה נמצא הרחוב.' + perkLine;",
    "var tips = (window.currentLang === 'en' ? 'Select the neighborhood where the street is located.' : 'בחרו את השכונה שבה נמצא הרחוב.') + perkLine;"
)

code = code.replace(
    "'ניקוד כולל: ' +\n          state.score +\n          ' · ברמה זו: ' +\n          earned +\n          '/' +\n          state.targetScore +\n          ' נק׳ · ' +\n          state.questionsInLevel +\n          ' שכונות'",
    "(window.currentLang === 'en' ? 'Total score: ' : 'ניקוד כולל: ') + state.score + (window.currentLang === 'en' ? ' · This level: ' : ' · ברמה זו: ') + earned + '/' + state.targetScore + (window.currentLang === 'en' ? ' pts · ' : ' נק׳ · ') + state.questionsInLevel + (window.currentLang === 'en' ? ' neighborhoods' : ' שכונות')"
)

with open('js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("Tiles and Rail text patched.")
