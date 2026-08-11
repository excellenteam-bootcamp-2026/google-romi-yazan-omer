import unittest

from src.matching.matcher import calculate_score
from src.models import Sentence

SENTENCE = Sentence(
    text="To be or not to be, that is the question.",
    normalized_text="to be or not to be that is the question",
    source="test.txt",
    offset=1,
)


class TestCalculateScore(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(calculate_score("to be", SENTENCE), 10)

    def test_exact_match_mid_sentence(self):
        self.assertEqual(calculate_score("or not", SENTENCE), 12)

    def test_exact_match_spanning_removed_punctuation(self):
        self.assertEqual(calculate_score("be that", SENTENCE), 14)

    def test_one_substitution(self):
        self.assertEqual(calculate_score("2o be", SENTENCE), 5)
        self.assertEqual(calculate_score("to pe", SENTENCE), 8)

    def test_one_insertion_or_deletion(self):
        self.assertEqual(calculate_score("or knot", SENTENCE), 8)

    def test_no_match_when_more_than_one_correction_needed(self):
        self.assertIsNone(calculate_score("not be", SENTENCE))
        self.assertIsNone(calculate_score("abc", Sentence(
            text="axy", normalized_text="axy", source="test.txt", offset=1,
        )))


if __name__ == "__main__":
    unittest.main()
