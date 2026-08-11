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
