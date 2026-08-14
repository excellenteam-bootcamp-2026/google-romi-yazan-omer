import tempfile
import unittest
from pathlib import Path

from src.loader.data_loader import load_sentences
from src.loader.index import build_index, get_candidates


class TestLoaderIndexIntegration(unittest.TestCase):

    def test_full_person1_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            nested_dir = root / "nested"
            nested_dir.mkdir()

            (root / "first.txt").write_text(
                "Python, is a useful language!\n"
                "All that glitters is not gold.\n",
                encoding="utf-8",
            )

            (nested_dir / "second.txt").write_text(
                "Information about writing a good bug report.\n",
                encoding="utf-8",
            )

            # Step 1:
            # Load all sentences recursively.
            sentences = load_sentences(temp_dir)

            self.assertEqual(len(sentences), 3)

            # Step 2:
            # Verify that the original text is preserved while
            # normalized_text contains the searchable representation.
            python_sentence = next(
                sentence
                for sentence in sentences
                if sentence.text == "Python, is a useful language!"
            )

            self.assertEqual(
                python_sentence.text,
                "Python, is a useful language!",
            )

            self.assertEqual(
                python_sentence.normalized_text,
                "python is a useful language",
            )

            # Step 3 + 4:
            # Build the trigram inverted index.
            index = build_index(sentences)

            self.assertIn("pyt", index)

            # Step 5:
            # Query normalization + index lookup should retrieve
            # the original Python sentence.
            candidates = get_candidates(
                "PYTHON,",
                sentences,
                index,
            )

            self.assertIn(
                python_sentence,
                candidates,
            )

    def test_nested_file_sentence_can_be_found_through_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            nested_dir = root / "level1" / "level2"
            nested_dir.mkdir(parents=True)

            (nested_dir / "deep.txt").write_text(
                "Information about writing a good bug report.\n",
                encoding="utf-8",
            )

            sentences = load_sentences(temp_dir)
            index = build_index(sentences)

            candidates = get_candidates(
                "writing",
                sentences,
                index,
            )

            self.assertEqual(len(candidates), 1)

            self.assertEqual(
                candidates[0].text,
                "Information about writing a good bug report.",
            )

            self.assertEqual(
                candidates[0].offset,
                1,
            )

            self.assertEqual(
                Path(candidates[0].source),
                nested_dir / "deep.txt",
            )

    def test_query_normalization_works_with_real_loaded_sentence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "sentences.txt").write_text(
                "Hello,     WORLD!!!\n",
                encoding="utf-8",
            )

            sentences = load_sentences(temp_dir)
            index = build_index(sentences)

            candidates = get_candidates(
                "HELLO WORLD",
                sentences,
                index,
            )

            self.assertIn(
                sentences[0],
                candidates,
            )

            # The returned candidate must still contain the ORIGINAL text.
            self.assertEqual(
                candidates[0].text,
                "Hello,     WORLD!!!",
            )

            self.assertEqual(
                candidates[0].normalized_text,
                "hello world",
            )

    def test_short_query_fallback_works_with_loaded_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "sentences.txt").write_text(
                "Python is useful.\n"
                "Today is sunny.\n"
                "Yellow flowers grow here.\n",
                encoding="utf-8",
            )

            sentences = load_sentences(temp_dir)
            index = build_index(sentences)

            # One-character query cannot safely use the trigram index.
            candidates = get_candidates(
                "y",
                sentences,
                index,
            )

            # Person 1 safely returns all candidates.
            # Person 2 will later decide which ones really match.
            self.assertEqual(
                len(candidates),
                len(sentences),
            )

    def test_candidate_search_does_not_score_or_modify_sentences(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            original_text = "PYTHON, Language!!!"

            (root / "sentences.txt").write_text(
                original_text + "\n",
                encoding="utf-8",
            )

            sentences = load_sentences(temp_dir)
            index = build_index(sentences)

            candidates = get_candidates(
                "python",
                sentences,
                index,
            )

            self.assertEqual(len(candidates), 1)

            # Person 1 must return the original Sentence object.
            self.assertEqual(
                candidates[0].text,
                original_text,
            )

            self.assertEqual(
                candidates[0].normalized_text,
                "python language",
            )


if __name__ == "__main__":
    unittest.main()
