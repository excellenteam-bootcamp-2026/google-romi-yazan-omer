from typing import Optional

from src.models import Sentence


def calculate_score(query: str, sentence: Sentence) -> Optional[int]:
    """Return the match score, or None if query does not match sentence."""
    pass