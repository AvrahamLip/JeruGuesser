import pandas as pd
import json
import time
from deep_translator import GoogleTranslator

print("Loading streets from CSV...")
df = pd.read_csv('jerusalem_streets_complete.csv')
streets = sorted(list(set(df['שם רחוב'].dropna().astype(str))))

print(f"Translating {len(streets)} unique streets...")
translator = GoogleTranslator(source='iw', target='en')

street_map = {}
batch_size = 50

for i in range(0, len(streets), batch_size):
    batch = streets[i:i+batch_size]
    # Join with a delimiter that Google Translate won't mess up too much, like " | "
    text_to_translate = " | ".join(batch)
    try:
        translated_text = translator.translate(text_to_translate)
        # Split back
        translated_batch = [s.strip() for s in translated_text.split('|')]
        
        # If lengths match, map them
        if len(batch) == len(translated_batch):
            for he, en in zip(batch, translated_batch):
                street_map[he] = en
        else:
            # Fallback to one-by-one for this batch if split failed
            print(f"Batch {i} length mismatch, falling back to one-by-one...")
            for he in batch:
                street_map[he] = translator.translate(he)
    except Exception as e:
        print(f"Error on batch {i}: {e}")
        time.sleep(2)
        # One-by-one fallback
        for he in batch:
            try:
                street_map[he] = translator.translate(he)
            except Exception as e2:
                print(f"Failed to translate {he}: {e2}")
                street_map[he] = he # fallback to original

    print(f"Progress: {min(i+batch_size, len(streets))}/{len(streets)}")
    time.sleep(1) # Be nice to the API

with open('street_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(street_map, f, ensure_ascii=False, indent=2)

print("Saved street_mapping.json")
