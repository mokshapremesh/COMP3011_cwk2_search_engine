# Search Engine Tool — COMP3011 Coursework 2

A command-line search engine that crawls [quotes.toscrape.com](https://quotes.toscrape.com), builds an inverted index with TF-IDF ranking, and provides interactive search with spelling suggestions.

---

## Features

- **BFS web crawler** — breadth-first traversal with a 6-second politeness window
- **Inverted index** — stores word frequency, token positions, and TF per document
- **TF-IDF ranking** — results sorted by relevance, not just presence
- **Multi-word AND queries** — returns only pages containing every search term
- **Spell suggestions** — Levenshtein distance (≤ 2 edits) when a word is not found
- **Index persistence** — save to and load from `data/index.json`

---

## Requirements

- Python 3.9 or later
- See `requirements.txt` for package dependencies

---

## Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd <repo-name>

# 2. (Recommended) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

Start the interactive shell:

```bash
python src/main.py
```

### Commands

| Command | Description |
|---|---|
| `build` | Crawl the website, build the index, and save it to `data/index.json` |
| `load` | Load a previously saved index from `data/index.json` |
| `print <word>` | Display the full index entry for a word (frequency, positions, TF, TF-IDF) |
| `find <query>` | Search for pages containing all query words, ranked by TF-IDF |
| `quit` / `exit` | Exit the program |

### Examples

```
> load
Index loaded from data/index.json
Loaded index with 1842 unique words.

> print indifference
Index entry for 'indifference':
  https://quotes.toscrape.com/page/3
    frequency : 2
    positions : [45, 102]
    tf        : 0.0083
    tfidf     : 0.0241

> find indifference
Found 1 page(s) for 'indifference':
  https://quotes.toscrape.com/page/3  (score: 0.0241)

> find good friends
Found 2 page(s) for 'good friends':
  https://quotes.toscrape.com/page/1  (score: 0.0312)
  https://quotes.toscrape.com/page/4  (score: 0.0187)

> find nonexistentwrd
'nonexistentwrd' not found. Did you mean: nonexistent?

> quit
Goodbye.
```

> **Note:** `build` takes several minutes because of the mandatory 6-second politeness window between requests. Use `load` to reuse the pre-built `data/index.json` included in the repository.

---

## Architecture

```
src/
├── crawler.py   — BFS web crawler (requests + BeautifulSoup)
├── indexer.py   — Tokenisation, inverted index construction, TF-IDF
├── search.py    — JSON persistence, search, spell suggestions
└── main.py      — Interactive CLI shell (REPL)
```

### Data flow

```
crawler.crawl()
    │  { url: page_text }
    ▼
indexer.build_index()  →  indexer.add_tfidf()
    │  { word: { url: { frequency, positions, tf, tfidf } } }
    ▼
search.save_index()  ←→  search.load_index()
    │
    ▼
search.find_pages()  /  search.print_word()
```

### Index structure (JSON)

```json
{
  "word": {
    "https://quotes.toscrape.com/page/1": {
      "frequency": 3,
      "positions": [12, 45, 89],
      "tf": 0.0125,
      "tfidf": 0.0287
    }
  }
}
```

### TF-IDF scoring

```
TF  = frequency / total_words_in_document
IDF = log( total_documents / documents_containing_word )
TF-IDF = TF × IDF
```

Words that appear in every page (e.g. navigation text) get IDF ≈ 0 and
are effectively filtered out, while rare, meaningful words score highly.

---

## Testing

```bash
# Run the full test suite
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/test_search.py

# Run a specific test by name
pytest tests/test_indexer.py::test_build_index_performance
```

The test suite achieves **99% line coverage** across 57 tests, including:

- **Unit tests** — tokenisation, index construction, TF-IDF, link extraction, text parsing
- **Integration tests** — all four CLI commands tested end-to-end via patched `input()`
- **Edge cases** — empty queries, missing words, case insensitivity, no-common-pages, `KeyboardInterrupt`
- **Performance test** — indexing 100 pages of 900 words must complete in under 2 seconds

---

## Dependencies

| Package | Purpose |
|---|---|
| `requests` | HTTP requests for web crawling |
| `beautifulsoup4` | HTML parsing and text extraction |
| `pytest` | Test framework |
| `pytest-cov` | Test coverage reporting |

Install all dependencies with:

```bash
pip install -r requirements.txt
```
