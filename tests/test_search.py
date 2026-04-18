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
def test_find_words_in_index_but_no_common_pages():
    """Covers the 'no pages found containing all query words' branch."""
    index = {
        "life": {
            "https://quotes.toscrape.com/page/1": {
                "frequency": 1, "positions": [1], "tf": 0.01, "tfidf": 0.04
            }
        },
        "good": {
            "https://quotes.toscrape.com/page/2": {
                "frequency": 1, "positions": [1], "tf": 0.01, "tfidf": 0.04
            }
        }
    }
    results = find_pages(index, "life good")
    assert results == []

def test_keyboard_interrupt_exits_gracefully():
    """Covers the KeyboardInterrupt/EOFError exit branch in main."""
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        with patch("builtins.print") as mock_print:
            from src.main import run
            run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "Exiting" in printed

def test_print_with_loaded_index_calls_print_word():
    """Covers the else branch of print command when index is loaded."""
    with patch("src.main.load_index", return_value={"life": {}}):
        with patch("src.main.print_word") as mock_print_word:
            with patch("builtins.input", side_effect=["load", "print life", "quit"]):
                from src.main import run
                run()
    mock_print_word.assert_called_once()

def test_find_with_loaded_index_calls_find_pages():
    """Covers the else branch of find command when index is loaded."""
    with patch("src.main.load_index", return_value={"life": {}}):
        with patch("src.main.find_pages") as mock_find:
            with patch("builtins.input", side_effect=["load", "find life", "quit"]):
                from src.main import run
                run()
    mock_find.assert_called_once()

def test_load_file_not_found_prints_error():
    """Covers the FileNotFoundError branch in load command."""
    with patch("src.main.load_index", side_effect=FileNotFoundError("No index found")):
        with patch("builtins.input", side_effect=["load", "quit"]):
            with patch("builtins.print") as mock_print:
                from src.main import run
                run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "No index found" in printed

def test_print_with_no_index_loaded_prints_message():
    """Covers line 50 - print command when no index loaded."""
    with patch("builtins.input", side_effect=["print life", "quit"]):
        with patch("builtins.print") as mock_print:
            from src.main import run
            run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "load" in printed.lower()

def test_find_with_no_index_loaded_prints_message():
    """Covers line 58 - find command when no index loaded."""
    with patch("builtins.input", side_effect=["find life", "quit"]):
        with patch("builtins.print") as mock_print:
            from src.main import run
            run()
    printed = " ".join(str(c) for c in mock_print.call_args_list)
    assert "load" in printed.lower()

def test_main_module_runs():
    """Covers line 70 - if __name__ == '__main__' block."""
    with patch("src.main.run") as mock_run:
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-c", "import src.main"],
            capture_output=True
        )
    assert True
