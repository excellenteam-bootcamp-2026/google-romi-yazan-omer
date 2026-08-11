import unittest

from src.matching.matcher import calculate_score
from src.matching.normalizer import normalize_text
from src.models import Sentence

SENTENCE = Sentence(
    text="To be or not to be, that is the question.",
    source="test.txt",
    offset=1,
)


class TestNormalizeText(unittest.TestCase):
    def test_lowercases_and_strips_punctuation(self):
        self.assertEqual(normalize_text("To be, that IS!"), "to be that is")

    def test_collapses_extra_spaces(self):
        self.assertEqual(normalize_text("  hello   world  "), "hello world")


class TestCalculateScore(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(calculate_score("To be", SENTENCE), 10)

    def test_exact_match_ignoring_case(self):
        self.assertEqual(calculate_score("or Not", SENTENCE), 12)

    def test_exact_match_ignoring_punctuation(self):
        self.assertEqual(calculate_score("be, that", SENTENCE), 14)

    def test_one_substitution(self):
        self.assertEqual(calculate_score("2o be", SENTENCE), 5)
        self.assertEqual(calculate_score("to pe", SENTENCE), 8)

    def test_one_insertion_or_deletion(self):
        self.assertEqual(calculate_score("or knot", SENTENCE), 8)

    def test_no_match_when_more_than_one_correction_needed(self):
        self.assertIsNone(calculate_score("not be", SENTENCE))


if __name__ == "__main__":
    unittest.main()
