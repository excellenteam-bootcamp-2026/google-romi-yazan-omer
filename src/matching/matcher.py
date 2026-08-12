from typing import Optional

from src.models import Sentence


_SUBSTITUTION_PENALTIES = {
    1: 5,
    2: 4,
    3: 3,
    4: 2,
}
_SUBSTITUTION_PENALTY_DEFAULT = 1

_INDEL_PENALTIES = {
    1: 10,
    2: 8,
    3: 6,
    4: 4,
}
_INDEL_PENALTY_DEFAULT = 2


def _substitution_penalty(position: int) -> int:
    return _SUBSTITUTION_PENALTIES.get(
        position,
        _SUBSTITUTION_PENALTY_DEFAULT,
    )


def _indel_penalty(position: int) -> int:
    return _INDEL_PENALTIES.get(
        position,
        _INDEL_PENALTY_DEFAULT,
    )


def _score_same_length_at(
    query: str,
    sentence: str,
    start: int,
) -> Optional[int]:
    """Check exact match or one substitution without slicing."""
    mismatch_position = None

    for index, query_character in enumerate(query):
        if query_character == sentence[start + index]:
            continue

        if mismatch_position is not None:
            return None

        mismatch_position = index + 1

    base_score = 2 * len(query)

    if mismatch_position is None:
        return base_score

    return base_score - _substitution_penalty(
        mismatch_position
    )


def _score_one_apart_at(
    shorter: str,
    shorter_start: int,
    longer: str,
    longer_start: int,
    shorter_length: int,
) -> Optional[int]:
    """Check one insertion or deletion without slicing."""
    shorter_index = 0
    longer_index = 0
    difference_position = None

    while (
        shorter_index < shorter_length
        and longer_index < shorter_length + 1
    ):
        shorter_character = shorter[
            shorter_start + shorter_index
        ]
        longer_character = longer[
            longer_start + longer_index
        ]

        if shorter_character == longer_character:
            shorter_index += 1
            longer_index += 1
        elif difference_position is None:
            difference_position = longer_index + 1
            longer_index += 1
        else:
            return None

    if difference_position is None:
        difference_position = longer_index + 1

    base_score = 2 * shorter_length
    return base_score - _indel_penalty(
        difference_position
    )


def calculate_score(
    query: str,
    sentence: Sentence,
) -> Optional[int]:
    """Return the best valid score, or None."""
    normalized_sentence = sentence.normalized_text
    query_length = len(query)

    if not query or not normalized_sentence:
        return None

    base_score = 2 * query_length

    # Fast path for an exact match.
    if query in normalized_sentence:
        return base_score

    best_score = None

    # Check one substitution.
    number_of_starts = (
        len(normalized_sentence) - query_length + 1
    )

    for start in range(max(0, number_of_starts)):
        score = _score_same_length_at(
            query,
            normalized_sentence,
            start,
        )

        if score is not None:
            if best_score is None or score > best_score:
                best_score = score

    # This is the highest score below an exact match.
    if best_score == base_score - 1:
        return best_score

    # Sentence window contains one extra character.
    number_of_starts = (
        len(normalized_sentence) - query_length
    )

    for start in range(max(0, number_of_starts)):
        score = _score_one_apart_at(
            query,
            0,
            normalized_sentence,
            start,
            query_length,
        )

        if score is not None:
            if best_score is None or score > best_score:
                best_score = score

    # This is the highest possible insertion/deletion score.
    if best_score == base_score - 2:
        return best_score

    # Query contains one extra character.
    if query_length > 1:
        shorter_length = query_length - 1
        number_of_starts = (
            len(normalized_sentence)
            - shorter_length
            + 1
        )

        for start in range(max(0, number_of_starts)):
            score = _score_one_apart_at(
                normalized_sentence,
                start,
                query,
                0,
                shorter_length,
            )

            if score is not None:
                if best_score is None or score > best_score:
                    best_score = score

    return best_score