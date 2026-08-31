import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://books.toscrape.com/"

CACHE_FILE = Path("cache/catalogue-page-1.html")

HEADERS = {
    "User-Agent": "https://github.com/shiirotech/polite_scraper"
}


def fetch(url: str, headers: dict, cache_file: Path) -> None:
    if cache_file.exists():
        html = cache_file.read_bytes()

        print("CACHE HIT")
        print(f"Size of the file: {len(html)} bytes")

    else:
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            response.raise_for_status()

        html = response.content

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(html)

        print("FETCH")
        print(f"Size of the file: {len(html)} bytes")


def parse(cache_file: Path) -> BeautifulSoup:
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        return soup
    
    else:
        raise FileNotFoundError("File does not exist")


if __name__ == "__main__":
    fetch(URL, HEADERS, CACHE_FILE)
    parsed = parse(CACHE_FILE)

    book_links = set()
    for link in parsed.select("article.product_pod h3 a"):
        href = link.get("href")
        absolute_url = urljoin(URL, href)
        book_links.add(absolute_url)

    for link in book_links:
        print(link)