import sys
import json
import re
import pandas as pd
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

html_path = r"C:\Users\user\.gemini\antigravity-ide\brain\51d5c1ac-b066-4c24-a4fc-68799db94a23\.system_generated\steps\187\content.md"

with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Extract streets from HTML
# Look for <h3 ...>English Name</h3><span ... dir="rtl">Hebrew Name</span> ... <span ... map-pin ...>Neighborhood</span>
soup = BeautifulSoup(html_content, 'html.parser')
street_cards = soup.find_all('div', class_='bg-card')

guidebook_streets = {} # hebrew_street -> english_neighborhood
for card in street_cards:
    hebrew_spans = card.find_all('span', dir='rtl')
    if not hebrew_spans:
        continue
    hebrew_name = hebrew_spans[0].text.strip()
    
    # Find neighborhood (it has a map-pin icon)
    # The neighborhood span might just be the last span with text-xs text-muted-foreground
    pin_span = card.find('svg', class_='lucide-map-pin')
    if pin_span and pin_span.parent:
        neighborhood_en = pin_span.parent.text.strip()
        # Handle "Beit Hanina / Pisgat Ze'ev" by just taking the first or keeping it
        neighborhood_en = neighborhood_en.split(' / ')[0]
        guidebook_streets[hebrew_name] = neighborhood_en

print(f"Extracted {len(guidebook_streets)} streets with English neighborhoods from Guidebook.")

# Read our CSV
df = pd.read_csv('jerusalem_streets_complete.csv')
print(f"Read {len(df)} streets from our CSV.")

mapping = {}
for idx, row in df.iterrows():
    he_street = str(row['שם רחוב']).strip()
    he_neigh = str(row['שכונה עירונית']).strip()
    
    if he_street in guidebook_streets:
        en_neigh = guidebook_streets[he_street]
        # Only assign if we don't have a mapping yet or just collect them
        if he_neigh not in mapping:
            mapping[he_neigh] = set()
        mapping[he_neigh].add(en_neigh)

print("\nDerived Mapping (Hebrew -> English):")
final_mapping = {}
for he, en_set in mapping.items():
    # Pick the most common or just join them
    en_list = list(en_set)
    final_mapping[he] = en_list[0] if len(en_list) == 1 else " / ".join(en_list)
    print(f"{he} -> {final_mapping[he]}")

# We still need to map the 115 statistical areas (from GeoJSON)
with open('../jerusalem_neighborhoods.geojson', 'r', encoding='utf-8') as f:
    geo = json.load(f)

stat_areas = set(f['properties'].get('SCHN_NAME') for f in geo['features'] if f['properties'].get('SCHN_NAME'))

print("\nMapping Statistical Areas:")
geo_mapping = {}
for sa in sorted(stat_areas):
    # Try to find a match in the final_mapping
    # E.g. "פסגת זאב" in "פסגת זאב מזרח"
    matched_en = []
    for he, en in final_mapping.items():
        if he in sa or sa in he:
            matched_en.append(en)
    
    if matched_en:
        geo_mapping[sa] = matched_en[0]
        print(f"{sa} -> {matched_en[0]}")
    else:
        geo_mapping[sa] = ""
        print(f"{sa} -> NOT FOUND")

with open('en_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(geo_mapping, f, ensure_ascii=False, indent=2)

print("Saved en_mapping.json")
