import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.loader.cache import load_or_build_cache


class TestCache(unittest.TestCase):

    def test_first_run_builds_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "archive"
            cache_dir = Path(temp_dir) / "cache"

            root.mkdir()

            (
                root / "sentences.txt"
            ).write_text(
                "Python is useful.\n",
                encoding="utf-8",
            )

            (
                sentences,
                index,
                short_query_index,
                loaded_from_cache,
            ) = load_or_build_cache(
                str(root),
                cache_dir,
            )

            self.assertFalse(
                loaded_from_cache
            )

            self.assertEqual(
                len(sentences),
                1,
            )

            self.assertIn(
                "pyt",
                index,
            )

            self.assertIn(
                "p",
                short_query_index,
            )

            self.assertIn(
                "py",
                short_query_index,
            )

            self.assertEqual(
                short_query_index["py"],
                [0],
            )

            self.assertTrue(
                (
                    cache_dir
                    / "prepared_data.pkl"
                ).exists()
            )

            self.assertTrue(
                (
                    cache_dir
                    / "manifest.json"
                ).exists()
            )

    def test_second_run_loads_existing_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "archive"
            cache_dir = Path(temp_dir) / "cache"

            root.mkdir()

            (
                root / "sentences.txt"
            ).write_text(
                "Python is useful.\n",
                encoding="utf-8",
            )

            load_or_build_cache(
                str(root),
                cache_dir,
            )

            with patch(
                "src.loader.cache.load_sentences"
            ) as loader:

                (
                    sentences,
                    index,
                    short_query_index,
                    loaded_from_cache,
                ) = load_or_build_cache(
                    str(root),
                    cache_dir,
                )

            self.assertTrue(
                loaded_from_cache
            )

            self.assertEqual(
                len(sentences),
                1,
            )

            self.assertIn(
                "pyt",
                index,
            )

            self.assertIn(
                "py",
                short_query_index,
            )

            self.assertEqual(
                short_query_index["py"],
                [0],
            )

            loader.assert_not_called()

    def test_modified_source_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "archive"
            cache_dir = Path(temp_dir) / "cache"

            root.mkdir()

            source = (
                root / "sentences.txt"
            )

            source.write_text(
                "Python is useful.\n",
                encoding="utf-8",
            )

            load_or_build_cache(
                str(root),
                cache_dir,
            )

            source.write_text(
                "Python is useful.\n"
                "Network services are useful.\n",
                encoding="utf-8",
            )

            (
                sentences,
                index,
                short_query_index,
                loaded_from_cache,
            ) = load_or_build_cache(
                str(root),
                cache_dir,
            )

            self.assertFalse(
                loaded_from_cache
            )

            self.assertEqual(
                len(sentences),
                2,
            )

            self.assertIn(
                "pyt",
                index,
            )

            self.assertIn(
                "net",
                index,
            )

            self.assertIn(
                "py",
                short_query_index,
            )

            self.assertIn(
                "ne",
                short_query_index,
            )

    def test_new_source_file_invalidates_cache(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "archive"
            cache_dir = Path(temp_dir) / "cache"

            root.mkdir()

            (
                root / "first.txt"
            ).write_text(
                "Python is useful.\n",
                encoding="utf-8",
            )

            load_or_build_cache(
                str(root),
                cache_dir,
            )

            (
                root / "second.txt"
            ).write_text(
                "Network services are useful.\n",
                encoding="utf-8",
            )

            (
                sentences,
                index,
                short_query_index,
                loaded_from_cache,
            ) = load_or_build_cache(
                str(root),
                cache_dir,
            )

            self.assertFalse(
                loaded_from_cache
            )

            self.assertEqual(
                len(sentences),
                2,
            )

            self.assertIn(
                "pyt",
                index,
            )

            self.assertIn(
                "net",
                index,
            )

            self.assertIn(
                "py",
                short_query_index,
            )

            self.assertIn(
                "ne",
                short_query_index,
            )


if __name__ == "__main__":
    unittest.main()