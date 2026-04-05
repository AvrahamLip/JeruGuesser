import pandas as pd
import geopandas as gpd

def inspect_files():
    print("--- Inspecting addresses.csv ---")
    try:
        # National address file might be large, just read first few rows
        df_addr = pd.read_csv("addresses.csv", nrows=5, encoding='utf-8')
        print(df_addr.columns.tolist())
        print(df_addr.head())
    except Exception as e:
        print(f"Error reading addresses.csv: {e}")

    print("\n--- Inspecting census_2022.xlsx ---")
    try:
        # Peek at columns of the first few sheets
        xls = pd.ExcelFile("census_2022.xlsx")
        for sheet_name in xls.sheet_names[:2]:
            print(f"Sheet: {sheet_name}")
            df_census = pd.read_excel("census_2022.xlsx", sheet_name=sheet_name, nrows=5)
            print(df_census.columns.tolist())
            print(df_census.head())
    except Exception as e:
        print(f"Error reading census_2022.xlsx: {e}")

    print("\n--- Inspecting jerusalem_neighborhoods.geojson ---")
    try:
        gdf_muni = gpd.read_file("jerusalem_neighborhoods.geojson")
        print(gdf_muni.columns.tolist())
        print(gdf_muni.head(3))
        print(f"CRS: {gdf_muni.crs}")
    except Exception as e:
        print(f"Error reading jerusalem_neighborhoods.geojson: {e}")

if __name__ == "__main__":
    inspect_files()
