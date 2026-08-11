# google-autocomplete

Automatic sentence completion over a corpus of text files.

## Run

From the repo root (so `src` resolves as a package):

```
python -m src.main
```

## Run the tests

```
python -m unittest discover tests -v
```

## Structure & ownership

Shared contract lives in `src/models.py` (`Sentence`, `AutoCompleteData`) — do not
change these shapes without syncing with the other two owners.

| Package | Owner | Responsibility |
|---|---|---|
| `src/loader` | Person 3 | Read all `.txt` files under `data/Archive` (recursively), normalize each line (`normalizer.py`) into `Sentence.normalized_text`, and return `Sentence` records. |
| `src/matching` | Person 2 | Score an already-normalized query against a `Sentence.normalized_text` (`matcher.py`), allowing at most one correction (substitution/insertion/deletion). Does not normalize anything itself. |
| `src/autocomplete` | Person 1 | Normalize the query, run the matcher over the candidate sentences, rank matches, and return the top 5 as `AutoCompleteData` (ties broken alphabetically), using each sentence's original `text`. |

## The route through the project

1. **Person 3** loads and normalizes the corpus into `Sentence` records.
2. **Person 1** normalizes the query and, for each sentence, calls Person 2.
3. **Person 2** checks the match and returns a score or `None`.
4. **Person 1** sorts the results and returns the top 5.

## Branches

- `feature/data-loader` — Person 3
- `feature/matching` — Person 2
- `feature/autocomplete` — Person 1
- `dev` — integration branch; all three feature branches are merged in here

## Sample data for local debugging

The real corpus (`data/Archive/*`) is 120MB+ and gitignored — it isn't in the repo.
For local dev, `data/Archive/sample/` is a small, committed set of `.txt` files
(including a nested subfolder, to exercise recursive loading) you can point
`load_sentences` at directly:

```python
load_sentences("data/Archive/sample")
```

`quotes.txt` includes `"To be or not to be, that is the question."`, which has
known worked scoring examples in the project spec — useful for sanity-checking
`calculate_score` against expected numbers. Note `calculate_score` expects an
**already-normalized** query (lowercase, no punctuation) — `get_best_completions`
handles that normalization for you if you're calling it instead:

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

Or exercise the full pipeline at once:

```python
from src.loader.data_loader import load_sentences
from src.autocomplete.autocomplete import get_best_completions

sentences = load_sentences("data/Archive/sample")
get_best_completions("TO BE!!", sentences)
```

## Data loader conventions

`load_sentences` recursively reads all `.txt` files under the provided root directory.

- Each physical line in a text file represents one sentence.
- Offsets are **1-indexed** and represent the original line number in the source file.
- Empty lines are skipped, but they still count toward the original line number.
- Files are read as UTF-8.
- If a file cannot be decoded as UTF-8, the entire file is skipped.
- Sentence text is preserved exactly as it appears in the source file, except for line-ending characters.
- `normalize_text` is also owned here (`src/loader/normalizer.py`): lowercase,
  strip punctuation, collapse whitespace. `load_sentences` uses it to populate
  `Sentence.normalized_text` for every line.
