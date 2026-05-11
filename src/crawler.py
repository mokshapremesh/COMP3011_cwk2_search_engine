"""
crawler.py — Web crawler for quotes.toscrape.com

Performs a breadth-first crawl of the target website, extracting
visible text from each page and respecting a politeness delay between
requests so the server is not overloaded.
"""

import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# The website we are crawling (used as the default start URL)
BASE_URL = "https://quotes.toscrape.com"

# Minimum seconds to wait between successive HTTP requests.
# Required by the assignment brief to be at least 6 seconds.
POLITENESS_WINDOW = 6


def get_page(url: str) -> str:
    """
    Fetch the raw HTML content of a single URL.

    Uses a 10-second timeout so the crawler does not hang indefinitely
    on unresponsive servers.  raise_for_status() converts HTTP error
    codes (4xx, 5xx) into exceptions, which are caught by the caller.

    Args:
        url: The fully-qualified URL to fetch.

    Returns:
        The raw HTML as a string.

    Raises:
        requests.RequestException: On any network or HTTP error.
    """
    response = requests.get(url, timeout=10)

    # Raise an HTTPError for 4xx/5xx responses (e.g. 404, 500)
    response.raise_for_status()

    return response.text


def get_links(html: str, base_url: str) -> set[str]:
    """
    Extract all internal hyperlinks from a page's HTML.

    'Internal' means the link's domain (netloc) matches the domain of
    base_url.  External links (e.g. social media, third-party sites)
    are discarded so the crawler stays within the target website.

    Trailing slashes are stripped from each URL so that
    'https://example.com/page/' and 'https://example.com/page'
    are treated as the same URL and not crawled twice.

    Args:
        html:     Raw HTML string of the page.
        base_url: The root URL of the site — used to resolve relative
                  hrefs and to filter out external links.

    Returns:
        A set of normalised, absolute internal URLs.
    """
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()

    # The domain of the site we are allowed to crawl
    allowed_domain = urlparse(base_url).netloc

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # urljoin handles both relative paths ("/page/2/") and
        # absolute URLs ("https://…") correctly
        full_url = urljoin(base_url, href)

        # Only keep links that stay on the same domain
        if urlparse(full_url).netloc == allowed_domain:
            # Normalise by removing trailing slash to avoid duplicate crawls
            links.add(full_url.rstrip("/"))

    return links


def extract_text(html: str) -> str:
    """
    Extract all visible text from a page's HTML.

    BeautifulSoup's get_text() strips HTML tags and returns the raw
    text content.  A space separator prevents words from different
    tags being joined without whitespace (e.g. '</p><p>' → ' ').

    Args:
        html: Raw HTML string of the page.

    Returns:
        A single string of visible text with leading/trailing
        whitespace removed.
    """
    soup = BeautifulSoup(html, "html.parser")

    # separator=" " ensures adjacent tags don't merge their text;
    # strip=True removes surrounding whitespace from each text node
    return soup.get_text(separator=" ", strip=True)


def crawl(base_url: str = BASE_URL) -> dict[str, str]:
    """
    Crawl the entire website using breadth-first search (BFS).

    BFS is chosen over DFS because it crawls pages level by level,
    meaning shallow (higher-value) pages are indexed first.  If the
    crawl is interrupted, the most important pages will already be
    in the index.

    A deque is used as the queue instead of a plain list because
    deque.popleft() is O(1), whereas list.pop(0) is O(n) — important
    for large sites with many pages.

    The politeness window (time.sleep) is applied after every
    successful request to avoid overwhelming the server with rapid
    repeated requests.

    Args:
        base_url: The starting URL for the crawl.

    Returns:
        A dictionary mapping each visited URL to its extracted text:
        { url: page_text, … }
    """
    # Set of URLs already processed — prevents re-visiting pages
    visited: set[str] = set()

    # BFS queue, initialised with the start URL (trailing slash removed)
    to_visit: deque[str] = deque([base_url.rstrip("/")])

    # Accumulates {url: text} for every successfully crawled page
    pages: dict[str, str] = {}

    while to_visit:
        # Take the next URL from the front of the queue (FIFO = BFS)
        url = to_visit.popleft()

        # Skip URLs we have already crawled or attempted
        if url in visited:
            continue

        try:
            print(f"Crawling: {url}")
            html = get_page(url)

            # Extract visible text and store it indexed by URL
            text = extract_text(html)
            pages[url] = text

            # Mark this URL as done before discovering its links,
            # so links back to the current page don't re-queue it
            visited.add(url)

            # Discover outgoing links and add any not yet queued
            new_links = get_links(html, base_url)
            to_visit.extend(new_links - visited)

            # Respect the 6-second politeness window between requests
            time.sleep(POLITENESS_WINDOW)

        except requests.RequestException as e:
            # Log the error but continue crawling the remaining pages;
            # mark the URL as visited so we don't retry it
            print(f"Error fetching {url}: {e}")
            visited.add(url)

    return pages
