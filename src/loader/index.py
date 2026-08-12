import string
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from src.loader.normalizer import normalize_text
from src.models import Sentence


TRIGRAM_SIZE = 3
MIN_SAFE_QUERY_LENGTH = 6
MAX_FILTER_TRIGRAMS = 4

NORMALIZED_ALPHABET = (
    string.ascii_lowercase
    + string.digits
    + " "
)

SHORT_QUERY_ALPHABET = (
    string.ascii_lowercase
    + string.digits
)

SHORT_QUERY_MAX_LENGTH = 2
TOP_K = 5


TrigramIndex = Dict[str, Set[int]]
ShortQueryIndex = Dict[str, List[int]]


MIN_VARIANT_SEARCH_QUERY_LENGTH = (
    TRIGRAM_SIZE + 1
)


def generate_trigrams(text: str) -> Set[str]:
    """Return all unique trigrams in text."""
    if len(text) < TRIGRAM_SIZE:
        return set()

    return {
        text[i:i + TRIGRAM_SIZE]
        for i in range(
            len(text) - TRIGRAM_SIZE + 1
        )
    }


def _add_sentence_to_trigram_index(
    sentence_id: int,
    normalized_text: str,
    index: Dict[str, Set[int]],
) -> None:
    """
    Add one sentence to the trigram index.
    """
    for trigram in generate_trigrams(
        normalized_text
    ):
        index[trigram].add(sentence_id)


def _update_short_query_top_five(
    query: str,
    sentence_id: int,
    sentences: List[Sentence],
    short_query_index: ShortQueryIndex,
) -> None:
    """
    Keep only the alphabetically best five
    exact matches for a short query.
    """
    bucket = short_query_index.setdefault(
        query,
        [],
    )

    if len(bucket) < TOP_K:
        bucket.append(sentence_id)

        bucket.sort(
            key=lambda current_id: (
                sentences[current_id].text,
                current_id,
            )
        )

        return

    worst_id = bucket[-1]

    new_key = (
        sentences[sentence_id].text,
        sentence_id,
    )

    worst_key = (
        sentences[worst_id].text,
        worst_id,
    )

    if new_key >= worst_key:
        return

    bucket.append(sentence_id)

    bucket.sort(
        key=lambda current_id: (
            sentences[current_id].text,
            current_id,
        )
    )

    bucket.pop()


def _add_sentence_to_search_indexes(
    sentence_id: int,
    sentence: Sentence,
    sentences: List[Sentence],
    index: Dict[str, Set[int]],
    short_query_index: ShortQueryIndex,
    last_seen: Dict[str, int],
) -> None:
    """
    Add one sentence to both the trigram index
    and short-query index in one text pass.
    """
    text = sentence.normalized_text
    previous_character = None

    for position, character in enumerate(text):

        # Build trigram index.
        if (
            position + TRIGRAM_SIZE
            <= len(text)
        ):
            trigram = text[
                position:
                position + TRIGRAM_SIZE
            ]

            index[trigram].add(
                sentence_id
            )

        # One-character exact query.
        if (
            character
            in SHORT_QUERY_ALPHABET
        ):
            if (
                last_seen.get(character)
                != sentence_id
            ):
                last_seen[character] = (
                    sentence_id
                )

                _update_short_query_top_five(
                    character,
                    sentence_id,
                    sentences,
                    short_query_index,
                )

        # Two-character exact query.
        if (
            previous_character is not None
            and previous_character
            in SHORT_QUERY_ALPHABET
            and character
            in SHORT_QUERY_ALPHABET
        ):
            bigram = (
                previous_character
                + character
            )

            if (
                last_seen.get(bigram)
                != sentence_id
            ):
                last_seen[bigram] = (
                    sentence_id
                )

                _update_short_query_top_five(
                    bigram,
                    sentence_id,
                    sentences,
                    short_query_index,
                )

        previous_character = character


def build_index(
    sentences: List[Sentence],
) -> TrigramIndex:
    """
    Build only the trigram inverted index.

    This function is kept for the existing
    tests and existing project interface.
    """
    index: Dict[str, Set[int]] = (
        defaultdict(set)
    )

    for sentence_id, sentence in enumerate(
        sentences
    ):
        _add_sentence_to_trigram_index(
            sentence_id,
            sentence.normalized_text,
            index,
        )

    return dict(index)


def build_search_indexes(
    sentences: List[Sentence],
) -> Tuple[
    TrigramIndex,
    ShortQueryIndex,
]:
    """
    Build both search structures together:

    1. Trigram inverted index.
    2. Compact Top-5 index for 1-2 char queries.
    """
    index: Dict[str, Set[int]] = (
        defaultdict(set)
    )

    short_query_index: ShortQueryIndex = {}

    last_seen: Dict[str, int] = {}

    for sentence_id, sentence in enumerate(
        sentences
    ):
        _add_sentence_to_search_indexes(
            sentence_id,
            sentence,
            sentences,
            index,
            short_query_index,
            last_seen,
        )

    return (
        dict(index),
        short_query_index,
    )


def _generate_one_edit_variants(
    text: str,
) -> Set[str]:
    """
    Generate strings within at most
    one edit from text.
    """
    variants = {text}

    for (
        position,
        original_character,
    ) in enumerate(text):

        # Deletion
        variants.add(
            text[:position]
            + text[position + 1:]
        )

        # Substitution
        for replacement in (
            NORMALIZED_ALPHABET
        ):
            if (
                replacement
                != original_character
            ):
                variants.add(
                    text[:position]
                    + replacement
                    + text[position + 1:]
                )

    # Insertion
    for position in range(
        len(text) + 1
    ):
        for inserted_character in (
            NORMALIZED_ALPHABET
        ):
            variants.add(
                text[:position]
                + inserted_character
                + text[position:]
            )

    return variants


def _exact_variant_candidate_ids(
    variant: str,
    index: TrigramIndex,
) -> Set[int]:
    """
    Find sentences containing every
    trigram of a variant.
    """
    trigrams = generate_trigrams(
        variant
    )

    if not trigrams:
        return set()

    postings = []

    for trigram in trigrams:
        posting = index.get(trigram)

        if not posting:
            return set()

        postings.append(posting)

    postings.sort(key=len)

    candidate_ids = (
        postings[0].copy()
    )

    for posting in postings[1:]:
        candidate_ids.intersection_update(
            posting
        )

        if not candidate_ids:
            break

    return candidate_ids


def _short_query_candidate_ids(
    query: str,
    index: TrigramIndex,
) -> Set[int]:
    """
    Find candidates for a query
    of length four or five.
    """
    candidate_ids: Set[int] = set()

    for variant in (
        _generate_one_edit_variants(query)
    ):
        candidate_ids.update(
            _exact_variant_candidate_ids(
                variant,
                index,
            )
        )

    return candidate_ids


def get_candidates(
    query: str,
    sentences: List[Sentence],
    index: TrigramIndex,
    short_query_index:
        ShortQueryIndex | None = None,
) -> List[Sentence]:
    """
    Return candidates without
    performing final scoring.
    """
    normalized_query = normalize_text(
        query
    )

    # -----------------------------
    # FAST PATH FOR LENGTH 1-2
    # -----------------------------
    if (
        0
        < len(normalized_query)
        <= SHORT_QUERY_MAX_LENGTH
        and short_query_index is not None
    ):
        exact_top_five = (
            short_query_index.get(
                normalized_query,
                [],
            )
        )

        if len(exact_top_five) == TOP_K:
            return [
                sentences[sentence_id]
                for sentence_id
                in exact_top_five
            ]

    # If fewer than 5 exact short matches
    # exist, we cannot safely ignore
    # corrected matches.
    #
    # Therefore preserve the old
    # full-corpus fallback.
    if (
        len(normalized_query)
        < MIN_VARIANT_SEARCH_QUERY_LENGTH
    ):
        return list(sentences)

    # Queries of length 4-5.
    if (
        len(normalized_query)
        < MIN_SAFE_QUERY_LENGTH
    ):
        candidate_ids = (
            _short_query_candidate_ids(
                normalized_query,
                index,
            )
        )

        return [
            sentences[sentence_id]
            for sentence_id
            in candidate_ids
        ]

    # Queries of length 6+.
    query_trigrams = generate_trigrams(
        normalized_query
    )

    selected_trigrams = sorted(
        query_trigrams,
        key=lambda trigram: len(
            index.get(
                trigram,
                (),
            )
        ),
    )[:MAX_FILTER_TRIGRAMS]

    candidate_ids: Set[int] = set()

    for trigram in selected_trigrams:
        candidate_ids.update(
            index.get(
                trigram,
                set(),
            )
        )

    return [
        sentences[sentence_id]
        for sentence_id
        in candidate_ids
    ]