from pathlib import Path
from typing import List

from src.models import Sentence


def load_sentences(root_path: str) -> List[Sentence]:
    """
    Load all sentences from .txt files under root_path recursively.

    Conventions:
    - Each line in a .txt file represents one sentence.
    - Offsets are 1-indexed and represent the original line number in the file.
    - Empty lines are skipped, but they still count toward the offset.
    - Files are read as UTF-8.
    - A file that cannot be decoded as UTF-8 is skipped entirely.
    - Sentence text is preserved exactly, except for the line ending.
    """
    sentences: List[Sentence] = []
    root = Path(root_path)

    for file_path in sorted(root.rglob("*.txt")):
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for offset, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue

            sentences.append(
                Sentence(
                    text=line,
                    source=str(file_path),
                    offset=offset,
                )
            )

    return sentences
