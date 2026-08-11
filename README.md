# google-autocomplete

Automatic sentence completion over a corpus of text files.

## Run

From the repo root (so `src` resolves as a package):

```
python -m src.main
```

## Structure & ownership

Shared contract lives in `src/models.py` (`Sentence`, `AutoCompleteData`) — do not
change these shapes without syncing with the other two owners.

| Package | Owner | Responsibility |
|---|---|---|
| `src/loader` | Person 1 | Read all `.txt` files under `data/Archive` (recursively), normalize each line (`normalizer.py`) into `Sentence.normalized_text`, and return `Sentence` records. Also owns candidate search (narrowing the corpus down before Person 2 scores it). |
| `src/matching` | Person 2 | Score an already-normalized query against a `Sentence.normalized_text` (`matcher.py`), allowing at most one correction (substitution/insertion/deletion). Does not normalize anything itself. |
| `src/autocomplete` | Person 3 | Run the matcher over the candidate sentences, rank matches, and return the top 5 as `AutoCompleteData` using each sentence's original `text` (ties broken alphabetically). |

## Branches

- `feature/data-loader` — Person 1
- `feature/matching` — Person 2
- `feature/autocomplete` — Person 3

## Sample data for local debugging

The real corpus (`data/Archive/*`) is 120MB+ and gitignored — it isn't in the repo.
For local dev, `data/Archive/sample/` is a small, committed set of `.txt` files
(including a nested subfolder, to exercise recursive loading) you can point
`load_sentences` at directly:

```python
load_sentences("data/Archive/sample")
```

`quotes.txt` includes `"To be or not to be, that is the question."`, which has
known worked scoring examples in the project spec — useful for Person 2 to
sanity-check `calculate_score` against expected numbers. Note `calculate_score`
expects an **already-normalized** query (lowercase, no punctuation):

| Query (pre-normalized) | Expected score | Why |
|---|---|---|
| `to be` | 10 | exact prefix match, 5 chars incl. space |
| `or not` | 12 | exact match, 6 chars |
| `be that` | 14 | exact match, 7 chars (comma already removed) |
| `2o be` | 5 | base 10, -5 wrong 1st letter |
| `to pe` | 8 | base 10, -2 wrong 4th letter |
| `or knot` | 8 | base 12, -4 for added 4th letter |
| `not be` | no match | needs 2 corrections ("to" missing) |

For unit tests, `tests/fixtures.py` has the same data already as `Sentence`
objects (`TEST_SENTENCES`, including `normalized_text`), so `matching`/`autocomplete`
can be tested without going through the loader at all:

```python
from tests.fixtures import TEST_SENTENCES
from src.matching.matcher import calculate_score

calculate_score("to be", TEST_SENTENCES[0])
```

## Data loader conventions

`load_sentences` recursively reads all `.txt` files under the provided root directory.

- Each physical line in a text file represents one sentence.
- Offsets are **1-indexed** and represent the original line number in the source file.
- Empty lines are skipped, but they still count toward the original line number.
- Files are read as UTF-8.
- If a file cannot be decoded as UTF-8, the entire file is skipped.
- Sentence text is preserved exactly as it appears in the source file, except for line-ending characters.
- The loader does not perform normalization, punctuation removal, matching, scoring, or ranking.
