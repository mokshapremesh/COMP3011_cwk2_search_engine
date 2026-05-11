# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the interactive CLI
python src/main.py

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/test_search.py

# Run a single test by name
pytest tests/test_search.py::test_find_pages_single_word
```

## Architecture

This is a web search engine for `quotes.toscrape.com` with four modules:

### Data flow

```
crawler.py → indexer.py → search.py ← main.py (CLI)
```

1. **`crawler.py`** — BFS crawl starting from `https://quotes.toscrape.com`. Returns `{url: text}`. Enforces a 6-second politeness delay between requests.

2. **`indexer.py`** — Builds an inverted index from crawled pages. Tokenizes text (lowercase, strips punctuation), then computes TF per word/URL pair. `add_tfidf()` adds a `tfidf` key to each entry using `TF × log(total_docs / docs_with_word)`.

   Index structure:
   ```json
   { "word": { "url": { "freq": N, "positions": [...], "tf": 0.x, "tfidf": 0.x } } }
   ```

3. **`search.py`** — Index persistence (JSON at `data/index.json`), single-word lookup, multi-word AND query ranked by summed TF-IDF, and Levenshtein-distance query suggestions (edit distance ≤ 2).

4. **`main.py`** — Interactive command loop. Holds index state in memory. Commands: `build`, `load`, `print <word>`, `find <query>`, `quit`/`exit`.

### Key function signatures

| Function | Module | Purpose |
|---|---|---|
| `crawl(base_url)` | crawler | Returns `{url: text}` |
| `build_index(pages)` | indexer | Returns inverted index |
| `add_tfidf(index, total_docs)` | indexer | Mutates index in-place, returns it |
| `find_pages(index, query)` | search | Returns sorted `[(url, score)]` |
| `suggest_similar(index, word)` | search | Returns list of close vocabulary words |
| `save_index` / `load_index` | search | JSON serialization |

## Testing conventions

Tests use `unittest.mock` to patch all network I/O (`requests.get`) and file I/O. Integration tests drive `main.run()` by patching `builtins.input` with a command sequence ending in `"quit"`. Coverage target is 99%.
