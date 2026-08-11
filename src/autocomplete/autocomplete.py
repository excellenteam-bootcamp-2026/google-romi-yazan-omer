from heapq import nsmallest
from typing import Iterator, List

from src.matching.matcher import calculate_score
from src.models import AutoCompleteData, Sentence


def get_best_completions(
    query: str,
    sentences: List[Sentence],
) -> List[AutoCompleteData]:
    """Return the top 5 matches, ranked by score desc, then alphabetically."""

    def matching_completions() -> Iterator[AutoCompleteData]:
        for sentence in sentences:
            score = calculate_score(query, sentence)

            if score is None:
                continue

            yield AutoCompleteData(
                completed_sentence=sentence.text,
                source_text=sentence.source,
                offset=sentence.offset,
                score=score,
            )

    return nsmallest(
        5,
        matching_completions(),
        key=lambda completion: (
            -completion.score,
            completion.completed_sentence,
        ),
    )