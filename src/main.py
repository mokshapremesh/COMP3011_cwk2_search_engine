"""
main.py — Command-line interface (shell) for the search engine

Provides an interactive REPL (Read-Eval-Print Loop) that accepts four
commands defined in the assignment brief:

  build          — crawl the website, build the index, save to disk
  load           — load a previously saved index from disk
  print <word>   — display all index statistics for a given word
  find <query>   — search for pages containing all query words
  quit / exit    — terminate the program

The index is held in memory as a plain Python dict for the lifetime of
the session, so 'load' only needs to read the file once.
"""

from src.crawler import crawl
from src.indexer import add_tfidf, build_index
from src.search import find_pages, load_index, print_word, save_index


def run() -> None:
    """
    Start the interactive search engine shell.

    The function loops indefinitely, reading one command per iteration,
    until the user types 'quit', 'exit', or sends EOF / Ctrl-C.

    Command parsing strategy:
      - Split the input into at most two parts (command + rest-of-line),
        so 'find good friends' correctly passes 'good friends' as the query.
      - Convert the command token to lowercase for case-insensitive matching,
        but preserve the argument's original casing (tokenize() handles
        normalisation later).

    State management:
      - 'index' is the single shared state variable.  It starts empty ({})
        and is replaced atomically by 'build' or 'load'.
      - Checking 'not index' before 'print'/'find' ensures a helpful error
        is shown rather than a silent empty result if the user forgets to
        load the index first.
    """
    print("Search Engine Ready. Commands: build, load, print <word>, find <query>, quit")

    # The inverted index lives here in memory for the session.
    # Empty dict signals that no index has been loaded yet.
    index: dict = {}

    while True:
        try:
            # Prompt the user with '> ' — same style as the assignment brief
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl-C or piped input ending — exit cleanly without a traceback
            print("\nExiting.")
            break

        # Ignore blank lines rather than treating them as unknown commands
        if not user_input:
            print("Please enter a command.")
            continue

        # Split into ['command', 'rest of line'] — maxsplit=1 keeps multi-word
        # arguments (e.g. 'find good friends') intact as a single string
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()                      # normalise command token
        argument = parts[1] if len(parts) > 1 else ""  # everything after the command

        # --- build ---
        if command == "build":
            print("Crawling website... this will take a few minutes due to politeness window.")
            pages = crawl()                          # fetch all pages (slow — ~6s per page)
            index = build_index(pages)               # build inverted index with TF
            index = add_tfidf(index, len(pages))     # augment with TF-IDF scores
            save_index(index)                        # persist to data/index.json
            print(f"Build complete. Indexed {len(index)} unique words from {len(pages)} pages.")

        # --- load ---
        elif command == "load":
            try:
                index = load_index()                 # deserialise from data/index.json
                print(f"Loaded index with {len(index)} unique words.")
            except FileNotFoundError as e:
                # Happens when 'build' has never been run yet
                print(e)

        # --- print <word> ---
        elif command == "print":
            if not argument:
                # User typed 'print' with no word — show usage hint
                print("Usage: print <word>")
            elif not index:
                # Index not yet loaded — give actionable guidance
                print("No index loaded. Run 'build' or 'load' first.")
            else:
                print_word(index, argument)

        # --- find <query> ---
        elif command == "find":
            if not argument:
                # User typed 'find' with no query — show usage hint
                print("Usage: find <query>")
            elif not index:
                print("No index loaded. Run 'build' or 'load' first.")
            else:
                # argument may be a single word or a multi-word phrase;
                # find_pages tokenises it internally
                find_pages(index, argument)

        # --- quit / exit ---
        elif command in ("quit", "exit"):
            print("Goodbye.")
            break

        # --- unknown command ---
        else:
            print(
                f"Unknown command: '{command}'. "
                "Commands: build, load, print <word>, find <query>, quit"
            )


if __name__ == "__main__":
    # Entry point when the script is run directly: python src/main.py
    run()
