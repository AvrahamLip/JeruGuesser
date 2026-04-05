"""
Jerusalem Streets + Neighborhoods Table Builder (FINAL)
========================================================
Sources:
1. Streets: ArcGIS FeatureServer (IYUfZFmrlf94i3k0 - Jerusalem Municipality)
   - 32,869 features, field: "street" = Hebrew street name
   - Geometry: polylines → we take centroid as representative point
2. Municipal Neighborhoods: jerusalem_neighborhoods.geojson (already downloaded)
   - Fields: CODE, SCHN_NAME (neighborhood name), East_West
3. Spatial Join: each street segment centroid → municipal neighborhood

Pipeline:
  a. Fetch all streets from ArcGIS (paginated)
  b. Load municipal neighborhoods
  c. Compute each polyline centroid → WGS84 lat/lon
  d. Spatial join: centroid in which neighborhood polygon?
  e. Deduplicate: one row per (street_name, neighborhood_name)
  f. Export to CSV and Excel

Output table columns:
  - שם רחוב
  - שכונה עירונית רשמית
  - מזרח/מערב (East_West)
  - קו רוחב (lat)
  - קו אורך (lon)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape, LineString, MultiLineString
import warnings
warnings.filterwarnings('ignore')
import time
import math

# ─── Configuration ─────────────────────────────────────────────────────────
STREETS_BASE_URL = (
    "https://services.arcgis.com/IYUfZFmrlf94i3k0/arcgis/rest/services/Streets"
    "/FeatureServer/0/query"
)
NEIGHBORHOODS_FILE = "jerusalem_neighborhoods.geojson"
OUTPUT_CSV = "jerusalem_streets_neighborhoods.csv"
OUTPUT_XLSX = "jerusalem_streets_neighborhoods.xlsx"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
PAGE_SIZE = 1000   # ArcGIS often limits to 1000 per request

# ─── Step 1: Fetch all streets from ArcGIS ─────────────────────────────────
print("=" * 65)
print("STEP 1: Fetching all Jerusalem street segments from ArcGIS")
print("=" * 65)

def fetch_streets_page(offset, page_size=PAGE_SIZE):
    params = {
        "where": "street IS NOT NULL AND street <> ' '",
        "outFields": "OBJECTID,street,RoadType,RoadFuncti",
        "returnGeometry": "true",
        "geometryType": "esriGeometryPolyline",
        "outSR": "4326",        # WGS84 directly
        "f": "json",
        "resultOffset": offset,
        "resultRecordCount": page_size,
    }
    for attempt in range(3):
        try:
            r = requests.get(STREETS_BASE_URL, params=params, headers=HEADERS, timeout=60)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                print(f"  API error at offset {offset}: {data['error']}")
                return []
            features = data.get("features", [])
            return features
        except Exception as e:
            print(f"  Attempt {attempt+1} failed (offset={offset}): {e}")
            time.sleep(2)
    return []

# Get total count first
count_params = {
    "where": "street IS NOT NULL AND street <> ' '",
    "returnCountOnly": "true",
    "f": "json"
}
try:
    r = requests.get(STREETS_BASE_URL, params=count_params, headers=HEADERS, timeout=30)
    total_count = r.json().get("count", 32869)
    print(f"  Total street features to fetch: {total_count}")
except:
    total_count = 32869
    print(f"  Using estimated total: {total_count}")

all_features = []
offset = 0
page_num = 0

while offset < total_count:
    page_num += 1
    print(f"  Fetching page {page_num} (offset={offset})...", end="", flush=True)
    features = fetch_streets_page(offset)
    if not features:
        print(f" empty, stopping.")
        break
    all_features.extend(features)
    print(f" got {len(features)} → total {len(all_features)}")
    offset += PAGE_SIZE
    if len(features) < PAGE_SIZE:
        print(f"  Last page reached (got {len(features)} < {PAGE_SIZE})")
        break
    time.sleep(0.3)  # be polite

print(f"\n  Total street features fetched: {len(all_features)}")

# ─── Step 2: Convert to GeoDataFrame ───────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 2: Converting to GeoDataFrame")
print("=" * 65)

rows = []
for feat in all_features:
    attrs = feat.get("attributes", {})
    geom = feat.get("geometry")
    
    if not geom:
        continue
    
    # Build Shapely geometry from esri JSON
    # For polylines: paths is a list of coordinate arrays
    paths = geom.get("paths", [])
    if not paths:
        continue
    
    # Collect all points from all paths
    all_coords = []
    for path in paths:
        all_coords.extend(path)  # each coord is [lon, lat] in WGS84
    
    if not all_coords:
        continue
    
    # Representative point = midpoint of the linestring
    mid_idx = len(all_coords) // 2
    lon, lat = all_coords[mid_idx][0], all_coords[mid_idx][1]
    
    rows.append({
        "OBJECTID": attrs.get("OBJECTID"),
        "street_name": attrs.get("street", "").strip(),
        "road_type": attrs.get("RoadType"),
        "road_function": attrs.get("RoadFuncti", ""),
        "lon": lon,
        "lat": lat,
        "geometry": Point(lon, lat)
    })

df_streets = pd.DataFrame(rows)
print(f"  Converted {len(df_streets)} street segments")
print(f"  Unique street names: {df_streets['street_name'].nunique()}")

# Create GeoDataFrame
gdf_streets = gpd.GeoDataFrame(df_streets, geometry="geometry", crs="EPSG:4326")

# ─── Step 3: Load municipal neighborhoods ──────────────────────────────────
print("\n" + "=" * 65)
print("STEP 3: Loading municipal neighborhoods")
print("=" * 65)

with open(NEIGHBORHOODS_FILE, 'r', encoding='utf-8') as f:
    neigh_data = json.load(f)

gdf_neigh = gpd.GeoDataFrame.from_features(neigh_data['features'], crs="EPSG:4326")
print(f"  Loaded {len(gdf_neigh)} neighborhood polygons")
print(f"  Columns: {gdf_neigh.columns.tolist()}")
print(f"  Sample names: {gdf_neigh['SCHN_NAME'].dropna().head(5).tolist()}")

# ─── Step 4: Spatial Join ────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 4: Spatial join - streets to neighborhoods")
print("=" * 65)

# Points within polygons
gdf_joined = gpd.sjoin(
    gdf_streets,
    gdf_neigh[['CODE', 'SCHN_NAME', 'East_West', 'geometry']],
    how='left',
    predicate='within'
)

print(f"  After spatial join: {len(gdf_joined)} rows")
matched = gdf_joined['SCHN_NAME'].notna().sum()
unmatched = gdf_joined['SCHN_NAME'].isna().sum()
print(f"  Matched: {matched} | Unmatched: {unmatched}")

# For unmatched streets (outside polygon bounds), find nearest neighborhood
# Reset index to avoid alignment issues from sjoin duplicate rows
gdf_joined = gdf_joined.reset_index(drop=True)

if unmatched > 0:
    print(f"  Finding nearest neighborhood for {unmatched} unmatched streets...")
    unmatched_idx = gdf_joined[gdf_joined['SCHN_NAME'].isna()].index
    gdf_unmatched = gdf_joined.loc[unmatched_idx, ['lat', 'lon', 'geometry']].copy().reset_index(drop=True)
    
    # Use nearest join - may produce duplicates if equidistant, so dedup by taking first match
    gdf_nearest = gpd.sjoin_nearest(
        gdf_unmatched,
        gdf_neigh[['CODE', 'SCHN_NAME', 'East_West', 'geometry']],
        how='left'
    )
    # Keep only first match per original row
    gdf_nearest = gdf_nearest.groupby(level=0).first().reset_index(drop=True)
    
    # Update using numpy positional indexing
    unmatched_positions = [gdf_joined.index.get_loc(i) for i in unmatched_idx]
    for pos, (_, row) in zip(unmatched_positions, gdf_nearest.iterrows()):
        gdf_joined.iloc[pos, gdf_joined.columns.get_loc('SCHN_NAME')] = row.get('SCHN_NAME')
        gdf_joined.iloc[pos, gdf_joined.columns.get_loc('East_West')] = row.get('East_West')
    
    still_unmatched = gdf_joined['SCHN_NAME'].isna().sum()
    print(f"  After nearest join: {still_unmatched} still unmatched")

# ─── Step 5: Build final table ───────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 5: Building and deduplicating final table")
print("=" * 65)

df_final = gdf_joined[['street_name', 'SCHN_NAME', 'East_West', 'lat', 'lon']].copy()

# Rename columns to Hebrew
df_final = df_final.rename(columns={
    'street_name': 'שם רחוב',
    'SCHN_NAME': 'שכונה עירונית',
    'East_West': 'מזרח/מערב',
    'lat': 'קו רוחב',
    'lon': 'קו אורך',
})

# Remove empty street names
df_final = df_final[df_final['שם רחוב'].str.len() > 0]

# Round coordinates
df_final['קו רוחב'] = df_final['קו רוחב'].round(6)
df_final['קו אורך'] = df_final['קו אורך'].round(6)

print(f"  Before dedup: {len(df_final)} rows")

# Deduplicate: keep one row per (street_name, neighborhood)
# For the representative point: keep middle segment's coordinates
df_dedup = (
    df_final
    .sort_values('שם רחוב')
    .drop_duplicates(subset=['שם רחוב', 'שכונה עירונית'], keep='first')
    .reset_index(drop=True)
)

print(f"  After dedup: {len(df_dedup)} rows")
print(f"  Unique streets: {df_dedup['שם רחוב'].nunique()}")
print(f"  Unique neighborhoods: {df_dedup['שכונה עירונית'].nunique()}")

# Sort by neighborhood, then street name
df_dedup = df_dedup.sort_values(['שכונה עירונית', 'שם רחוב']).reset_index(drop=True)

# ─── Step 6: Export ──────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 6: Exporting results")
print("=" * 65)

# CSV with UTF-8-BOM for Excel compatibility
df_dedup.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"  ✓ Saved CSV: {OUTPUT_CSV} ({len(df_dedup)} rows)")

# Excel
df_dedup.to_excel(OUTPUT_XLSX, index=False, engine='openpyxl')
print(f"  ✓ Saved Excel: {OUTPUT_XLSX}")

# ─── Summary Print ────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("PREVIEW (first 30 rows):")
print("=" * 65)
print(df_dedup.head(30).to_string(index=True))

print("\n" + "=" * 65)
print("NEIGHBORHOOD SUMMARY:")
print("=" * 65)
neigh_summary = df_dedup.groupby('שכונה עירונית')['שם רחוב'].count().sort_values(ascending=False)
print(neigh_summary.to_string())

print("\n✅ Done! Results saved to:")
print(f"   {OUTPUT_CSV}")
print(f"   {OUTPUT_XLSX}")
