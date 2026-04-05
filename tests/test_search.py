import pytest
import json
import os
from src.search import save_index, load_index, print_word, find_pages

SAMPLE_INDEX = {
    "life": {
        "https://quotes.toscrape.com": {
            "frequency": 3,
            "positions": [1, 10, 20],
            "tf": 0.03,
            "tfidf": 0.12
        },
        "https://quotes.toscrape.com/page/2": {
            "frequency": 1,
            "positions": [5],
            "tf": 0.01,
            "tfidf": 0.04
        }
    },
    "good": {
        "https://quotes.toscrape.com": {
            "frequency": 2,
            "positions": [3, 15],
            "tf": 0.02,
            "tfidf": 0.08
        }
    }
}

def test_save_and_load_index(tmp_path):
    path = str(tmp_path / "test_index.json")
    save_index(SAMPLE_INDEX, path)
    loaded = load_index(path)
    assert loaded == SAMPLE_INDEX

def test_load_index_missing_file():
    with pytest.raises(FileNotFoundError):
        load_index("data/nonexistent_index.json")

def test_find_single_word():
    results = find_pages(SAMPLE_INDEX, "life")
    urls = [r[0] for r in results]
    assert "https://quotes.toscrape.com" in urls

def test_find_multi_word():
    results = find_pages(SAMPLE_INDEX, "life good")
    urls = [r[0] for r in results]
    assert "https://quotes.toscrape.com" in urls
    assert "https://quotes.toscrape.com/page/2" not in urls

def test_find_word_not_in_index():
    results = find_pages(SAMPLE_INDEX, "zzznotaword")
    assert results == []

def test_find_empty_query():
    results = find_pages(SAMPLE_INDEX, "")
    assert results == []

def test_find_results_ranked_by_tfidf():
    results = find_pages(SAMPLE_INDEX, "life")
    scores = [r[1] for r in results]
    assert scores == sorted(scores, reverse=True)

def test_print_word_not_in_index(capsys):
    print_word(SAMPLE_INDEX, "zzznotaword")
    captured = capsys.readouterr()
    assert "not found" in captured.out

def test_print_word_found(capsys):
    print_word(SAMPLE_INDEX, "life")
    captured = capsys.readouterr()
    assert "life" in captured.out
    assert "frequency" in captured.out