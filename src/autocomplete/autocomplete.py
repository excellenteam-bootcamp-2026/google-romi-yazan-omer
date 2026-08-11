from typing import List

from src.matching.matcher import calculate_score
from src.models import AutoCompleteData, Sentence


def get_best_completions(
    query: str,
    sentences: List[Sentence]
) -> List[AutoCompleteData]:
    """Return the top 5 matches, ranked by score desc, then alphabetically."""
    completions = []

    for sentence in sentences:
        score = calculate_score(query, sentence)

        if score is None:
            continue

        completions.append(
            AutoCompleteData(
                completed_sentence=sentence.text,
                source_text=sentence.source,
                offset=sentence.offset,
                score=score,
            )
        )

    completions.sort(
        key=lambda completion: (
            -completion.score,
            completion.completed_sentence,
        )
    )

    return completions[:5]