from dataclasses import dataclass


@dataclass
class Sentence:
    """One line of source text, as produced by the loader."""
    text: str
    normalized_text: str
    source: str
    offset: int


@dataclass
class AutoCompleteData:
    """One ranked completion, as returned by the autocomplete layer."""
    completed_sentence: str
    source_text: str
    offset: int
    score: int
