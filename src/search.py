import json
import os
from src.indexer import tokenize

INDEX_PATH = "data/index.json"

def save_index(index: dict, path: str = INDEX_PATH) -> None:
    """Save the inverted index to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(index, f, indent=2)
    print(f"Index saved to {path}")

def load_index(path: str = INDEX_PATH) -> dict:
    """Load the inverted index from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"No index found at {path}. Run 'build' first.")
    with open(path, "r") as f:
        index = json.load(f)
    print(f"Index loaded from {path}")
    return index

def print_word(index: dict, word: str) -> None:
    """Print the inverted index entry for a given word."""
    word = word.lower().strip()
    if word not in index:
        print(f"'{word}' not found in index.")
        return
    print(f"\nIndex entry for '{word}':")
    for url, stats in index[word].items():
        print(f"  {url}")
        print(f"    frequency : {stats['frequency']}")
        print(f"    positions : {stats['positions']}")
        print(f"    tf        : {stats['tf']:.4f}")
        print(f"    tfidf     : {stats.get('tfidf', 0.0):.4f}")

def find_pages(index: dict, query: str) -> list:
    """
    Find pages containing all words in the query.
    Returns a list of (url, score) tuples ranked by TF-IDF.
    """
    words = tokenize(query)

    if not words:
        print("Empty query.")
        return []

    # Find pages that contain ALL query words (AND logic)
    matching_urls = None
    for word in words:
        if word not in index:
            suggestions = suggest_similar(index, word)
            if suggestions:
                print(f"'{word}' not found. Did you mean: {', '.join(suggestions)}?")
            else:
                print(f"'{word}' not found in index.")
            return []
        urls_for_word = set(index[word].keys())
        if matching_urls is None:
            matching_urls = urls_for_word
        else:
            matching_urls &= urls_for_word

    if not matching_urls:
        print("No pages found containing all query words.")
        return []

    # Rank by combined TF-IDF score across all query words
    results = []
    for url in matching_urls:
        score = sum(
            index[word][url].get("tfidf", 0.0)
            for word in words
        )
        results.append((url, score))

    results.sort(key=lambda x: x[1], reverse=True)

    print(f"\nFound {len(results)} page(s) for '{query}':")
    for url, score in results:
        print(f"  {url}  (score: {score:.4f})")

    return results
def suggest_similar(index: dict, word: str, max_suggestions: int = 3) -> list:
    """
    Suggest similar words from the index using Levenshtein distance.
    
    Args:
        index: the inverted index
        word: the word to find suggestions for
        max_suggestions: maximum number of suggestions to return
    
    Returns:
        list of similar words found in the index
    
    Time complexity: O(V * L) where V = vocabulary size, L = word length
    """
    def levenshtein(s1: str, s2: str) -> int:
        """Calculate edit distance between two strings."""
        if len(s1) < len(s2):
            return levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    word = word.lower().strip()
    suggestions = []
    for indexed_word in index.keys():
        distance = levenshtein(word, indexed_word)
        if distance <= 2:
            suggestions.append((indexed_word, distance))
    suggestions.sort(key=lambda x: x[1])
    return [w for w, _ in suggestions[:max_suggestions]]
