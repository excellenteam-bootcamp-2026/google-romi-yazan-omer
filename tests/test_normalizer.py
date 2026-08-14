import unittest

from src.loader.normalizer import normalize_text


class TestNormalizer(unittest.TestCase):

    def test_converts_to_lowercase(self):
        self.assertEqual(
            normalize_text("PYTHON"),
            "python",
        )

    def test_removes_punctuation(self):
        self.assertEqual(
            normalize_text("Hello, WORLD!!!"),
            "hello world",
        )

    def test_collapses_multiple_spaces(self):
        self.assertEqual(
            normalize_text("hello     world"),
            "hello world",
        )

    def test_handles_tabs_and_newlines_as_whitespace(self):
        self.assertEqual(
            normalize_text("hello\t\nworld"),
            "hello world",
        )

    def test_removes_leading_and_trailing_whitespace(self):
        self.assertEqual(
            normalize_text("   hello world   "),
            "hello world",
        )

    def test_combines_all_normalization_rules(self):
        self.assertEqual(
            normalize_text("   To   BE,   or NOT!   "),
            "to be or not",
        )

    def test_equivalent_inputs_produce_same_result(self):
        first = normalize_text("Be, that")
        second = normalize_text("BE     THAT")
        third = normalize_text("be that")

        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_preserves_digits(self):
        self.assertEqual(
            normalize_text("2o BE!"),
            "2o be",
        )

    def test_empty_string(self):
        self.assertEqual(
            normalize_text(""),
            "",
        )

    def test_only_punctuation_and_whitespace(self):
        self.assertEqual(
            normalize_text("   !!!,.$@   "),
            "",
        )


if __name__ == "__main__":
    unittest.main()
