import requests
import os

def download_file(url, filename):
    print(f"Downloading {url} to {filename}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=60, verify=False)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# URLs
urls = {
    "addresses.csv": "https://data.gov.il/dataset/3fb0a6b3-60ad-4ca4-924a-ec051c039328/resource/f399ef3d-de3b-48c0-b962-d99f0ce0804b/download/israel-addresses.csv",
    "census_2022.xlsx": "https://www.cbs.gov.il/he/publications/census2022pub/%D7%9E%D7%A4%D7%A7%D7%93-2022.xlsx",
    "jerusalem_neighborhoods.geojson": "https://services.arcgis.com/IYUfZFmrlf94i3k0/arcgis/rest/services/Neighborhoods/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson"
}

if __name__ == "__main__":
    for filename, url in urls.items():
        download_file(url, filename)
