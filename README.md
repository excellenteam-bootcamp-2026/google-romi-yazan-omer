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
| `src/loader` | Person 1 | Read all `.txt` files under `data/Archive` (recursively) and return `Sentence` records (text, source, offset). |
| `src/matching` | Person 2 | Normalize text (`normalizer.py`) and score a query against a `Sentence` (`matcher.py`), allowing at most one correction (substitution/insertion/deletion). |
| `src/autocomplete` | Person 3 | Run the matcher over all sentences, rank matches, and return the top 5 as `AutoCompleteData` (ties broken alphabetically). |

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
sanity-check `calculate_score` against expected numbers:

| Query | Expected score | Why |
|---|---|---|
| `To be` | 10 | exact prefix match, 5 chars incl. space |
| `or Not` | 12 | exact match (case-insensitive), 6 chars |
| `be, that` | 14 | exact match, 7 chars (comma ignored) |
| `2o be` | 5 | base 10, -5 wrong 1st letter |
| `to pe` | 8 | base 10, -2 wrong 4th letter |
| `or knot` | 8 | base 12, -4 for added 4th letter |
| `not be` | no match | needs 2 corrections ("to" missing) |

For unit tests, `tests/fixtures.py` has the same data already as `Sentence`
objects (`TEST_SENTENCES`), so `matching`/`autocomplete` can be tested without
going through the loader at all:

```python
from tests.fixtures import TEST_SENTENCES
from src.matching.matcher import calculate_score

calculate_score("To be", TEST_SENTENCES[0])
```
