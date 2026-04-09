import pytest
import time
from unittest.mock import patch, Mock, call
from src.crawler import get_links, extract_text, get_page, crawl

SAMPLE_HTML = """
<html>
  <body>
    <a href="/page/2/">Next</a>
    <a href="/author/Einstein/">Einstein</a>
    <a href="https://external.com">External</a>
    <p>The only way to do great work is to love what you do.</p>
  </body>
</html>
"""

HTML_NO_LINKS = """
<html><body><p>No links here at all.</p></body></html>
"""

def test_get_links_internal_only():
    links = get_links(SAMPLE_HTML, "https://quotes.toscrape.com")
    assert "https://quotes.toscrape.com/page/2" in links
    assert "https://external.com" not in links

def test_get_links_returns_set():
    links = get_links(SAMPLE_HTML, "https://quotes.toscrape.com")
    assert isinstance(links, set)

def test_get_links_no_links():
    links = get_links(HTML_NO_LINKS, "https://quotes.toscrape.com")
    assert links == set()

def test_get_links_empty_html():
    links = get_links("", "https://quotes.toscrape.com")
    assert links == set()

def test_extract_text_returns_string():
    text = extract_text(SAMPLE_HTML)
    assert isinstance(text, str)
    assert "love" in text.lower()

def test_extract_text_empty_html():
    text = extract_text("")
    assert isinstance(text, str)

def test_extract_text_strips_tags():
    text = extract_text("<p>Hello <b>world</b></p>")
    assert "<b>" not in text
    assert "Hello" in text

@patch("src.crawler.requests.get")
def test_get_page_success(mock_get):
    mock_get.return_value = Mock(status_code=200, text="<html>hello</html>")
    mock_get.return_value.raise_for_status = Mock()
    result = get_page("https://quotes.toscrape.com")
    assert result == "<html>hello</html>"

@patch("src.crawler.requests.get")
def test_get_page_handles_error(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("Connection failed")
    with pytest.raises(requests.RequestException):
        get_page("https://quotes.toscrape.com")

@patch("src.crawler.time.sleep")
@patch("src.crawler.get_links")
@patch("src.crawler.get_page")
def test_crawl_visits_pages(mock_get_page, mock_get_links, mock_sleep):
    mock_get_page.return_value = "<html>test</html>"
    mock_get_links.return_value = set()
    pages = crawl("https://quotes.toscrape.com")
    assert "https://quotes.toscrape.com" in pages
    mock_sleep.assert_called()

@patch("src.crawler.time.sleep")
@patch("src.crawler.get_links")
@patch("src.crawler.get_page")
def test_crawl_respects_politeness(mock_get_page, mock_get_links, mock_sleep):
    mock_get_page.return_value = "<html>test</html>"
    mock_get_links.return_value = set()
    crawl("https://quotes.toscrape.com")
    mock_sleep.assert_called_with(6)

@patch("src.crawler.time.sleep")
@patch("src.crawler.get_links")
@patch("src.crawler.get_page")
def test_crawl_handles_network_error(mock_get_page, mock_get_links, mock_sleep):
    import requests
    mock_get_page.side_effect = requests.RequestException("timeout")
    mock_get_links.return_value = set()
    pages = crawl("https://quotes.toscrape.com")
    assert pages == {}

@patch("src.crawler.time.sleep")
@patch("src.crawler.get_links")
@patch("src.crawler.get_page")
def test_crawl_does_not_revisit(mock_get_page, mock_get_links, mock_sleep):
    mock_get_page.return_value = "<html>test</html>"
    mock_get_links.return_value = {"https://quotes.toscrape.com"}
    pages = crawl("https://quotes.toscrape.com")
    assert mock_get_page.call_count == 1