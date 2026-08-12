from typing import Dict, List, Set

from src.loader.normalizer import normalize_text
from src.models import Sentence


TRIGRAM_SIZE = 3
MIN_SAFE_QUERY_LENGTH = 2 * TRIGRAM_SIZE

def generate_trigrams(text: str) -> Set[str]:
    """
    Generate all unique character trigrams from normalized text.

    Example:
        "python" -> {"pyt", "yth", "tho", "hon"}

    The input is expected to already be normalized.

    If the text contains fewer than 3 characters,
    no trigram can be created and an empty set is returned.

    Time complexity: O(n)
    Space complexity: O(n)

    where n is the length of the input text.
    """
    if len(text) < TRIGRAM_SIZE:
        return set()

    return {
        text[i:i + TRIGRAM_SIZE]
        for i in range(len(text) - TRIGRAM_SIZE + 1)
    }


def build_index(sentences: List[Sentence]) -> Dict[str, Set[int]]:
    """
    Build a trigram inverted index from normalized sentences.

    Each trigram maps to the IDs of sentences containing that trigram.
    A sentence ID is its position in the sentences list.

    Example:
        index["pyt"] = {1, 4, 20}

    means that the trigram "pyt" appears in sentences
    with IDs 1, 4, and 20.

    Time complexity: O(T)
    Space complexity: O(T)

    where T is the total number of characters in all normalized sentences.
    """
    index: Dict[str, Set[int]] = {}

    for sentence_id, sentence in enumerate(sentences):
        trigrams = generate_trigrams(sentence.normalized_text)

        for trigram in trigrams:
            if trigram not in index:
                index[trigram] = set()

            index[trigram].add(sentence_id)

    return index


def get_candidates(
    query: str,
    sentences: List[Sentence],
    index: Dict[str, Set[int]],
) -> List[Sentence]:
    """
    Return candidate sentences that may match the user's query.

    The query is normalized before searching.

    For normalized queries shorter than 6 characters, trigram filtering
    cannot safely guarantee that a valid one-edit match will retain a
    common trigram, so all sentences are returned as candidates.

    For queries of length 6 or more, candidate sentence IDs are collected
    from the union of all matching trigram posting lists.

    This function only retrieves candidates.
    Final match validation and scoring are handled by the matching layer.

    Time complexity for indexed lookup:
        O(m + P + C)

    where:
        m = normalized query length
        P = total posting entries examined
        C = number of candidate sentences returned
    """
    normalized_query = normalize_text(query)

    # For short queries, trigram filtering is not safe enough for
    # one-edit matching, so return all sentences as candidates.
    if len(normalized_query) < MIN_SAFE_QUERY_LENGTH:
        return list(sentences)

    query_trigrams = generate_trigrams(normalized_query)

    candidate_ids: Set[int] = set()

    for trigram in query_trigrams:
        candidate_ids.update(index.get(trigram, set()))

    return [
        sentences[sentence_id]
        for sentence_id in candidate_ids
    ]
