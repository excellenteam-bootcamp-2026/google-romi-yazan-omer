import json
import pickle
from pathlib import Path
from typing import List, Tuple

from src.loader.data_loader import load_sentences
from src.loader.index import (
    ShortQueryIndex,
    TrigramIndex,
    build_search_indexes,
)
from src.models import Sentence


CACHE_VERSION = 2

DEFAULT_CACHE_DIR = Path("data/cache")

CACHE_DATA_FILE = "prepared_data.pkl"
CACHE_MANIFEST_FILE = "manifest.json"


def _build_manifest(root_path: str) -> dict:
    """
    Build metadata describing the current source files.

    The manifest is used to detect whether any .txt file was
    added, removed, or modified since the cache was created.
    """
    root = Path(root_path)

    files = []

    for file_path in sorted(root.rglob("*.txt")):
        stat = file_path.stat()

        files.append(
            {
                "path": file_path.relative_to(root).as_posix(),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )

    return {
        "cache_version": CACHE_VERSION,
        "root_path": str(root.resolve()),
        "files": files,
    }


def _load_manifest(manifest_path: Path) -> dict | None:
    try:
        with manifest_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError):
        return None


def _save_cache(
    sentences: List[Sentence],
    index: TrigramIndex,
    short_query_index: ShortQueryIndex,
    manifest: dict,
    cache_dir: Path,
) -> None:
    """
    Save all prepared search data to disk.
    """
    cache_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_path = cache_dir / CACHE_DATA_FILE
    manifest_path = cache_dir / CACHE_MANIFEST_FILE

    temporary_data_path = data_path.with_suffix(".tmp")
    temporary_manifest_path = manifest_path.with_suffix(".tmp")

    with temporary_data_path.open("wb") as file:
        pickle.dump(
            (
                sentences,
                index,
                short_query_index,
            ),
            file,
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    with temporary_manifest_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            indent=2,
        )

    temporary_data_path.replace(data_path)
    temporary_manifest_path.replace(manifest_path)


def _load_cache(
    cache_dir: Path,
) -> Tuple[
    List[Sentence],
    TrigramIndex,
    ShortQueryIndex,
]:
    """
    Load all prepared search data from disk.
    """
    data_path = cache_dir / CACHE_DATA_FILE

    with data_path.open("rb") as file:
        (
            sentences,
            index,
            short_query_index,
        ) = pickle.load(file)

    return (
        sentences,
        index,
        short_query_index,
    )


def load_or_build_cache(
    root_path: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> Tuple[
    List[Sentence],
    TrigramIndex,
    ShortQueryIndex,
    bool,
]:
    """
    Load prepared data from cache when the source files
    have not changed.

    If the source files changed, rebuild the Sentence list,
    trigram index, and short-query Top-5 index and replace
    the old cache.

    Returns:
        sentences
        index
        short_query_index
        loaded_from_cache
    """
    cache_dir = Path(cache_dir)

    manifest_path = (
        cache_dir / CACHE_MANIFEST_FILE
    )

    data_path = (
        cache_dir / CACHE_DATA_FILE
    )

    current_manifest = _build_manifest(root_path)
    cached_manifest = _load_manifest(manifest_path)

    if (
        data_path.exists()
        and cached_manifest == current_manifest
    ):
        try:
            (
                sentences,
                index,
                short_query_index,
            ) = _load_cache(cache_dir)

            return (
                sentences,
                index,
                short_query_index,
                True,
            )

        except (
            OSError,
            EOFError,
            pickle.UnpicklingError,
            AttributeError,
            ValueError,
            TypeError,
        ):
            pass

    sentences = load_sentences(root_path)

    (
        index,
        short_query_index,
    ) = build_search_indexes(sentences)

    _save_cache(
        sentences,
        index,
        short_query_index,
        current_manifest,
        cache_dir,
    )

    return (
        sentences,
        index,
        short_query_index,
        False,
    )