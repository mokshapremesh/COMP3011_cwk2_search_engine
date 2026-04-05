from src.crawler import crawl
from src.indexer import build_index, add_tfidf
from src.search import save_index, load_index, print_word, find_pages

def run():
    """Main CLI loop for the search engine."""
    print("Search Engine Ready. Commands: build, load, print <word>, find <query>, quit")
    index = {}

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_input:
            print("Please enter a command.")
            continue

        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        if command == "build":
            print("Crawling website... this will take a few minutes due to politeness window.")
            pages = crawl()
            index = build_index(pages)
            index = add_tfidf(index, len(pages))
            save_index(index)
            print(f"Build complete. Indexed {len(index)} unique words from {len(pages)} pages.")

        elif command == "load":
            try:
                index = load_index()
                print(f"Loaded index with {len(index)} unique words.")
            except FileNotFoundError as e:
                print(e)

        elif command == "print":
            if not argument:
                print("Usage: print <word>")
            elif not index:
                print("No index loaded. Run 'build' or 'load' first.")
            else:
                print_word(index, argument)

        elif command == "find":
            if not argument:
                print("Usage: find <query>")
            elif not index:
                print("No index loaded. Run 'build' or 'load' first.")
            else:
                find_pages(index, argument)

        elif command == "quit" or command == "exit":
            print("Goodbye.")
            break

        else:
            print(f"Unknown command: '{command}'. Commands: build, load, print <word>, find <query>, quit")

if __name__ == "__main__":
    run()