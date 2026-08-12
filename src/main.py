import sys

from src.autocomplete import autocomplete
from src.loader.data_loader import load_sentences
from src.loader.index import build_index


DEFAULT_ROOT_PATH = "data/Archive"


def _print_suggestions(results) -> None:
    if not results:
        print("No suggestions.")
        return

    print(f"Here are {len(results)} suggestions:")

    for index, result in enumerate(results, start=1):
        print(
            f"{index}. {result.completed_sentence}  "
            f"({result.source_text}, line {result.offset})"
        )


def _search_and_print(query: str) -> None:
    results = autocomplete.get_best_k_completions(query)
    _print_suggestions(results)
    print(query)


def run(root_path: str) -> None:
    print("Loading the files and preparing the system...")

    sentences = load_sentences(root_path)
    index = build_index(sentences)
    autocomplete.initialize(sentences, index)

    print(
        f"The system is ready. "
        f"Loaded {len(sentences)} sentences."
    )
    print("Enter your text (# to start a new sentence):")

    query = ""

    while True:
        try:
            typed = input()
        except EOFError:
            print()
            return

        # '#' by itself immediately resets the current query.
        if typed == "#":
            query = ""
            print("Enter your text (# to start a new sentence):")
            continue

        # Separate the text that appears before '#'.
        text_before_hash, marker, _ = typed.partition("#")
        query += text_before_hash

        if query:
            _search_and_print(query)

        # A '#' at the end of the input starts a new query.
        if marker:
            query = ""
            print("Enter your text (# to start a new sentence):")


if __name__ == "__main__":
    root_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_ROOT_PATH
    )

    run(root_path)