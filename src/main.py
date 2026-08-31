import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pydantic import BaseModel
from datetime import datetime, timezone
from time import sleep


class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: datetime


def get_time() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def fetch(url: str, headers: dict[str, str], cache_file: Path) -> bool:
    if cache_file.exists():
        html = cache_file.read_bytes()

        print("CACHE HIT")
        print(f"Size of the file: {len(html)} bytes")

        return False

    else:
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            response.raise_for_status()

        html = response.content

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(html)

        print("FETCH")
        print(f"Size of the file: {len(html)} bytes")

        return True


def parse(cache_file: Path) -> BeautifulSoup:
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        return soup
    
    else:
        raise FileNotFoundError("File does not exist")


def find_book_links(html: BeautifulSoup, page_url: str) -> list[tuple[str, str]]:
    book_links = []

    for link in html.select("article.product_pod h3 a"):
        href = link.get("href")
        absolute_url = urljoin(page_url, href)
        book_links.append((absolute_url, page_url))

    return book_links


def find_next_url(html: BeautifulSoup, page_url: str) -> str | None:
    next_link = html.select_one("li.next a")

    if next_link is None:
        return None
    
    href = next_link.get("href")
    next_url = urljoin(page_url, href)

    return next_url


def extract_data(html: BeautifulSoup, link: tuple[str, str]) -> Book:
    # Getting title as text
    title = html.select_one("h1").get_text(strip=True)

    # Getting product url as text
    product_url = link[0]

    # Getting price and availability as text
    table = html.select_one("table.table-striped")
    for row in table.select("tr"):
        label = row.select_one("th")

        if label and label.get_text(strip=True) == "Price (excl. tax)":
            price = row.select_one("td")
            price_text = price.get_text(strip=True)

        elif label and label.get_text(strip=True) == "Availability":
            availability = row.select_one("td")
            availability_text = availability.get_text(strip=True)
            break

    # Getting rating as text
    rating = html.select_one("p.star-rating")
    rating_classes = rating.get("class")
    rating_text = rating_classes[1]

    # Getting description as text
    description_text = None
    description_header = html.select_one("#product_description")

    if description_header is not None:
        description = description_header.find_next("p")
        if description is not None:
            description_text = description.get_text(strip=True)

    # Getting source page as text
    source_page = link[1]

    # Getting fetched_at as datetime
    fetched_at = get_time()

    book = Book(
        title=title,
        product_url=product_url,
        price_text=price_text,
        availability_text=availability_text,
        rating_text=rating_text,
        description=description_text,
        source_page=source_page,
        fetched_at=fetched_at
    )

    return book


URL = "https://books.toscrape.com/"
HEADERS = { "User-Agent": "https://github.com/shiirotech/polite_scraper" }


if __name__ == "__main__":
    # === Getting first 3 pages of books ===
    pages_processed = 0
    page_url = URL
    book_links = []

    while pages_processed < 3:
        cache_file = Path(f"cache/catalogue-page-{pages_processed + 1}.html")

        fetched = fetch(page_url, HEADERS, cache_file)

        parsed = parse(cache_file)

        book_links += find_book_links(parsed, page_url)

        page_url = find_next_url(parsed, page_url)

        pages_processed += 1

        if page_url is None:
            break

        if fetched:
            sleep(1)

    print(f"\ncatalogue_pages={pages_processed}")
    print(f"discovered={len(book_links)}")
    print(f"unique_urls={len(set(link[0] for link in book_links))}\n")


    # === Getting 60 book records ===
    book_number = 1
    book_records = []
    
    for link in book_links:
        cache_file = Path(f"cache/book-{book_number}.html")

        fetched = fetch(link[0], HEADERS, cache_file)

        parsed = parse(cache_file)

        record = extract_data(parsed, link)

        book_records.append(record)

        book_number += 1

        if fetched:
            sleep(1)

    print("\n" + book_records[5].model_dump_json(indent=2))
    print(f"detail_pages={len(book_records)}")

    # notes for future: make fetched_at to be updated only during the initial fetch