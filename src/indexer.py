import re
import math
from collections import defaultdict

def tokenize(text: str) -> list:
    """Convert text to lowercase list of words, removing punctuation."""
    text = text.lower()
    words = re.findall(r'\b[a-z]+\b', text)
    return words

def build_index(pages: dict) -> dict:
    """
    Build an inverted index from crawled pages.
    
    Structure:
    {
        "word": {
            "url": {
                "frequency": 3,
                "positions": [4, 17, 42],
                "tf": 0.03
            }
        }
    }
    """
    index = defaultdict(dict)
    doc_word_counts = {}

    for url, text in pages.items():
        words = tokenize(text)
        doc_word_counts[url] = len(words)

        for position, word in enumerate(words):
            if url not in index[word]:
                index[word][url] = {
                    "frequency": 0,
                    "positions": [],
                    "tf": 0.0
                }
            index[word][url]["frequency"] += 1
            index[word][url]["positions"].append(position)

    # Calculate TF (term frequency) for each word in each doc
    for word, urls in index.items():
        for url, stats in urls.items():
            total_words = doc_word_counts[url]
            stats["tf"] = stats["frequency"] / total_words if total_words > 0 else 0.0

    return dict(index)

def add_tfidf(index: dict, total_docs: int) -> dict:
    """
    Add TF-IDF score to each word/url entry.
    TF-IDF = TF * log(total_docs / docs_containing_word)
    """
    for word, urls in index.items():
        docs_with_word = len(urls)
        idf = math.log(total_docs / docs_with_word) if docs_with_word > 0 else 0.0
        for url, stats in urls.items():
            stats["tfidf"] = stats["tf"] * idf
    return index