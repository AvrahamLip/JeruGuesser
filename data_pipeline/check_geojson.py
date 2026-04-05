import geopandas as gpd
import json

def check_geojson():
    print("--- Jerusalem Neighborhoods GeoJSON ---")
    try:
        with open("jerusalem_neighborhoods.geojson", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        gdf = gpd.GeoDataFrame.from_features(data['features'])
        print(f"Columns: {gdf.columns.tolist()}")
        print(f"Sample Names: {gdf['SCHN_NAME'].head().tolist()}")
        print(f"CRS: {gdf.crs}") # Features often don't have CRS in the JSON structure itself but the GeoJSON might have it
        
        # Check if it has centroids or polygons
        print(f"Geometry type: {gdf.geometry.iloc[0].geom_type}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_geojson()
