import unittest
from unittest.mock import patch

from src.autocomplete.autocomplete import get_best_completions
from src.models import Sentence


class TestAutocomplete(unittest.TestCase):
    def test_returns_matching_candidate(self):
        candidate = Sentence(
            text="Python is a programming language.",
            source="python.txt",
            offset=15,
        )

        with patch(
            "src.autocomplete.autocomplete.calculate_score",
            return_value=24,
        ):
            results = get_best_completions("Python", [candidate])

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
            Sentence("Zulu", "test.txt", 1),
            Sentence("Beta", "test.txt", 2),
            Sentence("Alpha", "test.txt", 3),
            Sentence("Gamma", "test.txt", 4),
            Sentence("Delta", "test.txt", 5),
            Sentence("Epsilon", "test.txt", 6),
            Sentence("Ignored", "test.txt", 7),
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
            results = get_best_completions("query", candidates)

        self.assertEqual(
            [result.completed_sentence for result in results],
            ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
        )
        self.assertEqual(matcher.call_count, len(candidates))

    def test_returns_empty_list_when_there_are_no_candidates(self):
        with patch(
            "src.autocomplete.autocomplete.calculate_score"
        ) as matcher:
            results = get_best_completions("query", [])

        self.assertEqual(results, [])
        matcher.assert_not_called()


if __name__ == "__main__":
    unittest.main()