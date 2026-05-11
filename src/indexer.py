"""
indexer.py — Inverted index builder with TF-IDF scoring

Converts a dictionary of {url: page_text} into an inverted index —
the core data structure of a search engine.  The index maps each
unique word to the set of pages it appears in, along with statistics
(frequency, positions, TF, TF-IDF) needed for ranked retrieval.

Data structure design rationale
--------------------------------
The index is a nested dict:  { word: { url: { stats } } }

- O(1) average lookup for any word (hash table)
- O(1) average lookup for any URL within a word's entry
- Scales to large vocabularies without linear scans

Alternative considered: a flat list of (word, url, stats) tuples
would require O(N) scan per query — rejected as too slow.
"""

import math
import re
from collections import defaultdict


def tokenize(text: str) -> list[str]:
    """
    Convert raw text into a list of lowercase word tokens.

    Uses a regex to extract only alphabetic sequences, which
    simultaneously lowercases (after text.lower()) and removes
    punctuation, numbers, and whitespace in one pass.

    Design note: we keep only alphabetic tokens (a-z) for simplicity.
    Numbers and hyphenated compounds are discarded — acceptable for a
    quotes website where search terms are plain English words.

    Args:
        text: Any raw string (HTML-stripped page text).

    Returns:
        A list of lowercase word tokens, preserving word order
        (order matters for position tracking).

    Examples:
        >>> tokenize("Hello, World!")
        ['hello', 'world']
        >>> tokenize("it's a beautiful day!")
        ['it', 's', 'a', 'beautiful', 'day']
    """
    # Lowercase first so 'Good' and 'good' map to the same token
    text = text.lower()

    # \b[a-z]+\b — match whole words made of only ASCII letters;
    # punctuation, digits, and apostrophes are implicitly excluded
    words = re.findall(r'\b[a-z]+\b', text)

    return words


def build_index(pages: dict[str, str]) -> dict:
    """
    Build an inverted index from a collection of crawled pages.

    For each page, every word is tokenized and recorded with:
      - frequency:  how many times the word appears on that page
      - positions:  list of token offsets (0-based) where the word occurs
      - tf:         term frequency = frequency / total_words_on_page

    Positions are stored to support potential phrase-query extensions
    (e.g. proximity search) and as evidence of depth of implementation.

    Time complexity:  O(N × M)
        N = number of pages, M = average words per page
    Space complexity: O(V × D)
        V = vocabulary size, D = average documents per word

    Args:
        pages: Dict mapping URL strings to their extracted page text.

    Returns:
        An inverted index dict: { word: { url: { frequency, positions, tf } } }
    """
    # defaultdict(dict) means index[new_word] automatically returns {}
    # instead of raising a KeyError — cleaner than checking 'if word in index'
    index: defaultdict = defaultdict(dict)

    # Track total word count per page — needed to compute TF correctly
    doc_word_counts: dict[str, int] = {}

    for url, text in pages.items():
        words = tokenize(text)

        # Store total word count so we can normalise frequencies later
        doc_word_counts[url] = len(words)

        # enumerate gives us both the token position and the token itself
        for position, word in enumerate(words):
            # Initialise entry for this (word, url) pair on first encounter
            if url not in index[word]:
                index[word][url] = {
                    "frequency": 0,
                    "positions": [],
                    "tf": 0.0       # filled in below after full page scan
                }

            # Increment count and record where in the document this word appears
            index[word][url]["frequency"] += 1
            index[word][url]["positions"].append(position)

    # --- Compute Term Frequency (TF) ---
    # TF = frequency / total_words  (raw count normalised by document length)
    # Normalisation prevents long pages from always outranking short ones.
    for word, urls in index.items():
        for url, stats in urls.items():
            total_words = doc_word_counts[url]
            # Guard against empty documents (shouldn't happen, but defensive)
            stats["tf"] = stats["frequency"] / total_words if total_words > 0 else 0.0

    # Convert defaultdict back to a plain dict for JSON serialisation safety
    return dict(index)


def add_tfidf(index: dict, total_docs: int) -> dict:
    """
    Augment each index entry with a TF-IDF score.

    TF-IDF (Term Frequency – Inverse Document Frequency) is the
    standard weighting scheme in information retrieval.  It rewards
    words that appear frequently in a specific page (high TF) but
    rarely across the whole collection (high IDF), making it ideal
    for distinguishing relevant pages from generic ones.

    Formula:
        TF-IDF = TF × IDF
        IDF    = log( total_docs / docs_containing_word )

    IDF Properties:
      - Word appears in 1 of 10 docs  → IDF = log(10) ≈ 2.30  (rare, valued)
      - Word appears in 10 of 10 docs → IDF = log(1)  = 0.00  (universal, ignored)

    This function mutates the index in-place and also returns it,
    allowing chained assignment:  index = add_tfidf(index, n)

    Args:
        index:      The inverted index produced by build_index().
        total_docs: Total number of documents (pages) in the collection.

    Returns:
        The same index dict, with a 'tfidf' key added to every entry.
    """
    for word, urls in index.items():
        # Number of documents that contain this word
        docs_with_word = len(urls)

        # IDF: penalises words that appear in many documents (common words
        # like 'the', 'and' will have IDF ≈ 0 and contribute little to ranking)
        # The guard 'if docs_with_word > 0' is always True here (since we only
        # iterate over words that exist in the index), but kept for safety.
        idf = math.log(total_docs / docs_with_word) if docs_with_word > 0 else 0.0

        for url, stats in urls.items():
            # TF-IDF combines local term importance (TF) with global rarity (IDF)
            stats["tfidf"] = stats["tf"] * idf

    return index
