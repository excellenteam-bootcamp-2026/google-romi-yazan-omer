import unittest

from src.loader.index import (
    build_index,
    generate_trigrams,
    get_candidates,
)
from src.models import Sentence


class TestTrigramGeneration(unittest.TestCase):

    def test_generates_trigrams(self):
        trigrams = generate_trigrams("python")

        self.assertEqual(
            trigrams,
            {"pyt", "yth", "tho", "hon"},
        )

    def test_exactly_three_characters(self):
        trigrams = generate_trigrams("abc")

        self.assertEqual(
            trigrams,
            {"abc"},
        )

    def test_returns_empty_set_for_two_characters(self):
        self.assertEqual(
            generate_trigrams("ab"),
            set(),
        )

    def test_returns_empty_set_for_one_character(self):
        self.assertEqual(
            generate_trigrams("a"),
            set(),
        )

    def test_returns_empty_set_for_empty_string(self):
        self.assertEqual(
            generate_trigrams(""),
            set(),
        )

    def test_does_not_duplicate_same_trigram(self):
        trigrams = generate_trigrams("aaaa")

        self.assertEqual(
            trigrams,
            {"aaa"},
        )

    def test_trigrams_can_contain_spaces(self):
        trigrams = generate_trigrams("a bc")

        self.assertEqual(
            trigrams,
            {"a b", " bc"},
        )

    def test_longer_text_generates_correct_number_of_trigrams(self):
        trigrams = generate_trigrams("abcdef")

        self.assertEqual(
            trigrams,
            {"abc", "bcd", "cde", "def"},
        )


class TestBuildIndex(unittest.TestCase):

    def test_maps_trigram_to_correct_sentence_id(self):
        sentences = [
            Sentence(
                text="Hello world.",
                normalized_text="hello world",
                source="test.txt",
                offset=1,
            ),
            Sentence(
                text="Python language.",
                normalized_text="python language",
                source="test.txt",
                offset=2,
            ),
        ]

        index = build_index(sentences)

        self.assertEqual(
            index["pyt"],
            {1},
        )

    def test_shared_trigram_maps_to_multiple_sentence_ids(self):
        sentences = [
            Sentence(
                text="To be or not to be.",
                normalized_text="to be or not to be",
                source="first.txt",
                offset=1,
            ),
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="second.txt",
                offset=1,
            ),
            Sentence(
                text="This is not gold.",
                normalized_text="this is not gold",
                source="third.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        self.assertEqual(
            index["not"],
            {0, 2},
        )

    def test_does_not_duplicate_sentence_id(self):
        sentences = [
            Sentence(
                text="AAAA.",
                normalized_text="aaaa",
                source="test.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        self.assertEqual(
            index["aaa"],
            {0},
        )

    def test_sentence_shorter_than_three_characters_is_not_indexed(self):
        sentences = [
            Sentence(
                text="Hi",
                normalized_text="hi",
                source="test.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        self.assertEqual(
            index,
            {},
        )

    def test_empty_sentence_list_returns_empty_index(self):
        index = build_index([])

        self.assertEqual(
            index,
            {},
        )


class TestGetCandidates(unittest.TestCase):

    def setUp(self):
        self.sentences = [
            Sentence(
                text="Python language is useful.",
                normalized_text="python language is useful",
                source="first.txt",
                offset=1,
            ),
            Sentence(
                text="Information about writing a good bug report.",
                normalized_text="information about writing a good bug report",
                source="second.txt",
                offset=1,
            ),
            Sentence(
                text="All that glitters is not gold.",
                normalized_text="all that glitters is not gold",
                source="third.txt",
                offset=1,
            ),
        ]

        self.index = build_index(self.sentences)

    def test_returns_candidate_for_matching_query(self):
        candidates = get_candidates(
            "python",
            self.sentences,
            self.index,
        )

        self.assertIn(
            self.sentences[0],
            candidates,
        )

    def test_normalizes_query_before_searching(self):
        candidates = get_candidates(
            "PYTHON,",
            self.sentences,
            self.index,
        )

        self.assertIn(
            self.sentences[0],
            candidates,
        )

    def test_returns_multiple_relevant_candidates(self):
        sentences = [
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="first.txt",
                offset=1,
            ),
            Sentence(
                text="Python is popular.",
                normalized_text="python is popular",
                source="second.txt",
                offset=1,
            ),
            Sentence(
                text="Completely unrelated.",
                normalized_text="completely unrelated",
                source="third.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        candidates = get_candidates(
            "python",
            sentences,
            index,
        )

        self.assertIn(sentences[0], candidates)
        self.assertIn(sentences[1], candidates)

    def test_short_query_falls_back_to_all_sentences(self):
        candidates = get_candidates(
            "py",
            self.sentences,
            self.index,
        )

        self.assertEqual(
            len(candidates),
            len(self.sentences),
        )

        self.assertEqual(
            set(sentence.text for sentence in candidates),
            set(sentence.text for sentence in self.sentences),
        )

    def test_empty_query_falls_back_to_all_sentences(self):
        candidates = get_candidates(
            "",
            self.sentences,
            self.index,
        )

        self.assertEqual(
            len(candidates),
            len(self.sentences),
        )

    def test_long_query_with_no_shared_trigrams_returns_no_candidates(self):
        candidates = get_candidates(
            "zzzzzzzz",
            self.sentences,
            self.index,
        )

        self.assertEqual(
            candidates,
            [],
        )

    def test_uses_union_not_intersection(self):
        sentences = [
            Sentence(
                text="Python language.",
                normalized_text="python language",
                source="test.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        candidates = get_candidates(
            "python",
            sentences,
            index,
        )

        self.assertIn(
            sentences[0],
            candidates,
        )

    def test_exact_match_is_not_lost_by_index(self):
        sentences = [
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="test.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        candidates = get_candidates(
            "python",
            sentences,
            index,
        )

        self.assertIn(sentences[0], candidates)

    def test_one_substitution_candidate_is_not_lost(self):
        sentences = [
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="test.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        # "pythxn" differs from "python" by one substitution.
        candidates = get_candidates(
            "pythxn",
            sentences,
            index,
        )

        self.assertIn(sentences[0], candidates)

    def test_extra_query_character_candidate_is_not_lost(self):
        sentences = [
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="test.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        # Extra "x" was inserted into the query.
        candidates = get_candidates(
            "pythxon",
            sentences,
            index,
        )

        self.assertIn(sentences[0], candidates)

    def test_missing_query_character_candidate_is_not_lost(self):
        sentences = [
            Sentence(
                text="Pythonx is useful.",
                normalized_text="pythonx is useful",
                source="test.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        # "pytonx" is missing the "h" from "pythonx".
        # Length is 6, so this actually exercises the trigram index,
        # rather than the short-query fallback.
        candidates = get_candidates(
            "pytonx",
            sentences,
            index,
        )

        self.assertIn(sentences[0], candidates)

    def test_five_character_one_edit_query_uses_index_without_losing_match(self):
        sentences = [
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="test.txt",
                offset=1,
            ),
            Sentence(
                text="Completely unrelated.",
                normalized_text="completely unrelated",
                source="other.txt",
                offset=1,
            ),
        ]

        index = build_index(sentences)

        # "pyton" is missing one character from "python".
        candidates = get_candidates(
            "pyton",
            sentences,
            index,
        )

        # Preserve the valid one-edit match.
        self.assertIn(sentences[0], candidates)

        # Filter the unrelated sentence.
        self.assertNotIn(sentences[1], candidates)

    def test_three_character_query_uses_trigram_index_directly(self):
        sentences = [
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="first.txt",
                offset=1,
            ),
            Sentence(
                text="Completely unrelated.",
                normalized_text="completely unrelated",
                source="second.txt",
                offset=1,
            ),
        ]
        index = build_index(sentences)

        # "pyt" is itself a single trigram, so this should narrow via a
        # direct index lookup rather than falling back to every sentence.
        candidates = get_candidates("pyt", sentences, index)

        self.assertIn(sentences[0], candidates)
        self.assertNotIn(sentences[1], candidates)
        self.assertLess(len(candidates), len(sentences))

    def test_three_character_query_with_no_match_returns_no_candidates(self):
        sentences = [
            Sentence(
                text="Python is useful.",
                normalized_text="python is useful",
                source="first.txt",
                offset=1,
            ),
        ]
        index = build_index(sentences)

        candidates = get_candidates("zzz", sentences, index)

        self.assertEqual(candidates, [])

    def test_long_query_survivor_trigram_is_not_lost_even_when_common(self):
        """
        Adversarial regression test for the length>=6 rare-trigram selection.

        A single edit can break at most 3 of a query's trigrams, so at
        least N-3 always survive unedited (where N is the number of
        distinct trigrams). The algorithm only keeps the MAX_FILTER_TRIGRAMS
        (4) trigrams with the smallest posting lists, dropping N-4. Since
        N-4 < N-3 always, it is mathematically impossible for every
        surviving trigram to be excluded -- but this test proves it by
        deliberately flooding the *surviving* trigrams with huge posting
        lists (so the "smallest posting" heuristic would naturally want to
        drop them first) and confirming the true match is still found.
        """
        query = "abcdefghij"
        # One substitution at position 6 (1-indexed): 'f' -> 'X'.
        target_substring = "abcdeXghij"

        # Trigrams of "abcdefghij" NOT touching the edited position (index 5):
        # 'abc', 'bcd', 'cde' (before it) and 'ghi', 'hij' (after it).
        surviving_trigrams = ["abc", "bcd", "cde", "ghi", "hij"]

        noise_sentences = []
        for i, trigram in enumerate(surviving_trigrams):
            for j in range(20):
                noise_sentences.append(
                    Sentence(
                        text="noise",
                        normalized_text=f"zz{trigram}zz sentence number {i} {j}",
                        source="noise.txt",
                        offset=1,
                    )
                )

        target = Sentence(
            text="TARGET",
            normalized_text=f"xx {target_substring} yy",
            source="target.txt",
            offset=1,
        )

        sentences = noise_sentences + [target]
        index = build_index(sentences)

        candidates = get_candidates(query, sentences, index)

        self.assertIn(target, candidates)


if __name__ == "__main__":
    unittest.main()
