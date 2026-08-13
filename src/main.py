import sys
import time

from src.autocomplete import autocomplete
from src.loader.cache import load_or_build_cache


DEFAULT_ROOT_PATH = "data/Archive"


def _format_duration(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    return f"{minutes}:{remaining_seconds:05.2f}"


def _print_suggestions(results) -> None:
    """Print each completed sentence and its source location."""
    if not results:
        print("No suggestions.")
        return

    print(f"Here are {len(results)} suggestions:")

    for index, result in enumerate(results, start=1):
        print()
        print(f"Suggestion {index}:")
        print(f"  Sentence: {result.completed_sentence}")
        print(f"  File: {result.source_text}")
        print(f"  Line: {result.offset}")
        print(f"  Score: {result.score}")


def _search_and_print(query: str) -> None:
    search_start = time.perf_counter()

    results = (
        autocomplete.get_best_k_completions(
            query
        )
    )

    search_time = (
        time.perf_counter() - search_start
    )

    _print_suggestions(results)

    print()
    print(query)

    print()

    print(
        f"Search completed in "
        f"{_format_duration(search_time)}."
    )

    print("=" * 35)


def run(root_path: str) -> None:
    print("Preparing the system...")

    initialization_start = time.perf_counter()

    (
        sentences,
        index,
        short_query_index,
        loaded_from_cache,
    ) = load_or_build_cache(root_path)

    autocomplete.initialize(
        sentences,
        index,
        short_query_index,
    )

    initialization_time = (
        time.perf_counter()
        - initialization_start
    )

    print(
        f"The system is ready. "
        f"Loaded {len(sentences)} sentences.\n"
    )

    if loaded_from_cache:
        print(
            "Prepared data loaded from cache."
        )
    else:
        print(
            "Prepared data built from source files "
            "and saved to cache."
        )

    print(
        f"System initialization completed in "
        f"{_format_duration(initialization_time)}."
    )

    print("=" * 35)
    print()

    print(
        "Enter your text "
        "(# to start a new sentence):"
    )

    query = ""

    while True:
        try:
            typed = input()

        except (EOFError, KeyboardInterrupt):
            print()
            return

        # '#' by itself resets the current query.
        if typed == "#":
            query = ""

            print()

            print(
                "Enter your text "
                "(# to start a new sentence):"
            )

            continue

        text_before_hash, marker, _ = (
            typed.partition("#")
        )

        query += text_before_hash

        if query:
            _search_and_print(query)

        if marker:
            query = ""

            print()

            print(
                "Enter your text "
                "(# to start a new sentence):"
            )


if __name__ == "__main__":
    root_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_ROOT_PATH
    )

    run(root_path)