import string
from collections import defaultdict
from typing import Dict, List, Set

from src.loader.normalizer import normalize_text
from src.models import Sentence


TRIGRAM_SIZE = 3
MIN_SAFE_QUERY_LENGTH = 6
MAX_FILTER_TRIGRAMS = 4
NORMALIZED_ALPHABET = string.ascii_lowercase + string.digits + " "


def generate_trigrams(text: str) -> Set[str]:
    """Return all unique trigrams in text."""
    if len(text) < TRIGRAM_SIZE:
        return set()

    return {
        text[i:i + TRIGRAM_SIZE]
        for i in range(len(text) - TRIGRAM_SIZE + 1)
    }


def build_index(sentences: List[Sentence]) -> Dict[str, Set[int]]:
    """Build a trigram inverted index."""
    index: Dict[str, Set[int]] = defaultdict(set)

    for sentence_id, sentence in enumerate(sentences):
        trigrams = generate_trigrams(sentence.normalized_text)

        for trigram in trigrams:
            index[trigram].add(sentence_id)

    return dict(index)


def _generate_one_edit_variants(text: str) -> Set[str]:
    """Generate strings within at most one edit from text."""
    variants = {text}

    for position, original_character in enumerate(text):
        # Deletion
        variants.add(
            text[:position] + text[position + 1:]
        )

        # Substitution
        for replacement in NORMALIZED_ALPHABET:
            if replacement != original_character:
                variants.add(
                    text[:position]
                    + replacement
                    + text[position + 1:]
                )

    # Insertion
    for position in range(len(text) + 1):
        for inserted_character in NORMALIZED_ALPHABET:
            variants.add(
                text[:position]
                + inserted_character
                + text[position:]
            )

    return variants


def _exact_variant_candidate_ids(
    variant: str,
    index: Dict[str, Set[int]],
) -> Set[int]:
    """Find sentences that contain every trigram of a variant."""
    trigrams = generate_trigrams(variant)

    if not trigrams:
        return set()

    postings = []

    for trigram in trigrams:
        posting = index.get(trigram)

        if not posting:
            return set()

        postings.append(posting)

    # Start with the smallest posting list.
    postings.sort(key=len)
    candidate_ids = postings[0].copy()

    for posting in postings[1:]:
        candidate_ids.intersection_update(posting)

        if not candidate_ids:
            break

    return candidate_ids


def _short_query_candidate_ids(
    query: str,
    index: Dict[str, Set[int]],
) -> Set[int]:
    """Find candidates for a query of length four or five."""
    candidate_ids: Set[int] = set()

    for variant in _generate_one_edit_variants(query):
        candidate_ids.update(
            _exact_variant_candidate_ids(variant, index)
        )

    return candidate_ids


def get_candidates(
    query: str,
    sentences: List[Sentence],
    index: Dict[str, Set[int]],
) -> List[Sentence]:
    """Return candidates without performing final scoring."""
    normalized_query = normalize_text(query)

    # Too short to form even one trigram (length 1-2): must scan everything.
    if len(normalized_query) < TRIGRAM_SIZE:
        return list(sentences)

    # Length 3: the query IS one trigram, so look it up directly.
    if len(normalized_query) == TRIGRAM_SIZE:
        candidate_ids = index.get(normalized_query, set())

        return [
            sentences[sentence_id]
            for sentence_id in candidate_ids
        ]

    # Queries of length 4-5 use all one-edit variants.
    if len(normalized_query) < MIN_SAFE_QUERY_LENGTH:
        candidate_ids = _short_query_candidate_ids(
            normalized_query,
            index,
        )

        return [
            sentences[sentence_id]
            for sentence_id in candidate_ids
        ]

    # One edit can damage at most three neighboring trigrams.
    # Therefore, at least one of four different trigrams survives.
    query_trigrams = generate_trigrams(normalized_query)

    selected_trigrams = sorted(
        query_trigrams,
        key=lambda trigram: len(index.get(trigram, ())),
    )[:MAX_FILTER_TRIGRAMS]

    candidate_ids: Set[int] = set()

    for trigram in selected_trigrams:
        candidate_ids.update(
            index.get(trigram, set())
        )

    return [
        sentences[sentence_id]
        for sentence_id in candidate_ids
    ]