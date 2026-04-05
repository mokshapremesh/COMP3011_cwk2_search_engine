import pytest
from unittest.mock import patch, Mock
from src.crawler import get_links, extract_text, get_page

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

def test_get_links_internal_only():
    links = get_links(SAMPLE_HTML, "https://quotes.toscrape.com")
    assert "https://quotes.toscrape.com/page/2" in links
    assert "https://external.com" not in links

def test_get_links_returns_set():
    links = get_links(SAMPLE_HTML, "https://quotes.toscrape.com")
    assert isinstance(links, set)

def test_extract_text_returns_string():
    text = extract_text(SAMPLE_HTML)
    assert isinstance(text, str)
    assert "love" in text.lower()

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