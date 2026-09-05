## This is a Web Scraper

Requesting https://books.toscrape.com/robots.txt resulted in 404 status code.

*No robots file found*

## Target classification

**Website:** https://books.toscrape.com

**Why appropriate:** it is explicitly provided as a sandbox for practising web scraping.

**Scope:** the first 3 catalogue pages.

**Data collected:** book title, price, availability, rating and product URL.

## Lane

**Python web scraping**

The project uses:

* `requests` for HTTP requests
* `BeautifulSoup` for HTML parsing
* `Pydantic` for record validation

## Installation

Create and activate a virtual environment, then install the dependencies.

### Windows

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

## Running

Run the scraper with:

```bash
python scraper.py
```

The scraper produces `books.json`, `errors.json` and `run-report.json`.

## Record schema

Each valid book record contains:

| Field               | Type          | Description                                       |
| ------------------- | ------------- | ------------------------------------------------- |
| `title`             | `str`         | Book title                                        |
| `product_url`       | `str`         | Absolute URL of the product page                  |
| `price_text`        | `str`         | Original price as displayed on the page           |
| `price_gbp`         | `float`       | Price converted to a numeric value                |
| `availability_text` | `str`         | Availability information                          |
| `rating_text`       | `str`         | Rating displayed on the page                      |
| `description`       | `str \| null` | Book description, when available                  |
| `source_page`       | `str`         | Catalogue page from which the book was discovered |
| `fetched_at`        | `datetime`    | Time when the source page was fetched             |

## Politeness

The scraper follows these rules:

* A custom `User-Agent` identifies the scraper and links to this repository.
* A **1-second delay** is used after each actual network request.
* Cached responses do not cause an additional delay.
* Each request has a **5-second timeout**.
* A timed-out request or a `5xx` response is retried **once** after 5 seconds.
* `403` and `404` responses are not retried.
* Successfully fetched catalogue and book pages are cached locally and reused on subsequent runs.

The `cache/` and `output/` directories are excluded from Git because they contain generated files.

## Browser

A browser such as Chrome or Firefox was not needed. The required data is already included in the HTML returned by the server, so the scraper can fetch and parse it directly using `requests` and `BeautifulSoup`. Using browser automation would add unnecessary complexity and resource usage.

## Limitation

The scraper is intentionally limited to the first 3 catalogue pages and is not designed to crawl the entire website.

## Ethics

Use an official API when one exists. Never bypass logins, paywalls or blocks. Collect only the data needed for the task.

## Sample run report

A real `run-report.json` from a final run is included below:

```json
{
  "start_time": "2026-09-05T16:50:27.056947Z",
  "duration": 0.735209,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```