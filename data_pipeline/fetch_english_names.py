import sys
import json
import requests
import time
import re

sys.stdout.reconfigure(encoding='utf-8')

# Load existing geojson
with open('../jerusalem_neighborhoods.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract unique Hebrew names
hebrew_names = set(f['properties'].get('SCHN_NAME') for f in data['features'] if f['properties'].get('SCHN_NAME'))
hebrew_names = sorted(list(hebrew_names))
print(f"Found {len(hebrew_names)} unique neighborhoods.")

def clean_name(name):
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip()

mapping = {}

def get_english_title(he_title):
    url = "https://he.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "langlinks",
        "titles": he_title,
        "lllang": "en",
        "format": "json"
    }
    try:
        resp = requests.get(url, params=params).json()
        pages = resp.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if 'langlinks' in page_data:
                return page_data['langlinks'][0]['*']
    except Exception as e:
        pass
    return None

def search_wikipedia(he_name):
    # Search hebrew wikipedia
    url = "https://he.wikipedia.org/w/api.php"
    query = clean_name(he_name) + " (שכונה)"
    
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json"
    }
    try:
        resp = requests.get(url, params=params).json()
        search_res = resp.get('query', {}).get('search', [])
        if not search_res:
             # try without (שכונה)
             params["srsearch"] = clean_name(he_name) + " ירושלים"
             resp = requests.get(url, params=params).json()
             search_res = resp.get('query', {}).get('search', [])
             
        if search_res:
            top_title = search_res[0]['title']
            return get_english_title(top_title)
    except:
        pass
    return None

print("Fetching from Wikipedia...")
for i, he_name in enumerate(hebrew_names):
    en_name = search_wikipedia(he_name)
    if en_name:
        mapping[he_name] = en_name
        print(f"[{i+1}/{len(hebrew_names)}] {he_name} -> {en_name}")
    else:
        print(f"[{i+1}/{len(hebrew_names)}] {he_name} -> NOT FOUND")
        mapping[he_name] = ""
    time.sleep(0.1)

# Save mapping
with open('en_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print("\nSaved en_mapping.json")
