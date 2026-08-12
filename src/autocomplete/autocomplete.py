from heapq import nsmallest
from typing import Dict, Iterator, List, Optional, Set

from src.loader.index import get_candidates
from src.loader.normalizer import normalize_text
from src.matching.matcher import calculate_score
from src.models import AutoCompleteData, Sentence


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

    candidates = get_candidates(
        prefix,
        _sentences,
        _index,
    )

    return _rank_candidates(
        prefix,
        candidates,
    )