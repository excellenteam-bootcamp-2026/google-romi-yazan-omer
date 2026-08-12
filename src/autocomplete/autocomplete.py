from heapq import nsmallest
from typing import Dict, Iterator, List, Optional, Set

from src.loader.index import get_candidates
from src.loader.normalizer import normalize_text
from src.matching.matcher import calculate_score
from src.models import AutoCompleteData, Sentence


SHORT_EXACT_QUERY_LENGTH = 3

_sentences: Optional[List[Sentence]] = None
_index: Optional[Dict[str, Set[int]]] = None


def initialize(
    sentences: List[Sentence],
    index: Dict[str, Set[int]],
) -> None:
    """
    Store the sentences and index for future searches.

    This function must be called once after loading the sentences
    and building the trigram index.
    """
    global _sentences, _index

    _sentences = sentences
    _index = index


def _rank_candidates(
    query: str,
    candidates: List[Sentence],
) -> List[AutoCompleteData]:
    """Score candidates and return the five best completions."""
    normalized_query = normalize_text(query)

    def valid_completions() -> Iterator[AutoCompleteData]:
        for candidate in candidates:
            score = calculate_score(
                normalized_query,
                candidate,
            )

            if score is None:
                continue

            yield AutoCompleteData(
                completed_sentence=candidate.text,
                source_text=candidate.source,
                offset=candidate.offset,
                score=score,
            )

    return nsmallest(
        5,
        valid_completions(),
        key=lambda completion: (
            -completion.score,
            completion.completed_sentence,
        ),
    )


def _get_short_exact_completions(
    query: str,
    sentences: List[Sentence],
    index: Dict[str, Set[int]],
) -> Optional[List[AutoCompleteData]]:
    """
    Return five exact results for a short query.

    If fewer than five exact matches exist, return None so the
    complete approximate-matching algorithm can be used.
    """
    if not query:
        return None

    if len(query) > SHORT_EXACT_QUERY_LENGTH:
        return None

    # For a three-character query, use the trigram index.
    if len(query) == SHORT_EXACT_QUERY_LENGTH:
        sentence_pool = (
            sentences[sentence_id]
            for sentence_id in index.get(query, set())
        )
    else:
        # Length 1-2: Python's substring search is much faster
        # than running the approximate matcher on every sentence.
        sentence_pool = iter(sentences)

    exact_sentences = nsmallest(
        5,
        (
            sentence
            for sentence in sentence_pool
            if query in sentence.normalized_text
        ),
        key=lambda sentence: sentence.text,
    )

    # Approximate results may be needed to complete the Top 5.
    if len(exact_sentences) < 5:
        return None

    exact_score = 2 * len(query)

    return [
        AutoCompleteData(
            completed_sentence=sentence.text,
            source_text=sentence.source,
            offset=sentence.offset,
            score=exact_score,
        )
        for sentence in exact_sentences
    ]


def get_best_k_completions(
    prefix: str,
) -> List[AutoCompleteData]:
    """
    Return the five best completions for the given prefix.

    initialize() must be called before this function.
    """
    if _sentences is None or _index is None:
        raise RuntimeError(
            "get_best_k_completions() called before initialize(); "
            "call autocomplete.initialize(sentences, index) "
            "once at startup."
        )

    normalized_prefix = normalize_text(prefix)

    if not normalized_prefix:
        return []

    # Fast path for queries containing one to three characters.
    exact_completions = _get_short_exact_completions(
        normalized_prefix,
        _sentences,
        _index,
    )

    if exact_completions is not None:
        return exact_completions

    # General path for longer queries or when fewer than five
    # exact short-query matches were found.
    candidates = get_candidates(
        prefix,
        _sentences,
        _index,
    )

    return _rank_candidates(
        prefix,
        candidates,
    )