
import sys
import os
import json

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

import geopandas as gpd
import pandas as pd

# Check geojson
print("=== jerusalem_neighborhoods.geojson ===")
with open('jerusalem_neighborhoods.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

gdf = gpd.GeoDataFrame.from_features(data['features'])
print('Columns:', gdf.columns.tolist())
print('Shape:', gdf.shape)
print('Sample SCHN_NAME:', gdf['SCHN_NAME'].dropna().head(10).tolist())
print('Sample CODE:', gdf['CODE'].dropna().head(10).tolist())
print('East_West sample:', gdf['East_West'].dropna().head(10).tolist())
print()

# Check addresses.csv (it may be HTML / failed download)
print("=== addresses.csv (first 3 lines raw) ===")
with open('addresses.csv', 'r', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f):
        if i >= 3:
            break
        print(line[:200])

# Check jerusalem_streets_2022.xlsx
print("\n=== jerusalem_streets_2022.xlsx ===")
try:
    xls = pd.ExcelFile('jerusalem_streets_2022.xlsx')
    print('Sheets:', xls.sheet_names)
    for sheet in xls.sheet_names:
        df = pd.read_excel('jerusalem_streets_2022.xlsx', sheet_name=sheet, nrows=10)
        print(f'--- Sheet: {sheet} ---')
        print('Columns:', df.columns.tolist())
        print(df.head(5).to_string())
        print()
except Exception as e:
    print(f"Error: {e}")
