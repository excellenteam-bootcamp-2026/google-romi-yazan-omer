from heapq import nsmallest
from typing import Iterator, List

from src.loader.normalizer import normalize_text
from src.matching.matcher import calculate_score
from src.models import AutoCompleteData, Sentence


def get_best_completions(
    query: str,
    candidates: List[Sentence],
) -> List[AutoCompleteData]:
    """Score candidate sentences and return the five best completions."""
    normalized_query = normalize_text(query)

    def valid_completions() -> Iterator[AutoCompleteData]:
        for candidate in candidates:
            score = calculate_score(normalized_query, candidate)

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