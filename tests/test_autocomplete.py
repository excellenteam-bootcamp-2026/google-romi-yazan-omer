import unittest
from unittest.mock import patch

from src.autocomplete import autocomplete
from src.autocomplete.autocomplete import _rank_candidates, get_best_k_completions
from src.models import Sentence


class TestRankCandidates(unittest.TestCase):
    """Tests for the internal scoring/ranking helper (candidates passed in directly)."""

    def test_returns_matching_candidate(self):
        candidate = Sentence(
            text="Python is a programming language.",
            normalized_text="python is a programming language",
            source="python.txt",
            offset=15,
        )

        with patch(
            "src.autocomplete.autocomplete.calculate_score",
            return_value=24,
        ):
            results = _rank_candidates("Python", [candidate])

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].completed_sentence,
            "Python is a programming language.",
        )
        self.assertEqual(results[0].source_text, "python.txt")
        self.assertEqual(results[0].offset, 15)
        self.assertEqual(results[0].score, 24)

    def test_filters_sorts_and_returns_only_five(self):
        candidates = [
            Sentence("Zulu", "zulu", "test.txt", 1),
            Sentence("Beta", "beta", "test.txt", 2),
            Sentence("Alpha", "alpha", "test.txt", 3),
            Sentence("Gamma", "gamma", "test.txt", 4),
            Sentence("Delta", "delta", "test.txt", 5),
            Sentence("Epsilon", "epsilon", "test.txt", 6),
            Sentence("Ignored", "ignored", "test.txt", 7),
        ]

        scores = {
            "Zulu": 10,
            "Beta": 20,
            "Alpha": 20,
            "Gamma": 18,
            "Delta": 16,
            "Epsilon": 14,
            "Ignored": None,
        }

        def fake_calculate_score(query, candidate):
            return scores[candidate.text]

        with patch(
            "src.autocomplete.autocomplete.calculate_score",
            side_effect=fake_calculate_score,
        ) as matcher:
            results = _rank_candidates("query", candidates)

        self.assertEqual(
            [result.completed_sentence for result in results],
            ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
        )
        self.assertEqual(matcher.call_count, len(candidates))

    def test_returns_empty_list_when_there_are_no_candidates(self):
        with patch(
            "src.autocomplete.autocomplete.calculate_score"
        ) as matcher:
            results = _rank_candidates("query", [])

        self.assertEqual(results, [])
        matcher.assert_not_called()


class TestGetBestKCompletions(unittest.TestCase):
    """Tests for the public Stage-A contract: get_best_k_completions(prefix) -> List[AutoCompleteData]."""

    def setUp(self):
        self.addCleanup(autocomplete.initialize, None, None)

    def test_raises_if_called_before_initialize(self):
        autocomplete.initialize(None, None)

        with self.assertRaises(RuntimeError):
            get_best_k_completions("python")

    def test_does_not_reload_sentences_or_rebuild_index(self):
        sentence = Sentence(
            text="Python is a programming language.",
            normalized_text="python is a programming language",
            source="python.txt",
            offset=1,
        )
        autocomplete.initialize([sentence], {"pyt": {0}})

        with patch("src.loader.data_loader.load_sentences") as load_mock, \
             patch("src.loader.index.build_index") as build_mock:
            get_best_k_completions("python")

        load_mock.assert_not_called()
        build_mock.assert_not_called()

    def test_uses_initialized_sentences_and_index_end_to_end(self):
        sentence = Sentence(
            text="Python is a programming language.",
            normalized_text="python is a programming language",
            source="python.txt",
            offset=1,
        )
        other = Sentence(
            text="Completely unrelated sentence.",
            normalized_text="completely unrelated sentence",
            source="other.txt",
            offset=1,
        )
        from src.loader.index import build_index

        autocomplete.initialize([sentence, other], build_index([sentence, other]))

        results = get_best_k_completions("PYTHON!!")

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].completed_sentence,
            "Python is a programming language.",
        )
        self.assertEqual(results[0].source_text, "python.txt")
        self.assertEqual(results[0].offset, 1)


class TestShortExactQueryFastPath(unittest.TestCase):
    """Tests for the 1-3 character exact-match fast path in get_best_k_completions."""

    def setUp(self):
        self.addCleanup(autocomplete.initialize, None, None)

    def _init(self, sentences):
        from src.loader.index import build_index
        autocomplete.initialize(sentences, build_index(sentences))

    def test_length_two_query_returns_exact_matches_sorted_alphabetically(self):
        sentences = [
            Sentence(
                text=f"Sentence {chr(69 - i)} about python topic {i}.",
                normalized_text=f"sentence {chr(101 - i)} about python topic {i}",
                source="f.txt",
                offset=i + 1,
            )
            for i in range(5)
        ]
        self._init(sentences)

        results = get_best_k_completions("py")

        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.score == 4 for r in results))
        self.assertEqual(
            [r.completed_sentence for r in results],
            sorted(r.completed_sentence for r in results),
        )

    def test_length_three_query_uses_trigram_index(self):
        sentences = [
            Sentence(
                text=f"Sentence {chr(65 + i)} about python topic {i}.",
                normalized_text=f"sentence {chr(97 + i)} about python topic {i}",
                source="f.txt",
                offset=i + 1,
            )
            for i in range(5)
        ]
        self._init(sentences)

        results = get_best_k_completions("pyt")

        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.score == 6 for r in results))

    def test_falls_back_to_approximate_matching_when_fewer_than_five_exact(self):
        sentences = [
            Sentence(
                text="Alpha python one.",
                normalized_text="alpha python one",
                source="f.txt",
                offset=1,
            ),
            Sentence(
                text="Beta python two.",
                normalized_text="beta python two",
                source="f.txt",
                offset=2,
            ),
            Sentence(
                # "puthon" is one substitution away from "python" ("py" -> "pu").
                text="Gamma puthon typo.",
                normalized_text="gamma puthon typo",
                source="f.txt",
                offset=3,
            ),
            Sentence(
                text="Delta unrelated.",
                normalized_text="delta unrelated",
                source="f.txt",
                offset=4,
            ),
        ]
        self._init(sentences)

        results = get_best_k_completions("py")

        self.assertEqual(
            [r.completed_sentence for r in results],
            ["Alpha python one.", "Beta python two.", "Gamma puthon typo."],
        )
        self.assertEqual(results[0].score, 4)
        self.assertEqual(results[1].score, 4)
        self.assertLess(results[2].score, 4)

    def test_empty_or_punctuation_only_query_returns_empty_list(self):
        sentences = [
            Sentence(
                text="Hello world.",
                normalized_text="hello world",
                source="f.txt",
                offset=1,
            ),
        ]
        self._init(sentences)

        self.assertEqual(get_best_k_completions(""), [])
        self.assertEqual(get_best_k_completions("..."), [])

    def test_matches_general_pipeline_result_exactly(self):
        from src.loader.index import build_index, get_candidates
        from src.autocomplete.autocomplete import _rank_candidates

        sentences = [
            Sentence(
                text=f"Sentence {chr(65 + i)} about python topic {i}.",
                normalized_text=f"sentence {chr(97 + i)} about python topic {i}",
                source="f.txt",
                offset=i + 1,
            )
            for i in range(5)
        ]
        index = build_index(sentences)

        slow_path = _rank_candidates(
            "py", get_candidates("py", sentences, index)
        )

        self._init(sentences)
        fast_path = get_best_k_completions("py")

        self.assertEqual(fast_path, slow_path)


if __name__ == "__main__":
    unittest.main()
