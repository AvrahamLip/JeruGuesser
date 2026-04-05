"""
Add CBS Statistical Neighborhoods to Jerusalem Streets Table
============================================================
Fetches the CBS Statistical Neighborhoods layer from ArcGIS,
spatial-joins it to our street points, and adds the stat neighborhood name.

Statistical Area layer: IsraelData - Statistical Areas 2022
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')
import time

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# ─── Fetch CBS Statistical Areas for Jerusalem ────────────────────────────────
# CBS ArcGIS hub – statistical neighborhoods (שכונות סטטיסטיות) yishuv_code 3000
STAT_NEIGH_URL = (
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services"
    "/Stat_Areas_Boundaries_2022/FeatureServer/0/query"
)

print("=" * 65)
print("Fetching CBS Statistical Neighborhoods (Jerusalem)")
print("=" * 65)

# First check schema
params_info = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
try:
    r = requests.get(STAT_NEIGH_URL, params=params_info, headers=HEADERS, timeout=30)
    data = r.json()
    if "count" in data:
        print(f"  Total statistical areas: {data['count']}")
    else:
        print(f"  Response: {str(data)[:300]}")
except Exception as e:
    print(f"  Error: {e}")

# Try alternative CBS URL (from ArcGIS Online)
ALT_URLS = [
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services/Stat_Areas_Boundaries_2022/FeatureServer/0",
    "https://services.arcgis.com/IYUfZFmrlf94i3k0/arcgis/rest/services/StatisticalAreas/FeatureServer/0",
    "https://hub.arcgis.com/api/v3/datasets/IsraelData::statistical-areas-2022/layers/0/query?where=1%3D1&outFields=*&returnGeometry=true&f=json",
]

stat_gdf = None
for url in ALT_URLS:
    print(f"\n  Trying: {url[:80]}...")
    try:
        if "hub.arcgis" in url:
            r = requests.get(url, headers=HEADERS, timeout=60)
        else:
            r = requests.get(
                url + "/query",
                params={"where": "1=1", "outFields": "*", "returnCountOnly": "true", "f": "json"},
                headers=HEADERS,
                timeout=30
            )
        data = r.json()
        if "count" in data:
            print(f"    → COUNT: {data['count']}")
            break
        elif "features" in data:
            print(f"    → Features: {len(data.get('features', []))}")
            break
        else:
            print(f"    → Response: {str(data)[:200]}")
    except Exception as e:
        print(f"    → Error: {e}")

# ─── Try ArcGIS Hub OGC API ───────────────────────────────────────────────────
print("\n" + "=" * 65)
print("Fetching from ArcGIS Hub (IsraelData CBS)")
print("=" * 65)

# From what the browser found: hub.arcgis.com/datasets/IsraelData::statistical-areas-2022
HUB_FEATURE_URL = (
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services"
    "/Statistical_Areas_2022_IsraelData/FeatureServer/0/query"
)

# Try direct query with Jerusalem filter
params = {
    "where": "SEMEL_YISH = 3000 OR YISHUV = '3000' OR YISHUV_NAME LIKE '%ירושלים%'",
    "outFields": "*",
    "returnGeometry": "false",
    "resultRecordCount": 5,
    "f": "json"
}

for base_url in [
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services/Statistical_Areas_2022/FeatureServer/0/query",
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services/CBS_Statistical_Areas_2022/FeatureServer/0/query",
]:
    try:
        r = requests.get(base_url, params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, 
                        headers=HEADERS, timeout=20)
        d = r.json()
        if "count" in d:
            print(f"  Found at {base_url[:80]}: {d['count']} features")
            # Get fields
            info_r = requests.get(base_url.replace("/query", ""), 
                                  params={"f": "json"}, headers=HEADERS, timeout=20)
            info_d = info_r.json()
            if "fields" in info_d:
                print("  Fields:", [f['name'] for f in info_d['fields']])
    except Exception as e:
        print(f"  Error at {base_url[:60]}: {e}")

# ─── Get the actual CBS stat areas GeoJSON ────────────────────────────────────
print("\n" + "=" * 65)
print("Downloading CBS Statistical Areas GeoJSON")
print("=" * 65)

# Use the ArcGIS Online item API to get the service URL
item_url = "https://www.arcgis.com/sharing/rest/content/items/IsraelData::statistical-areas-2022"
# The correct approach: use the known ArcGIS REST endpoint
# From the browser: hub.arcgis.com/datasets/IsraelData::statistical-areas-2022/about
# The actual data is usually at the ArcGIS Hub OGC endpoint

geojson_url = (
    "https://hub.arcgis.com/api/download/v1/items/cab47f8b9bbf4474accad87b22b3d4bf"
    "/geojson?redirect=false&where=SEMEL_YISH+%3D+3000&outSR=4326"
)

# Simpler: try direct ArcGIS REST - the dataset is from IsraelData organization
# Looking at page source from earlier: statistical areas 2022
STAT_ENDPOINT = (
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services"
    "/CBS_2022_Stat_Areas/FeatureServer/0/query"
)

for url in [
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services/CBS_2022_Stat_Areas/FeatureServer/0",
    "https://services3.arcgis.com/p3A2DfBNXJH1hSUL/arcgis/rest/services/Statistical_Areas_2022/FeatureServer/0",
    "https://services.arcgis.com/IYUfZFmrlf94i3k0/arcgis/rest/services/StatAreas/FeatureServer/0",
    "https://services.arcgis.com/IYUfZFmrlf94i3k0/arcgis/rest/services/StatisticalNeighborhoods/FeatureServer/0",
]:
    try:
        r = requests.get(url, params={"f": "json"}, headers=HEADERS, timeout=20)
        d = r.json()
        if "type" in d and d.get("type") == "Feature Layer":
            print(f"  ✓ Found layer at: {url}")
            fields = [f['name'] for f in d.get('fields', [])]
            print(f"    Fields: {fields}")
            count_r = requests.get(url + "/query", 
                                   params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
                                   headers=HEADERS, timeout=20)
            count_d = count_r.json()
            print(f"    Count: {count_d.get('count', '?')}")
        elif "error" in d:
            print(f"  Error at {url[-50:]}: {d['error'].get('message', '')[:100]}")
    except Exception as e:
        print(f"  Exception at {url[-50:]}: {e}")

print("\n" + "=" * 65)
print("Trying CBS direct download approach")
print("=" * 65)

# CBS publishes statistical geographic data on their website
# Try getting the GeoJSON of stat neighborhoods from ArcGIS Online directly
ARCGIS_QUERY = (
    "https://www.arcgis.com/sharing/rest/search"
    "?q=statistical+neighborhoods+2022+israel+CBS"
    "&num=5&f=json"
)
try:
    r = requests.get(ARCGIS_QUERY, headers=HEADERS, timeout=30)
    data = r.json()
    if "results" in data:
        for item in data["results"][:5]:
            print(f"  Item: {item.get('title')} | ID: {item.get('id')} | type: {item.get('type')}")
            print(f"       URL: {item.get('url', 'N/A')[:100]}")
except Exception as e:
    print(f"  Error: {e}")
