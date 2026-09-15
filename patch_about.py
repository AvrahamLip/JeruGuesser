import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add data-i18n-html="about-content" to about-container
html = html.replace('<div class="about-container">', '<div class="about-container" id="aboutContainer">')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('js/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

# Update updateUIForLanguage in js/app.js (Wait, updateUIForLanguage is in i18n.js!)
with open('js/i18n.js', 'r', encoding='utf-8') as f:
    i18n_js = f.read()

about_he = """<div class="about-card glass">
      <p class="about-lead">המפה עיוורת, אבל הלב ירושלמי? בואו נראה אתכם.</p>
      <p>בתור בן לאב ירושלמי מלידה, גדלתי על התחושה שירושלים היא הבית השני שלי. אבל המציאות החליטה לעשות לי "מבחן פתע".</p>
      <p>במהלך המילואים בפיקוד העורף, במבצע "שאגת הארי", שירתי בירושלים. תחת התראות ואזעקות, מצאתי את עצמי מנווט ברחבי העיר ודי מהר נחתה עליי ההבנה המביכה: אני לא באמת מכיר את העיר הזאת.</p>
      <p>באחד הערבים, ישבנו בצוות וחשבנו איך אפשר ללמוד באמת את השכונות הרבות בעיר ואת המיקום המדויק שלהן. מתוך המתח של המבצע והרצון להכיר את העיר לעומק, צמח לו משחק.</p>
      <p>ככה נולד <strong>JeruGuesser</strong> – אתגר זיהוי שכונות על מפה עיוורת.</p>
      <p>אין תמונות של הכותל או רמזים ויזואליים. רק אתם והמפה. המשחק מוקדש לכל אוהבי ירושלים ולכל אלו שבטוחים שהם מכירים את העיר טוב יותר מנהג מונית ותיק. ראו הוזהרתם – זה הרבה יותר מאתגר ממה שזה נראה.</p>
    </div>"""

about_en = """<div class="about-card glass">
      <p class="about-lead">The map is blind, but is your heart Jerusalemite? Let's see what you've got.</p>
      <p>As the son of a Jerusalemite father, I grew up feeling that Jerusalem was my second home. But reality decided to give me a "pop quiz".</p>
      <p>During my reserve duty in the Home Front Command, in Operation "Lion's Roar", I served in Jerusalem. Under alerts and sirens, I found myself navigating the city and quite quickly the embarrassing realization hit me: I don't really know this city.</p>
      <p>One evening, our team sat down and thought about how we could truly learn the city's many neighborhoods and their exact locations. Out of the tension of the operation and the desire to know the city deeply, a game grew.</p>
      <p>That's how <strong>JeruGuesser</strong> was born – a neighborhood identification challenge on a blind map.</p>
      <p>There are no pictures of the Western Wall or visual clues. Just you and the map. The game is dedicated to all Jerusalem lovers and to all those who are sure they know the city better than a veteran taxi driver. Be warned - it is much more challenging than it looks.</p>
    </div>"""

if 'window.JG_UI_I18N = {' in i18n_js:
    # We can just append to the dictionary programmatically using JS if we want, or do string replacement
    i18n_js = i18n_js.replace('"about-title": "אודות JeruGuesser",', f'"about-title": "אודות JeruGuesser",\n    "about-content": `{about_he}`,')
    i18n_js = i18n_js.replace('"about-title": "About JeruGuesser",', f'"about-title": "About JeruGuesser",\n    "about-content": `{about_en}`,')

# Update updateUIForLanguage to handle about-content
new_logic = """
  const aboutContainer = document.getElementById('aboutContainer');
  if (aboutContainer && window.t('about-content')) {
    aboutContainer.innerHTML = window.t('about-content');
  }
"""
if "aboutContainer" not in i18n_js:
    i18n_js = i18n_js.replace("const toggleBtn = document.getElementById('langToggleBtn');", new_logic + "\n  const toggleBtn = document.getElementById('langToggleBtn');")

with open('js/i18n.js', 'w', encoding='utf-8') as f:
    f.write(i18n_js)

print("About translation patched.")
