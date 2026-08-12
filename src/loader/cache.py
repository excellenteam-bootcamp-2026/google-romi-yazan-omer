import json
import pickle
from pathlib import Path
from typing import Dict, List, Set, Tuple

from src.loader.data_loader import load_sentences
from src.loader.index import build_index
from src.models import Sentence


CACHE_VERSION = 1

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
    index: Dict[str, Set[int]],
    manifest: dict,
    cache_dir: Path,
) -> None:
    """
    Save the prepared Sentence list and trigram index to disk.
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
            (sentences, index),
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
) -> Tuple[List[Sentence], Dict[str, Set[int]]]:
    """
    Load the already prepared Sentence list and trigram index.
    """
    data_path = cache_dir / CACHE_DATA_FILE

    with data_path.open("rb") as file:
        sentences, index = pickle.load(file)

    return sentences, index


def load_or_build_cache(
    root_path: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
) -> Tuple[
    List[Sentence],
    Dict[str, Set[int]],
    bool,
]:
    """
    Load prepared data from cache when the source files
    have not changed.

    If the source files changed, rebuild the Sentence list
    and trigram index and replace the old cache.

    Returns:
        sentences
        index
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

    # Cache is valid.
    if (
        data_path.exists()
        and cached_manifest == current_manifest
    ):
        try:
            sentences, index = _load_cache(
                cache_dir
            )

            return sentences, index, True

        except (
            OSError,
            EOFError,
            pickle.UnpicklingError,
            AttributeError,
            ValueError,
            TypeError,
        ):
            # Cache is damaged or incompatible.
            # Rebuild it below.
            pass

    # No valid cache exists:
    # rebuild everything from the source files.
    sentences = load_sentences(root_path)

    index = build_index(sentences)

    _save_cache(
        sentences,
        index,
        current_manifest,
        cache_dir,
    )

    return sentences, index, False