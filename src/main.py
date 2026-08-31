import requests
from pathlib import Path

URL = "https://books.toscrape.com/"

CACHE_FILE = Path("cache/catalogue-page-1.html")

HEADERS = {
    "User-Agent": "https://github.com/shiirotech/polite_scraper"
}

if CACHE_FILE.exists():
    html = CACHE_FILE.read_text(encoding="utf-8")

    print("CACHE HIT")
    print(f"Size of the file: {len(html.encode("utf-8"))} bytes")

else:
    response = requests.get(URL, headers=HEADERS, timeout=5)

    if response.status_code != 200:
        response.raise_for_status()

    html = response.text

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(html, encoding="utf-8")

    print("FETCH")
    print(f"Size of the file: {len(response.content)} bytes")