"""
Add CBS Statistical Neighborhoods to Jerusalem Streets Table
============================================================
Uses:
1. CBS ArcGIS: statistical_areas_2022 (JcXY3lLZni6BK4El org)
   URL: https://services8.arcgis.com/JcXY3lLZni6BK4El/arcgis/rest/services/statistical_areas_2022/FeatureServer
2. CBS Excel: רחובות עיקריים ושכונות לאס 2022.xlsx
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
import io

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

CBS_STAT_AREAS_URL = (
    "https://services8.arcgis.com/JcXY3lLZni6BK4El/arcgis/rest/services"
    "/statistical_areas_2022/FeatureServer/0"
)

# ─── Step 1: Inspect CBS Statistical Areas layer ───────────────────────────────
print("=" * 65)
print("STEP 1: Inspecting CBS Statistical Areas (2022)")
print("=" * 65)

try:
    r = requests.get(CBS_STAT_AREAS_URL, params={"f": "json"}, headers=HEADERS, timeout=30)
    info = r.json()
    print(f"  Layer name: {info.get('name')}")
    fields = [f['name'] for f in info.get('fields', [])]
    print(f"  Fields: {fields}")
    
    # Count
    r2 = requests.get(CBS_STAT_AREAS_URL + "/query", 
                      params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
                      headers=HEADERS, timeout=30)
    count_data = r2.json()
    print(f"  Total count: {count_data.get('count', '?')}")
    
    # Sample 1 record for Jerusalem (SEMEL_YISH = 3000)
    r3 = requests.get(CBS_STAT_AREAS_URL + "/query",
                      params={
                          "where": "SEMEL_YISH = 3000",
                          "outFields": "*",
                          "returnGeometry": "false",
                          "resultRecordCount": 3,
                          "f": "json"
                      },
                      headers=HEADERS, timeout=30)
    data3 = r3.json()
    if "features" in data3 and data3["features"]:
        print(f"\n  Sample Jerusalem records:")
        for feat in data3["features"]:
            attrs = feat["attributes"]
            # Show all fields
            for k, v in attrs.items():
                print(f"    {k}: {v}")
            print()
    elif "error" in data3:
        print(f"  Error: {data3['error']}")
        
        # Try different field name
        for yishuv_field in ["SEMEL_YISH", "YISHUV_CODE", "MUNI_NUM", "SAS_CODE1", "YISHUV"]:
            r_test = requests.get(CBS_STAT_AREAS_URL + "/query",
                                  params={
                                      "where": f"{yishuv_field} = 3000",
                                      "outFields": "*",
                                      "returnGeometry": "false",
                                      "resultRecordCount": 1,
                                      "f": "json"
                                  },
                                  headers=HEADERS, timeout=30)
            d_test = r_test.json()
            if "features" in d_test and d_test["features"]:
                print(f"\n  ✓ Field name is: {yishuv_field}")
                for k, v in d_test["features"][0]["attributes"].items():
                    print(f"    {k}: {v}")
                break
            elif "error" not in d_test:
                print(f"  Field {yishuv_field}: {d_test}")
except Exception as e:
    print(f"  Exception: {e}")

# ─── Step 2: Check the CBS Excel file (רחובות ושכונות) ────────────────────────
print("\n" + "=" * 65)
print("STEP 2: Downloading CBS Excel - Main Streets & Neighborhoods")
print("=" * 65)

CBS_EXCEL_URL = (
    "https://www.cbs.gov.il/he/mediarelease/doclib/2022/026/"
    "%D7%A8%D7%97%D7%95%D7%91%D7%95%D7%AA%20%D7%A2%D7%99%D7%A7%D7%A8%D7%99%D7%99%D7%9D%20"
    "%D7%95%D7%A9%D7%9B%D7%95%D7%A0%D7%95%D7%AA%20%D7%9C%D7%90%D7%A1%202022.xlsx"
)

try:
    r = requests.get(CBS_EXCEL_URL, headers=HEADERS, timeout=60, verify=False)
    print(f"  Status: {r.status_code}, Content-Type: {r.headers.get('Content-Type')}, Size: {len(r.content)} bytes")
    
    if r.status_code == 200 and len(r.content) > 10000:
        with open("cbs_streets_neighborhoods_2022.xlsx", "wb") as f:
            f.write(r.content)
        print("  ✓ Saved CBS streets+neighborhoods Excel")
        
        # Inspect
        xls = pd.ExcelFile(io.BytesIO(r.content), engine='openpyxl')
        print(f"  Sheets: {xls.sheet_names}")
        for sheet in xls.sheet_names[:3]:
            df = pd.read_excel(io.BytesIO(r.content), sheet_name=sheet, nrows=5, engine='openpyxl')
            print(f"\n  Sheet '{sheet}':")
            print(f"  Columns: {df.columns.tolist()}")
            print(df.head(3).to_string())
    else:
        print(f"  Failed or too small. Response: {r.text[:200]}")
except Exception as e:
    print(f"  Exception: {e}")

# ─── Step 3: Try the CBS stat areas GeoJSON for Jerusalem ─────────────────────
print("\n" + "=" * 65)
print("STEP 3: Downloading CBS Statistical Areas for Jerusalem")
print("=" * 65)

PAGE_SIZE = 1000
all_stat_features = []
offset = 0

# Try with SEMEL_YISH
for yishuv_field in ["SEMEL_YISH", "YISHUV_CODE", "MUNI_NUM", "SAS_CODE", "SHEM_YIS"]:
    test_url = CBS_STAT_AREAS_URL + "/query"
    test_params = {
        "where": f"{yishuv_field} = 3000",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": 2,
        "f": "json"
    }
    try:
        r = requests.get(test_url, params=test_params, headers=HEADERS, timeout=30)
        d = r.json()
        if "features" in d and d["features"] and "error" not in d:
            print(f"  ✓ Jerusalem field found: {yishuv_field}, got {len(d['features'])} features")
            JER_FIELD = yishuv_field
            # Now fetch all Jerusalem stat areas
            while True:
                params = {
                    "where": f"{yishuv_field} = 3000",
                    "outFields": "*",
                    "returnGeometry": "true",
                    "outSR": "4326",
                    "resultRecordCount": PAGE_SIZE,
                    "resultOffset": offset,
                    "f": "json"
                }
                r2 = requests.get(test_url, params=params, headers=HEADERS, timeout=60)
                d2 = r2.json()
                feats = d2.get("features", [])
                all_stat_features.extend(feats)
                print(f"    offset={offset}: got {len(feats)}, total={len(all_stat_features)}")
                if len(feats) < PAGE_SIZE:
                    break
                offset += PAGE_SIZE
                time.sleep(0.3)
            break
        elif "error" in d:
            print(f"  Field {yishuv_field}: error - {d['error'].get('message','')}")
    except Exception as e:
        print(f"  Field {yishuv_field}: {e}")

if all_stat_features:
    print(f"\n  Total stat area features for Jerusalem: {len(all_stat_features)}")
    # Save as GeoJSON
    geojson_out = {
        "type": "FeatureCollection",
        "features": []
    }
    rows_stat = []
    for feat in all_stat_features:
        attrs = feat.get("attributes", {})
        geom = feat.get("geometry")
        rows_stat.append(attrs)
    
    df_stat = pd.DataFrame(rows_stat)
    print(f"  Columns: {df_stat.columns.tolist()}")
    print(df_stat.head(3).to_string())
    df_stat.to_csv("cbs_stat_areas_jerusalem.csv", index=False, encoding='utf-8-sig')
    print("\n  ✓ Saved cbs_stat_areas_jerusalem.csv")
else:
    # Fallback: fetch all without filter (will be large)
    print("\n  Fetching ALL stat areas (no filter)...")
    params = {
        "where": "1=1",
        "outFields": "OBJECTID,SEMEL_YISH,YISHUV_STAT,SAS_CODE1,SHEM_YIS,STAT_AREA,SHKHUNA,SHEH_STAT",
        "returnGeometry": "false",
        "resultRecordCount": 5,
        "f": "json"
    }
    r = requests.get(CBS_STAT_AREAS_URL + "/query", params=params, headers=HEADERS, timeout=30)
    d = r.json()
    if "features" in d:
        print(f"  Sample (first 5):")
        for feat in d["features"]:
            print(f"    {feat['attributes']}")
    else:
        print(f"  Response: {str(d)[:500]}")
