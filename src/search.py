"""
search.py — Index persistence, search, and query suggestions

Provides five public functions that sit between the inverted index
and the CLI:

  save_index      — serialise the index to a JSON file on disk
  load_index      — deserialise the index from disk back into memory
  print_word      — display all statistics for a single word
  find_pages      — AND-query over the index, results ranked by TF-IDF
  suggest_similar — Levenshtein-distance spell correction
"""

import json
import os

from src.indexer import tokenize

# Default path where the index file is stored.
# Keeping it under data/ separates generated artefacts from source code.
INDEX_PATH = "data/index.json"


def save_index(index: dict, path: str = INDEX_PATH) -> None:
    """
    Serialise the inverted index to a JSON file.

    JSON is chosen over binary formats (pickle, shelve) because:
      - Human-readable: the saved file can be opened and inspected
      - Language-agnostic: another tool can consume the index later
      - Standard library: no extra dependencies required

    os.makedirs(..., exist_ok=True) ensures the data/ directory is
    created automatically on a fresh clone with no data/ folder yet.

    Args:
        index: The inverted index dict produced by build_index/add_tfidf.
        path:  File path to write to (default: data/index.json).
    """
    # Create the target directory tree if it does not already exist
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        # indent=2 keeps the file human-readable; remove for smaller files
        json.dump(index, f, indent=2)

    print(f"Index saved to {path}")


def load_index(path: str = INDEX_PATH) -> dict:
    """
    Deserialise the inverted index from a JSON file.

    Raises FileNotFoundError with an actionable message when the file
    does not exist — typically because 'build' has not been run yet.

    Args:
        path: File path to read from (default: data/index.json).

    Returns:
        The inverted index dict.

    Raises:
        FileNotFoundError: If no index file exists at the given path.
    """
    if not os.path.exists(path):
        # Give the user a clear action to take rather than a bare Python error
        raise FileNotFoundError(f"No index found at {path}. Run 'build' first.")

    with open(path, "r") as f:
        index = json.load(f)

    print(f"Index loaded from {path}")
    return index


def suggest_similar(
    index: dict,
    word: str,
    max_suggestions: int = 3
) -> list[str]:
    """
    Suggest vocabulary words that are close to the given word.

    Uses the Levenshtein (edit distance) algorithm to find index words
    that differ from the query by at most 2 edits.  An edit is a single
    character insertion, deletion, or substitution.

    Algorithm: Wagner–Fischer dynamic programming
      - Build a (|s1|+1) × (|s2|+1) table row by row
      - Each cell = minimum edits to transform s1[:i] into s2[:j]
      - Space-optimised: only two rows are kept in memory at once

    Time complexity:  O(V × L²)  where V = vocabulary size, L = max word length
    Space complexity: O(L)       — only two DP rows stored simultaneously

    Design note: threshold of 2 catches single-character typos and most
    common misspellings without flooding the output with spurious matches.

    Args:
        index:           The loaded inverted index (keys = vocabulary words).
        word:            The misspelled or unknown word to correct.
        max_suggestions: Maximum number of suggestions to return.

    Returns:
        Up to max_suggestions vocabulary words with edit distance ≤ 2,
        sorted by closeness (nearest first).
    """
    def levenshtein(s1: str, s2: str) -> int:
        """
        Compute the Levenshtein (edit) distance between two strings.

        Optimisation: ensure s1 is the longer string so the inner loop
        iterates over the shorter one — minimises the number of cell
        computations per row.
        """
        # Swap so s1 is always the longer string (reduces inner-loop width)
        if len(s1) < len(s2):
            return levenshtein(s2, s1)

        # Base case: transforming s1 into an empty string costs |s1| deletions
        if len(s2) == 0:
            return len(s1)

        # Initialise the previous row: cost of transforming "" → s2[:j]
        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            # Cost of deleting the first i+1 characters of s1
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # Three possible edit operations from the DP recurrence:
                insertions    = previous_row[j + 1] + 1      # insert c2 into s1
                deletions     = current_row[j] + 1           # delete c1 from s1
                substitutions = previous_row[j] + (c1 != c2) # replace c1↔c2 (free if equal)

                current_row.append(min(insertions, deletions, substitutions))

            # Slide the window: discard the old row, keep only the current one
            previous_row = current_row

        # Bottom-right cell of the completed DP table = final edit distance
        return previous_row[-1]

    # Normalise to match how the index was built (tokenize also lowercases)
    word = word.lower().strip()

    # Score every vocabulary word against the query
    suggestions: list[tuple[str, int]] = []
    for indexed_word in index.keys():
        distance = levenshtein(word, indexed_word)
        if distance <= 2:
            suggestions.append((indexed_word, distance))

    # Return closest matches first; cap at max_suggestions
    suggestions.sort(key=lambda x: x[1])
    return [w for w, _ in suggestions[:max_suggestions]]


def print_word(index: dict, word: str) -> None:
    """
    Print all index statistics for a single word.

    Normalises the input to lowercase so the lookup is case-insensitive,
    consistent with how the index was built.  If the word is not found,
    suggest_similar() is called to offer spelling corrections.

    Output format for each page the word appears in:
        <url>
          frequency : N
          positions : [p1, p2, ...]
          tf        : 0.XXXX
          tfidf     : 0.XXXX

    Args:
        index: The loaded inverted index.
        word:  The word to look up (case-insensitive).
    """
    # Normalise case and whitespace so 'Good', 'GOOD', ' good ' all match
    word = word.lower().strip()

    if word not in index:
        # Before giving up, check for near-matches in the vocabulary
        suggestions = suggest_similar(index, word)
        if suggestions:
            print(f"'{word}' not found. Did you mean: {', '.join(suggestions)}?")
        else:
            print(f"'{word}' not found in index.")
        return

    print(f"\nIndex entry for '{word}':")

    for url, stats in index[word].items():
        # Print each document's stats in a clearly aligned block
        print(f"  {url}")
        print(f"    frequency : {stats['frequency']}")
        print(f"    positions : {stats['positions']}")
        print(f"    tf        : {stats['tf']:.4f}")
        # tfidf may be absent if add_tfidf() was not called; default to 0.0
        print(f"    tfidf     : {stats.get('tfidf', 0.0):.4f}")


def find_pages(index: dict, query: str) -> list[tuple[str, float]]:
    """
    Search the index for pages containing ALL words in the query (AND logic).

    AND logic (set intersection) is used rather than OR (union) because
    a page matching every query word is almost certainly more relevant
    than one that contains only some of them.

    Ranking: pages are sorted by the sum of TF-IDF scores for each query
    word.  Summing (rather than averaging) rewards pages that score well
    on multiple query terms simultaneously.

    If any query word is missing from the index, suggest_similar() is
    called to offer spelling corrections before returning an empty list.

    Args:
        index: The loaded inverted index.
        query: One or more space-separated search terms (case-insensitive).

    Returns:
        A list of (url, score) tuples sorted by score descending,
        or an empty list if no pages match or the query is empty.
    """
    # Reuse the same tokenisation used at index-build time (lowercase + regex)
    words = tokenize(query)

    if not words:
        # Guard: empty string or a query composed entirely of punctuation/digits
        print("Empty query.")
        return []

    # --- AND intersection ---
    # None signals "not yet initialised"; the first word sets the base set.
    # Each subsequent word narrows it via set intersection (&=).
    matching_urls: set[str] | None = None

    for word in words:
        if word not in index:
            # Word absent — offer spell suggestions before giving up
            suggestions = suggest_similar(index, word)
            if suggestions:
                print(f"'{word}' not found. Did you mean: {', '.join(suggestions)}?")
            else:
                print(f"'{word}' not found in index.")
            return []

        urls_for_word = set(index[word].keys())

        if matching_urls is None:
            matching_urls = urls_for_word          # first word: initialise
        else:
            matching_urls &= urls_for_word         # subsequent: narrow down

    if not matching_urls:
        # Words exist individually but no single page contains all of them
        print("No pages found containing all query words.")
        return []

    # --- TF-IDF ranking ---
    # Sum TF-IDF across all query words for each candidate page.
    # .get("tfidf", 0.0) guards against an index built without add_tfidf().
    results: list[tuple[str, float]] = []
    for url in matching_urls:
        score = sum(
            index[word][url].get("tfidf", 0.0)
            for word in words
        )
        results.append((url, score))

    # Sort highest score first (most relevant page at the top)
    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\nFound {len(results)} page(s) for '{query}':")
    for url, score in results:
        print(f"  {url}  (score: {score:.4f})")

    return results
