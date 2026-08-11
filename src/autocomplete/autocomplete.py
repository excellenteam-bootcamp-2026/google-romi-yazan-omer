from typing import List

from src.models import AutoCompleteData, Sentence


def get_best_completions(query: str, sentences: List[Sentence]) -> List[AutoCompleteData]:
    """Return the top 5 matches, ranked by score desc, then alphabetically."""
    pass