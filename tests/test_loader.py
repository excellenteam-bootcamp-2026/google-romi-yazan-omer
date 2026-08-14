import tempfile
import unittest
from pathlib import Path

from src.loader.data_loader import load_sentences


class TestDataLoader(unittest.TestCase):

    def test_loads_sample_files_recursively(self):
        sentences = load_sentences("data/Archive/sample")

        self.assertEqual(len(sentences), 6)

        sources = {Path(sentence.source) for sentence in sentences}

        self.assertIn(
            Path("data/Archive/sample/quotes.txt"),
            sources,
        )
        self.assertIn(
            Path("data/Archive/sample/nested/tech_docs.txt"),
            sources,
        )

    def test_preserves_original_text_source_and_offset(self):
        sentences = load_sentences("data/Archive/sample")

        target = next(
            sentence
            for sentence in sentences
            if sentence.text == "To be or not to be, that is the question."
        )

        self.assertEqual(
            target.text,
            "To be or not to be, that is the question.",
        )
        self.assertEqual(
            Path(target.source),
            Path("data/Archive/sample/quotes.txt"),
        )
        self.assertEqual(target.offset, 1)

    def test_skips_empty_lines_but_preserves_original_line_number(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "sentences.txt"

            file_path.write_text(
                "First sentence.\n\nSecond sentence.\n",
                encoding="utf-8",
            )

            sentences = load_sentences(temp_dir)

            self.assertEqual(len(sentences), 2)

            self.assertEqual(sentences[0].text, "First sentence.")
            self.assertEqual(sentences[0].offset, 1)

            self.assertEqual(sentences[1].text, "Second sentence.")
            self.assertEqual(sentences[1].offset, 3)

    def test_preserves_case_punctuation_and_spaces(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "original.txt"

            file_path.write_text(
                "Hello,   WORLD!!!\n",
                encoding="utf-8",
            )

            sentences = load_sentences(temp_dir)

            self.assertEqual(len(sentences), 1)
            self.assertEqual(
                sentences[0].text,
                "Hello,   WORLD!!!",
            )

    def test_ignores_non_txt_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "sentences.txt").write_text(
                "Valid sentence.\n",
                encoding="utf-8",
            )

            (root / "ignored.md").write_text(
                "This should not be loaded.\n",
                encoding="utf-8",
            )

            sentences = load_sentences(temp_dir)

            self.assertEqual(len(sentences), 1)
            self.assertEqual(
                sentences[0].text,
                "Valid sentence.",
            )

    def test_skips_file_with_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "valid.txt").write_text(
                "Valid sentence.\n",
                encoding="utf-8",
            )

            (root / "invalid.txt").write_bytes(
                b"\xff\xfe\xfa"
            )

            sentences = load_sentences(temp_dir)

            self.assertEqual(len(sentences), 1)
            self.assertEqual(
                sentences[0].text,
                "Valid sentence.",
            )


if __name__ == "__main__":
    unittest.main()
