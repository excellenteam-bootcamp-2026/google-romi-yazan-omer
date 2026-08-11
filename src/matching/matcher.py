from typing import Optional

from src.matching.normalizer import normalize_text
from src.models import Sentence

_SUBSTITUTION_PENALTIES = {1: 5, 2: 4, 3: 3, 4: 2}
_SUBSTITUTION_PENALTY_DEFAULT = 1

_INDEL_PENALTIES = {1: 10, 2: 8, 3: 6, 4: 4}
_INDEL_PENALTY_DEFAULT = 2


def _substitution_penalty(position: int) -> int:
    return _SUBSTITUTION_PENALTIES.get(position, _SUBSTITUTION_PENALTY_DEFAULT)


def _indel_penalty(position: int) -> int:
    return _INDEL_PENALTIES.get(position, _INDEL_PENALTY_DEFAULT)


def _score_same_length(query: str, window: str) -> Optional[int]:
    mismatches = [i for i in range(len(query)) if query[i] != window[i]]
    if len(mismatches) > 1:
        return None
    base = 2 * len(query)
    if not mismatches:
        return base
    position = mismatches[0] + 1
    return base - _substitution_penalty(position)


def _score_one_apart(shorter: str, longer: str) -> Optional[int]:
    i = j = 0
    diff_position = None
    while i < len(shorter) and j < len(longer):
        if shorter[i] == longer[j]:
            i += 1
            j += 1
        elif diff_position is None:
            diff_position = j + 1
            j += 1
        else:
            return None
    if diff_position is None:
        diff_position = j + 1
    base = 2 * len(shorter)
    return base - _indel_penalty(diff_position)


def calculate_score(query: str, sentence: Sentence) -> Optional[int]:
    normalized_query = normalize_text(query)
    normalized_sentence = normalize_text(sentence.text)
    query_len = len(normalized_query)

    best_score = None
    for start in range(len(normalized_sentence)):
        same = normalized_sentence[start:start + query_len]
        longer = normalized_sentence[start:start + query_len + 1]
        shorter = normalized_sentence[start:start + query_len - 1]

        candidates = []
        if len(same) == query_len:
            candidates.append(_score_same_length(normalized_query, same))
        if len(longer) == query_len + 1:
            candidates.append(_score_one_apart(normalized_query, longer))
        if query_len > 1 and len(shorter) == query_len - 1:
            candidates.append(_score_one_apart(shorter, normalized_query))

        for score in candidates:
            if score is not None and (best_score is None or score > best_score):
                best_score = score

    return best_score
