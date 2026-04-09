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

def test_find_case_insensitive():
    results = find_pages(SAMPLE_INDEX, "LIFE")
    assert len(results) > 0

def test_print_word_case_insensitive(capsys):
    print_word(SAMPLE_INDEX, "LIFE")
    captured = capsys.readouterr()
    assert "life" in captured.out

# --- CLI tests ---
from unittest.mock import patch

def test_build_command_calls_crawl():
    with patch("src.main.crawl", return_value={"https://quotes.toscrape.com": "text"}) as mock_crawl:
        with patch("src.main.build_index", return_value={}):
            with patch("src.main.add_tfidf", return_value={}):
                with patch("src.main.save_index"):
                    with patch("builtins.input", side_effect=["build", "quit"]):
                        from src.main import run
                        run()
    mock_crawl.assert_called_once()

def test_load_command_calls_load_index():
    with patch("src.main.load_index", return_value={}) as mock_load:
        with patch("builtins.input", side_effect=["load", "quit"]):
            from src.main import run
            run()
    mock_load.assert_called_once()

def test_unknown_command_prints_error():
    with patch("builtins.input", side_effect=["badcommand", "quit"]):
        with patch("builtins.print") as mock_print:
            from src.main import run
            run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "Unknown command" in printed

def test_empty_input_prints_message():
    with patch("builtins.input", side_effect=["", "quit"]):
        with patch("builtins.print") as mock_print:
            from src.main import run
            run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "Please enter a command" in printed

def test_print_no_argument_prints_usage():
    with patch("src.main.load_index", return_value={"life": {}}):
        with patch("builtins.input", side_effect=["load", "print", "quit"]):
            with patch("builtins.print") as mock_print:
                from src.main import run
                run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "Usage" in printed

def test_find_no_argument_prints_usage():
    with patch("src.main.load_index", return_value={"life": {}}):
        with patch("builtins.input", side_effect=["load", "find", "quit"]):
            with patch("builtins.print") as mock_print:
                from src.main import run
                run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "Usage" in printed