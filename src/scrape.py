import urllib.request
import urllib.parse
import os

BASE = os.path.dirname(os.path.abspath(__file__))

URLS = [
    "https://es.wikipedia.org/wiki/XV_legislatura_de_España",
    "https://es.wikipedia.org/wiki/Tercer_Gobierno_Sánchez"
]

API_BASE = "https://r.jina.ai/"
OUTPUT_DIR = os.path.join(BASE, "..", "data")

def fetch_markdown(url):
    print(f"Fetching: {url}")
    
    # Parse url to properly encode characters like ñ, á
    parsed_url = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed_url.path)
    safe_url = urllib.parse.urlunparse(
        (parsed_url.scheme, parsed_url.netloc, encoded_path, 
         parsed_url.params, parsed_url.query, parsed_url.fragment)
    )
    
    req = urllib.request.Request(API_BASE + safe_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for url in URLS:
        md_content = fetch_markdown(url)
        
        # Create filename from URL
        filename = url.split('/')[-1] + ".md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Saved: {filepath}")

if __name__ == "__main__":
    main()
