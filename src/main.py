import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://books.toscrape.com/"

HEADERS = {
    "User-Agent": "https://github.com/shiirotech/polite_scraper"
}


def fetch(url: str, headers: dict[str, str], cache_file: Path) -> None:
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


def find_book_links(html: BeautifulSoup, page_url: str) -> list[str]:
    book_links = []

    for link in html.select("article.product_pod h3 a"):
        href = link.get("href")
        absolute_url = urljoin(page_url, href)
        book_links.append(absolute_url)

    return book_links


def find_next_url(html: BeautifulSoup, page_url: str) -> str | None:
    next_link = html.select_one("li.next a")

    if next_link is None:
        return None
    
    href = next_link.get("href")
    next_url = urljoin(page_url, href)

    return next_url


if __name__ == "__main__":
    pages_processed = 0
    page_url = URL
    book_links = []

    while pages_processed < 3:
        cache_file = Path(f"cache/catalogue-page-{pages_processed + 1}.html")

        fetch(page_url, HEADERS, cache_file)

        parsed = parse(cache_file)

        book_links += find_book_links(parsed, page_url)

        page_url = find_next_url(parsed, page_url)
        
        if page_url is None:
            break

        pages_processed += 1

    print(f"catalogue_pages={pages_processed}")
    print(f"discovered={len(book_links)}")
    print(f"unique_urls={len(set(book_links))}")