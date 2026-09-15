import sys

with open('js/app.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Stage 2 Street Name
code = code.replace(
    "document.getElementById('s2StreetName').textContent = q['שם רחוב'];",
    "document.getElementById('s2StreetName').textContent = window.tStreet ? window.tStreet(q['שם רחוב']) : q['שם רחוב'];"
)

# 2. syncRailKicker translations
code = code.replace(
    "el.textContent = 'תרגול · מפה עם שמות שכונות';",
    "el.textContent = window.currentLang === 'en' ? 'Practice · Map with Neighborhood Names' : 'תרגול · מפה עם שמות שכונות';"
)
code = code.replace(
    "if (stageNum === 2) el.textContent = 'טריוויה · שיוך רחוב לשכונה';",
    "if (stageNum === 2) el.textContent = window.currentLang === 'en' ? 'Trivia · Match Street to Neighborhood' : 'טריוויה · שיוך רחוב לשכונה';"
)
code = code.replace(
    "else if (stageNum === 3) el.textContent = 'טריוויה · מיקום במפה';",
    "else if (stageNum === 3) el.textContent = window.currentLang === 'en' ? 'Trivia · Locate on Map' : 'טריוויה · מיקום במפה';"
)
code = code.replace(
    "else el.textContent = 'טריוויה';",
    "else el.textContent = window.currentLang === 'en' ? 'Trivia' : 'טריוויה';"
)
code = code.replace(
    "if (stageNum === 2) el.textContent = 'שיוך רחוב · בונוס סיום רמה';",
    "if (stageNum === 2) el.textContent = window.currentLang === 'en' ? 'Street Match · Level Bonus' : 'שיוך רחוב · בונוס סיום רמה';"
)
code = code.replace(
    "else if (stageNum === 1) el.textContent = 'איתור שכונה · ללא שמות';",
    "else if (stageNum === 1) el.textContent = window.currentLang === 'en' ? 'Find Neighborhood · No Names' : 'איתור שכונה · ללא שמות';"
)
code = code.replace(
    "el.textContent = 'איתור שכונה · ללא שמות';",
    "el.textContent = window.currentLang === 'en' ? 'Find Neighborhood · No Names' : 'איתור שכונה · ללא שמות';"
)
code = code.replace(
    "el.textContent = 'שיוך רחוב לשכונה';",
    "el.textContent = window.currentLang === 'en' ? 'Match Street to Neighborhood' : 'שיוך רחוב לשכונה';"
)

# 3. showResults
code = code.replace(
    "document.getElementById('s0Total').textContent=`${state.scores[0]} נק\u05F3 תרגול`;",
    "document.getElementById('s0Total').textContent=window.currentLang === 'en' ? `${state.scores[0]} Practice pts` : `${state.scores[0]} נק\u05F3 תרגול`;"
)
code = code.replace(
    "setResultBreakdownLabels('רמה', 'איתור שכונות', 'בונוס', '-');",
    "setResultBreakdownLabels(window.currentLang === 'en' ? 'Level' : 'רמה', window.currentLang === 'en' ? 'Find Neighborhoods' : 'איתור שכונות', window.currentLang === 'en' ? 'Bonus' : 'בונוס', '-');"
)
code = code.replace(
    "document.getElementById('s0Total').textContent = `רמה ${state.level}`;",
    "document.getElementById('s0Total').textContent = window.currentLang === 'en' ? `Level ${state.level}` : `רמה ${state.level}`;"
)
code = code.replace(
    "setResultBreakdownLabels('מסלול', 'ניקוד', '-', '-');",
    "setResultBreakdownLabels(window.currentLang === 'en' ? 'Mode' : 'מסלול', window.currentLang === 'en' ? 'Score' : 'ניקוד', '-', '-');"
)
code = code.replace(
    "document.getElementById('s0Total').textContent = `טריוויה`;",
    "document.getElementById('s0Total').textContent = window.currentLang === 'en' ? `Trivia` : `טריוויה`;"
)
code = code.replace(
    "setResultBreakdownLabels('שלב 0', 'שלב 1', 'שלב 2', '-');",
    "setResultBreakdownLabels(window.currentLang === 'en' ? 'Stage 0' : 'שלב 0', window.currentLang === 'en' ? 'Stage 1' : 'שלב 1', window.currentLang === 'en' ? 'Stage 2' : 'שלב 2', '-');"
)

# 4. updateSUI
code = code.replace(
    "document.getElementById('s0ContextMain').textContent = 'שאלה ' + (state.round + 1);",
    "document.getElementById('s0ContextMain').textContent = (window.currentLang === 'en' ? 'Question ' : 'שאלה ') + (state.round + 1);"
)
code = code.replace(
    "document.getElementById('s' + stageNum + 'ContextMain').textContent =\n        'רמה ' + state.level + ' · בונוס סיום רמה';",
    "document.getElementById('s' + stageNum + 'ContextMain').textContent = (window.currentLang === 'en' ? 'Level ' : 'רמה ') + state.level + (window.currentLang === 'en' ? ' · Level Bonus' : ' · בונוס סיום רמה');"
)
code = code.replace(
    "document.getElementById('s1ContextMain').textContent =\n        'רמה ' + state.level + ' – שאלה ' + (state.round + 1) + '/' + state.questionsInLevel;",
    "document.getElementById('s1ContextMain').textContent = (window.currentLang === 'en' ? 'Level ' : 'רמה ') + state.level + (window.currentLang === 'en' ? ' – Question ' : ' – שאלה ') + (state.round + 1) + '/' + state.questionsInLevel;"
)


# 5. Leaderboard headers inside showLeaderboard() are static in HTML, but error messages inside it:
code = code.replace(
    "document.getElementById('lbLoading').textContent = `טוען נתונים עבור ${state.mode === 'trivia'?'טריוויה':'JeruGuesser'}...`;",
    "document.getElementById('lbLoading').textContent = window.currentLang === 'en' ? `Loading data for ${state.mode === 'trivia'?'Trivia':'JeruGuesser'}...` : `טוען נתונים עבור ${state.mode === 'trivia'?'טריוויה':'JeruGuesser'}...`;"
)
code = code.replace(
    "tbody.innerHTML = '<tr><td colspan=\"4\" style=\"text-align:center; padding:1.5rem; color:var(--muted)\">אין תוצאות עדיין... הראה להם מי הבוס!</td></tr>';",
    "tbody.innerHTML = window.currentLang === 'en' ? '<tr><td colspan=\"4\" style=\"text-align:center; padding:1.5rem; color:var(--muted)\">No results yet... Show them who\\'s boss!</td></tr>' : '<tr><td colspan=\"4\" style=\"text-align:center; padding:1.5rem; color:var(--muted)\">אין תוצאות עדיין... הראה להם מי הבוס!</td></tr>';"
)


with open('js/app.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("app.js translated sections patched.")
