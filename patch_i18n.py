import json
import re

with open('js/i18n.js', 'r', encoding='utf-8') as f:
    code = f.read()

# I will find window.JG_UI_I18N and replace it with a larger version
new_i18n_code = """window.JG_UI_I18N = {
  "he": {
    "title": "JeruGuesser",
    "subtitle": "מסע בין רחובות ושכונות ירושלים",
    "btn-start": "התחל JeruGuesser",
    "btn-practice": "תרגול חופשי",
    "btn-leaderboard": "טבלת אלופים",
    "btn-install": "התקן אפליקציה",
    "footer-credit": "תיכנון ופיתוח",
    "footer-donate": "תרומה",
    "footer-about": "אודות",
    "footer-contact": "צור קשר",
    "contact-title": "צור קשר",
    "contact-name": "שם מלא:",
    "contact-email": "אימייל:",
    "contact-message": "הודעה:",
    "contact-submit": "שלח הודעה",
    "back": "← חזור",
    "about-title": "אודות JeruGuesser",
    "feedback-next": "הבא →",
    "feedback-correct": "נכון!",
    "feedback-wrong": "לא בדיוק...",
    "game-find": "מצא את השכונה:",
    "game-end": "סיימת את המשחק!",
    "game-score": "הניקוד שלך:"
  },
  "en": {
    "title": "JeruGuesser",
    "subtitle": "A journey through Jerusalem's streets and neighborhoods",
    "btn-start": "Start JeruGuesser",
    "btn-practice": "Free Practice",
    "btn-leaderboard": "Leaderboard",
    "btn-install": "Install App",
    "footer-credit": "Design & Dev",
    "footer-donate": "Donate",
    "footer-about": "About",
    "footer-contact": "Contact",
    "contact-title": "Contact Us",
    "contact-name": "Full Name:",
    "contact-email": "Email:",
    "contact-message": "Message:",
    "contact-submit": "Send Message",
    "back": "← Back",
    "about-title": "About JeruGuesser",
    "feedback-next": "Next →",
    "feedback-correct": "Correct!",
    "feedback-wrong": "Not quite...",
    "game-find": "Find neighborhood:",
    "game-end": "Game Over!",
    "game-score": "Your Score:"
  }
};"""

code = re.sub(r'window\.JG_UI_I18N\s*=\s*\{.*?\n};\n', new_i18n_code + "\n", code, flags=re.DOTALL)

with open('js/i18n.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("i18n.js patched.")
