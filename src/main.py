import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pydantic import BaseModel, ValidationError
from datetime import datetime, timezone
from time import sleep


class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None
    source_page: str
    fetched_at: datetime


class Error(BaseModel):
    error_detail: str
    book_url: str
    book_number: int


class Report(BaseModel):
    start_time: datetime
    duration: float
    pages_fetched: int
    cache_hits: int
    valid_records: int
    invalid_records: int
    failed_pages: int


def get_time() -> datetime:
    return datetime.now(timezone.utc)


def fetch(url: str, headers: dict[str, str], cache_file: Path) -> tuple[bool, datetime]:
    if cache_file.exists():
        metadata_file = cache_file.with_suffix(".json")
        fetched_at = datetime.fromisoformat(
            json.loads(metadata_file.read_text(encoding="utf-8"))["fetched_at"]
        )

        html = cache_file.read_bytes()

        print("CACHE HIT")
        print(f"Size of the file: {len(html)} bytes")

        return (False, fetched_at)

    else:
        try:
            response = requests.get(url, headers=headers, timeout=5)

        except requests.Timeout:
            sleep(5)
            response = requests.get(url, headers=headers, timeout=5)

        else:
            if 500 <= response.status_code < 600:
                sleep(5)
                response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            response.raise_for_status()

        fetched_at = get_time()

        html = response.content

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(html)

        metadata_file = cache_file.with_suffix(".json")
        metadata_file.write_text(
            json.dumps({"fetched_at": fetched_at.isoformat()}),
            encoding="utf-8"
        )

        print("FETCH")
        print(f"Size of the file: {len(html)} bytes")

        return (True, fetched_at)


def parse(cache_file: Path) -> BeautifulSoup:
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        return soup
    
    else:
        raise FileNotFoundError("File does not exist")


def find_book_links(html: BeautifulSoup, page_url: str) -> dict[str, str]:
    book_links = {}

    for link in html.select("article.product_pod h3 a"):
        href = link.get("href")
        absolute_url = urljoin(page_url, href)
        book_links[absolute_url] = page_url

    return book_links


def find_next_url(html: BeautifulSoup, page_url: str) -> str | None:
    next_link = html.select_one("li.next a")

    if next_link is None:
        return None
    
    href = next_link.get("href")
    next_url = urljoin(page_url, href)

    return next_url


def extract_data(html: BeautifulSoup, fetched_at: datetime, abs_url: str, source_url: str) -> Book:
    # Getting title as text
    title = html.select_one("h1").get_text(strip=True)

    # Getting product url as text
    product_url = abs_url

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

    # Getting price as float (in GBP)
    price_gbp = float(price_text.strip("£"))

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
    source_page = source_url

    # Getting fetched_at as datetime (already gotten from fetch())

    book = Book(
        title=title,
        product_url=product_url,
        price_text=price_text,
        price_gbp=price_gbp,
        availability_text=availability_text,
        rating_text=rating_text,
        description=description_text,
        source_page=source_page,
        fetched_at=fetched_at
    )

    return book


def write_json(iterable: list[BaseModel], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [record.model_dump(mode="json") for record in iterable]

    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def write_run_report_json(data: Report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = data.model_dump(mode="json")

    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )


URL = "https://books.toscrape.com/"
HEADERS = { "User-Agent": "https://github.com/shiirotech/polite_scraper" }
OUTPUT_SUCCESS = Path("output/books.json")
OUTPUT_FAIL = Path("output/errors.json")
OUTPUT_REPORT = Path("output/run-report.json")


if __name__ == "__main__":
    # === Getting first 3 pages of books ===
    pages_processed = 0
    pages_fetched = 0
    pages_from_cache = 0
    failed_pages = 0

    page_url = URL
    book_links = {}
    start_time = get_time()

    while pages_processed < 3:
        cache_file = Path(f"cache/catalogue-page-{pages_processed + 1}.html")

        try:
            fetched, fetched_at = fetch(page_url, HEADERS, cache_file)

        except (requests.exceptions.HTTPError, requests.Timeout):
            failed_pages += 1

        else:
            if fetched:
                sleep(1)
                pages_fetched += 1
            else:
                pages_from_cache += 1

            parsed = parse(cache_file)

            book_links.update(find_book_links(parsed, page_url))

            page_url = find_next_url(parsed, page_url)

            if page_url is None:
                break

        pages_processed += 1

    print(f"\ncatalogue_pages={pages_processed}")
    print(f"discovered={len(book_links)}\n")
    

    # === Getting 60 book records ===
    book_number = 1
    book_records = []
    errors = []
    
    for abs_url, source_url in book_links.items():
        cache_file = Path(f"cache/book-{book_number}.html")

        try:
            fetched, fetched_at = fetch(abs_url, HEADERS, cache_file)
            
        except (requests.exceptions.HTTPError, requests.Timeout):
            failed_pages += 1

        else:
            if fetched:
                sleep(1)
                pages_fetched += 1
            else:
                pages_from_cache += 1

            parsed = parse(cache_file)

            try:
                record = extract_data(parsed, fetched_at, abs_url, source_url)

            except ValidationError as e:
                errors.append(
                    Error(error_detail=str(e),
                        book_url=abs_url,
                        book_number=book_number)
                )
            else:
                book_records.append(record)

        book_number += 1
            
    write_json(book_records, OUTPUT_SUCCESS)
    write_json(errors, OUTPUT_FAIL)

    end_time = get_time()

    print(f"\ndetail_pages={len(book_records) + len(errors)}")


    # === Generate report ===
    report = Report(start_time=start_time,
                    duration=(end_time - start_time).total_seconds(),
                    pages_fetched=pages_fetched,
                    cache_hits=pages_from_cache,
                    valid_records=len(book_records),
                    invalid_records=len(errors),
                    failed_pages=failed_pages)

    write_run_report_json(report, OUTPUT_REPORT)