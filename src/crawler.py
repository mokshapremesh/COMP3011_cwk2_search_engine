import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://quotes.toscrape.com"
POLITENESS_WINDOW = 6

def get_page(url: str) -> str:
    """Fetch raw HTML from a URL."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text

def get_links(html: str, base_url: str) -> set:
    """Extract all internal links from a page."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url.rstrip("/"))
    return links

def extract_text(html: str) -> str:
    """Extract visible text from a page."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def crawl(base_url: str = BASE_URL) -> dict:
    """
    Crawl all pages of a website.
    Returns a dict of {url: page_text}.
    """
    visited = set()
    to_visit = [base_url.rstrip("/")]
    pages = {}

    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue

        try:
            print(f"Crawling: {url}")
            html = get_page(url)
            text = extract_text(html)
            pages[url] = text
            visited.add(url)

            new_links = get_links(html, base_url)
            to_visit.extend(new_links - visited)

            time.sleep(POLITENESS_WINDOW)

        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            visited.add(url)

    return pages