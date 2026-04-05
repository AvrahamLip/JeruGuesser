"""
Final Jerusalem Streets Table Builder
======================================
Merges:
1. Jerusalem streets + municipal neighborhoods (already built: jerusalem_streets_neighborhoods.csv)
2. CBS Excel "רחובות ושכונות לאס 2022" - statistical area names
3. CBS ArcGIS statistical_areas_2022 - fetch polygons and spatial join for stat neighborhood name

Output: streets_jerusalem_complete.csv / .xlsx
Columns:
  שם רחוב | שכונה עירונית | שכונה סטטיסטית | מזרח/מערב | קו רוחב | קו אורך
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
import warnings
warnings.filterwarnings('ignore')
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
CBS_STAT_AREAS_URL = (
    "https://services8.arcgis.com/JcXY3lLZni6BK4El/arcgis/rest/services"
    "/statistical_areas_2022/FeatureServer/0"
)
PAGE_SIZE = 1000

# ─── Step 1: Load the existing streets table ─────────────────────────────────
print("=" * 65)
print("STEP 1: Loading existing Jerusalem streets table")
print("=" * 65)

df_streets = pd.read_csv("jerusalem_streets_neighborhoods.csv", encoding='utf-8-sig')
print(f"  Loaded {len(df_streets)} rows")
print(f"  Columns: {df_streets.columns.tolist()}")

# ─── Step 2: Parse CBS Excel for stat neighborhood names ─────────────────────
print("\n" + "=" * 65)
print("STEP 2: Parsing CBS Excel (רחובות ושכונות לאס 2022)")
print("=" * 65)

try:
    df_cbs = pd.read_excel("cbs_streets_neighborhoods_2022.xlsx", 
                           sheet_name="רחובות ושכונות לאס", 
                           engine='openpyxl')
    print(f"  Total rows: {len(df_cbs)}")
    print(f"  Columns: {df_cbs.columns.tolist()}")
    
    # Filter Jerusalem (yishuv code 3000)
    # Column 'סמל יישוב' = yishuv code
    if 'סמל יישוב' in df_cbs.columns:
        df_jer_cbs = df_cbs[df_cbs['סמל יישוב'] == 3000].copy()
        print(f"  Jerusalem rows: {len(df_jer_cbs)}")
        print(f"\n  First 10 Jerusalem entries:")
        print(df_jer_cbs.head(10).to_string())
        
        # Build mapping: stat area code → neighborhood names
        # 'א"ס' = statistical area code, 'שכונות' = neighborhood names
        # 'סמל א"ס מלא' = full stat area code (yishuv_code + area_code)
        df_jer_cbs.to_csv("cbs_jerusalem_stat_areas.csv", index=False, encoding='utf-8-sig')
        print(f"\n  ✓ Saved cbs_jerusalem_stat_areas.csv ({len(df_jer_cbs)} rows)")
    else:
        print(f"  Column 'סמל יישוב' not found. Available: {df_cbs.columns.tolist()}")
        # Show first row
        print(df_cbs.head(3).to_string())
        
except Exception as e:
    print(f"  Error: {e}")
    df_jer_cbs = pd.DataFrame()

# ─── Step 3: Download CBS Statistical Areas polygons ─────────────────────────
print("\n" + "=" * 65)
print("STEP 3: Downloading CBS Statistical Area polygons for Jerusalem")
print("=" * 65)

# The field for yishuv code is SEMEL_YISHUV
all_stat_features = []
offset = 0

while True:
    params = {
        "where": "SEMEL_YISHUV = 3000",
        "outFields": "OBJECTID,SEMEL_YISHUV,SHEM_YISHUV,STAT_2022,YISHUV_STAT_2022,ROVA,TAT_ROVA,COD_TIFKUD",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": PAGE_SIZE,
        "resultOffset": offset,
        "f": "json"
    }
    try:
        r = requests.get(CBS_STAT_AREAS_URL + "/query", params=params, headers=HEADERS, timeout=60)
        d = r.json()
        feats = d.get("features", [])
        if "error" in d:
            print(f"  Error: {d['error']}")
            break
        all_stat_features.extend(feats)
        print(f"  offset={offset}: got {len(feats)}, total={len(all_stat_features)}")
        if len(feats) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.3)
    except Exception as e:
        print(f"  Exception at offset={offset}: {e}")
        break

print(f"\n  Total CBS stat area features for Jerusalem: {len(all_stat_features)}")

if all_stat_features:
    # Show sample fields
    sample_attrs = all_stat_features[0]["attributes"]
    print(f"\n  Sample record:")
    for k, v in sample_attrs.items():
        print(f"    {k}: {v}")
    
    # Build GeoDataFrame
    rows_stat = []
    geoms = []
    
    for feat in all_stat_features:
        attrs = feat.get("attributes", {})
        geom = feat.get("geometry")
        
        if geom and "rings" in geom:
            # Polygon geometry
            from shapely.geometry import Polygon, MultiPolygon
            rings = geom["rings"]
            if len(rings) == 1:
                poly = Polygon(rings[0])
            else:
                # First ring = exterior, rest = holes, or multiple polygons
                exterior = rings[0]
                interior = rings[1:] if len(rings) > 1 else []
                poly = Polygon(exterior, interior)
        else:
            poly = None
        
        rows_stat.append(attrs)
        geoms.append(poly)
    
    df_stat = pd.DataFrame(rows_stat)
    gdf_stat = gpd.GeoDataFrame(df_stat, geometry=geoms, crs="EPSG:4326")
    
    print(f"\n  GeoDataFrame: {len(gdf_stat)} rows")
    print(f"  Columns: {gdf_stat.columns.tolist()}")
    print(f"  Valid geometries: {gdf_stat.geometry.is_valid.sum()}")
    
    # Save
    gdf_stat.to_file("cbs_stat_areas_jerusalem.geojson", driver="GeoJSON")
    print("  ✓ Saved cbs_stat_areas_jerusalem.geojson")

# ─── Step 4: Spatial join streets → CBS stat areas ────────────────────────────
print("\n" + "=" * 65)
print("STEP 4: Spatial join streets → CBS statistical areas")
print("=" * 65)

if all_stat_features and len(gdf_stat) > 0:
    # Build street points GeoDataFrame
    gdf_streets_pts = gpd.GeoDataFrame(
        df_streets.copy(),
        geometry=[Point(row['קו אורך'], row['קו רוחב']) for _, row in df_streets.iterrows()],
        crs="EPSG:4326"
    )
    
    # Make geometries valid
    gdf_stat['geometry'] = gdf_stat['geometry'].buffer(0)  # fix invalid geoms
    
    # Spatial join: which stat area does each street centroid fall in?
    gdf_joined = gpd.sjoin(
        gdf_streets_pts,
        gdf_stat[['STAT_2022', 'YISHUV_STAT_2022', 'ROVA', 'TAT_ROVA', 'geometry']],
        how='left',
        predicate='within'
    )
    
    matched = gdf_joined['STAT_2022'].notna().sum()
    unmatched = gdf_joined['STAT_2022'].isna().sum()
    print(f"  Matched: {matched} | Unmatched: {unmatched}")
    
    # For unmatched, use nearest
    if unmatched > 0:
        gdf_joined = gdf_joined.reset_index(drop=True)
        unmatched_idx = gdf_joined[gdf_joined['STAT_2022'].isna()].index
        gdf_unmatched = gdf_joined.loc[unmatched_idx, ['קו רוחב', 'קו אורך', 'geometry']].copy().reset_index(drop=True)
        
        gdf_nearest = gpd.sjoin_nearest(
            gdf_unmatched,
            gdf_stat[['STAT_2022', 'YISHUV_STAT_2022', 'ROVA', 'TAT_ROVA', 'geometry']],
            how='left'
        ).groupby(level=0).first().reset_index(drop=True)
        
        for i, (pos, row) in enumerate(zip(unmatched_idx, gdf_nearest.itertuples())):
            gdf_joined.at[pos, 'STAT_2022'] = row.STAT_2022
            gdf_joined.at[pos, 'ROVA'] = row.ROVA
            gdf_joined.at[pos, 'TAT_ROVA'] = row.TAT_ROVA
    
    # Merge CBS Excel data to get neighborhood name from stat area code
    # Join on STAT_2022 (= 'א"ס') and SEMEL_YISHUV=3000
    if len(df_jer_cbs) > 0 and 'א"ס' in df_jer_cbs.columns:
        stat_area_to_neigh = df_jer_cbs.set_index('א"ס')['שכונות'].to_dict()
        gdf_joined['שכונה סטטיסטית'] = gdf_joined['STAT_2022'].map(stat_area_to_neigh)
        print(f"  Matched with CBS Excel neighborhood names: {gdf_joined['שכונה סטטיסטית'].notna().sum()}")
    else:
        print("  CBS Excel data not available for name mapping")
        # Use ROVA (quarter/neighborhood code) as fallback
        gdf_joined['שכונה סטטיסטית'] = gdf_joined['ROVA'].fillna('').astype(str)
    
    # Build final table
    df_final = gdf_joined[[
        'שם רחוב', 'שכונה עירונית', 'שכונה סטטיסטית', 
        'מזרח/מערב', 'קו רוחב', 'קו אורך'
    ]].copy()
    
else:
    print("  No CBS stat area data available, using only municipal neighborhoods")
    df_final = df_streets.copy()
    df_final['שכונה סטטיסטית'] = ''
    df_final = df_final[['שם רחוב', 'שכונה עירונית', 'שכונה סטטיסטית', 'מזרח/מערב', 'קו רוחב', 'קו אורך']]

# ─── Step 5: Try CBS Excel as the primary stat neighborhood source ─────────────
print("\n" + "=" * 65)
print("STEP 5: Enriching with CBS Excel neighborhood names")
print("=" * 65)

# The CBS Excel has: שם יישוב, סמל א"ס מלא, סמל יישוב, א"ס, רחובות עיקריים, שכונות
# 'רחובות עיקריים' has street names, 'שכונות' has neighborhood names

if len(df_jer_cbs) > 0:
    print(f"  CBS Excel Jerusalem rows: {len(df_jer_cbs)}")
    print(f"  Columns: {df_jer_cbs.columns.tolist()}")
    
    if 'שכונות' in df_jer_cbs.columns:
        # Build set of unique CBS stat neighborhood names
        stat_neigh_names = df_jer_cbs['שכונות'].dropna().unique()
        print(f"  Unique CBS stat neighborhoods: {len(stat_neigh_names)}")
        print(f"  Sample names: {list(stat_neigh_names[:10])}")
    
    if 'א"ס' in df_jer_cbs.columns:
        # Building the stat area → neighborhood mapping
        stat_to_neigh = {}
        for _, row in df_jer_cbs.iterrows():
            stat_code = row.get('א"ס')
            neigh = row.get('שכונות', '')
            if pd.notna(stat_code) and pd.notna(neigh):
                stat_to_neigh[int(stat_code)] = str(neigh).strip()
        
        print(f"\n  Stat area → neighborhood mapping ({len(stat_to_neigh)} entries):")
        for code, neigh in list(stat_to_neigh.items())[:10]:
            print(f"    {code}: {neigh}")

# ─── Step 6: Finalize and export ──────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 6: Exporting complete table")
print("=" * 65)

# Clean up
df_final = df_final.drop_duplicates(subset=['שם רחוב', 'שכונה עירונית']).reset_index(drop=True)
df_final = df_final[df_final['שם רחוב'].astype(str).str.strip() != '']
df_final = df_final.sort_values(['שכונה עירונית', 'שם רחוב']).reset_index(drop=True)

print(f"  Final table: {len(df_final)} rows")
print(f"  Unique streets: {df_final['שם רחוב'].nunique()}")
print(f"  Unique municipal neighborhoods: {df_final['שכונה עירונית'].nunique()}")

# Save
df_final.to_csv("jerusalem_streets_complete.csv", index=False, encoding='utf-8-sig')
df_final.to_excel("jerusalem_streets_complete.xlsx", index=False, engine='openpyxl')
print(f"\n  ✓ Saved jerusalem_streets_complete.csv ({len(df_final)} rows)")
print(f"  ✓ Saved jerusalem_streets_complete.xlsx")

# Print preview
print("\n" + "=" * 65)
print("PREVIEW (first 40 rows):")
print("=" * 65)
print(df_final.head(40).to_string())

print("\n" + "=" * 65)
print("NEIGHBORHOOD COUNTS:")
print("=" * 65)
print(df_final.groupby('שכונה עירונית')['שם רחוב'].count().sort_values(ascending=False).to_string())
