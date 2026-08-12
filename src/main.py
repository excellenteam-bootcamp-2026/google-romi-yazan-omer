import sys
import time

from src.autocomplete import autocomplete
from src.loader.data_loader import load_sentences
from src.loader.index import build_index


DEFAULT_ROOT_PATH = "data/Archive"


def _format_duration(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:05.2f}"


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
    search_start = time.perf_counter()

    results = autocomplete.get_best_k_completions(query)

    search_time = time.perf_counter() - search_start

    _print_suggestions(results)

    print()
    print(query)

    print()
    print(
        f"Search completed in {_format_duration(search_time)}."
    )

    print("="*35)


def run(root_path: str) -> None:
    print("Loading the files and preparing the system...")

    initialization_start = time.perf_counter()

    sentences = load_sentences(root_path)
    index = build_index(sentences)
    autocomplete.initialize(sentences, index)

    initialization_time = (
        time.perf_counter() - initialization_start
    )

    print(
        f"The system is ready. "
        f"Loaded {len(sentences)} sentences.\n"
    )

    print(
        f"System initialization completed in "
        f"{_format_duration(initialization_time)}."
    )
    print("=" * 35)
    print()
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
            print()
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
            print()
            print("Enter your text (# to start a new sentence):")


if __name__ == "__main__":
    root_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_ROOT_PATH
    )

    run(root_path)