import json

with open('js/i18n.js', 'r', encoding='utf-8') as f:
    code = f.read()

translit_func = """
window.tStreet = function(hebrewName) {
  if (window.currentLang === 'he') return hebrewName;
  if (!hebrewName) return hebrewName;
  
  // Simple mapping
  const map = {
    'א': 'A', 'ב': 'B', 'ג': 'G', 'ד': 'D', 'ה': 'H', 'ו': 'V', 'ז': 'Z',
    'ח': 'H', 'ט': 'T', 'י': 'Y', 'כ': 'K', 'ל': 'L', 'מ': 'M', 'נ': 'N',
    'ס': 'S', 'ע': 'A', 'פ': 'P', 'צ': 'Tz', 'ק': 'K', 'ר': 'R', 'ש': 'Sh',
    'ת': 'T', 'ך': 'k', 'ם': 'm', 'ן': 'n', 'ף': 'f', 'ץ': 'tz',
    '-': ' ', '"': '', "'": ''
  };
  
  // Common words translation
  const words = hebrewName.split(' ');
  const res = [];
  
  const common = {
    'רחוב': 'Rehov',
    'שדרות': 'Sderot',
    'דרך': 'Derech',
    'בן': 'Ben',
    'בת': 'Bat',
    'אבן': 'Ibn',
    'הר': 'Har',
    'כפר': 'Kfar',
    'מעלה': 'Maale',
    'משעול': 'Mishol',
    'סמטת': 'Simtat',
    'סמטה': 'Simta',
    'קרית': 'Kiryat',
    'רמת': 'Ramat',
    'נחל': 'Nahal',
    'ה': 'Ha',
    'א': 'A',
    'מבוא': 'Mevo'
  };

  for (let i = 0; i < words.length; i++) {
    let w = words[i];
    if (common[w]) {
      res.push(common[w]);
      continue;
    }
    
    // Check if it starts with 'ה' (The)
    let prefix = '';
    if (w.length > 2 && w.startsWith('ה')) {
      prefix = 'Ha';
      w = w.substring(1);
    }
    
    // transliterate character by character
    let engWord = '';
    for (let c of w) {
      if (map[c]) engWord += map[c];
      else engWord += c;
    }
    
    // Clean up double vowels or weird consonants
    engWord = engWord.toLowerCase();
    engWord = engWord.charAt(0).toUpperCase() + engWord.slice(1);
    if (prefix) engWord = prefix + engWord;
    
    res.push(engWord);
  }
  
  return res.join(' ');
};
"""

if "window.tStreet = " not in code:
    code += "\n" + translit_func
    
with open('js/i18n.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("i18n.js transliteration patched.")
