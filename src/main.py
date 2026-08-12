import sys

from src.autocomplete import autocomplete
from src.loader.data_loader import load_sentences
from src.loader.index import build_index

DEFAULT_ROOT_PATH = "data/Archive"


def _print_suggestions(query: str, results) -> None:
    if not results:
        print("No suggestions.")
        return

    print(f"Here are {len(results)} suggestions:")
    for i, result in enumerate(results, start=1):
        print(f"{i}. {result.completed_sentence}  ({result.source_text}, line {result.offset})")


def run(root_path: str) -> None:
    print("Loading the files and preparing the system...")
    sentences = load_sentences(root_path)
    index = build_index(sentences)
    autocomplete.initialize(sentences, index)
    print(f"The system is ready. Loaded {len(sentences)} sentences.")

    query = ""
    print("Enter your text (# to start a new sentence):")

    while True:
        try:
            typed = input()
        except EOFError:
            print()
            return

        if typed == "#":
            query = ""
            print("Enter your text (# to start a new sentence):")
            continue

        query += typed
        results = autocomplete.get_best_k_completions(query)
        _print_suggestions(query, results)
        print(query)


if __name__ == "__main__":
    root_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT_PATH
    run(root_path)
