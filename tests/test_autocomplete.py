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


if __name__ == "__main__":
    unittest.main()
