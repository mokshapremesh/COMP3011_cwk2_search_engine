import pytest
from src.indexer import tokenize, build_index, add_tfidf

SAMPLE_PAGES = {
    "https://quotes.toscrape.com": "The world is a beautiful place to live in",
    "https://quotes.toscrape.com/page/2": "Live and let live is a good motto",
    "https://quotes.toscrape.com/page/3": "Beauty is in the eye of the beholder"
}

def test_tokenize_lowercase():
    words = tokenize("Hello World")
    assert "hello" in words
    assert "world" in words
    assert "Hello" not in words

def test_tokenize_removes_punctuation():
    words = tokenize("it's a beautiful day!")
    assert "day" in words
    assert "!" not in words

def test_tokenize_returns_list():
    result = tokenize("hello world")
    assert isinstance(result, list)

def test_build_index_structure():
    index = build_index(SAMPLE_PAGES)
    assert isinstance(index, dict)
    assert "live" in index
    assert "https://quotes.toscrape.com" in index["live"]

def test_build_index_frequency():
    index = build_index(SAMPLE_PAGES)
    # "live" appears twice in first page
    freq = index["live"]["https://quotes.toscrape.com"]["frequency"]
    assert freq >= 1

def test_build_index_positions():
    index = build_index(SAMPLE_PAGES)
    positions = index["live"]["https://quotes.toscrape.com"]["positions"]
    assert isinstance(positions, list)
    assert len(positions) >= 1

def test_build_index_tf():
    index = build_index(SAMPLE_PAGES)
    tf = index["live"]["https://quotes.toscrape.com"]["tf"]
    assert 0.0 < tf <= 1.0

def test_add_tfidf():
    index = build_index(SAMPLE_PAGES)
    index = add_tfidf(index, len(SAMPLE_PAGES))
    tf_idf = index["live"]["https://quotes.toscrape.com"]["tfidf"]
    assert isinstance(tf_idf, float)

def test_word_not_in_index():
    index = build_index(SAMPLE_PAGES)
    assert "zzznonsenseword" not in index