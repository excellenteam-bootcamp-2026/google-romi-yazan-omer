# google-autocomplete

Automatic sentence completion over a corpus of text files — type part of a
sentence, get the 5 best-matching completions from the corpus (typo-tolerant,
up to one correction).

## Quick start

```
python run.py
```

That's it — no `-m` flags needed. This loads the real corpus (`data/Archive`)
and starts an interactive prompt.

To run against a tiny 6-sentence test set instead (useful for a fast sanity
check), pass its path explicitly:

```
python run.py data/Archive/sample
```

### First run is slow — this is expected

The real corpus has ~2.6 million sentences. The **first** time you run
`python run.py`, it has to build a search index from scratch, which takes
roughly **1.5–2 minutes**. Let it finish — don't press Ctrl+C, or you'll lose
the work and have to rebuild from scratch next time.

Once it finishes, the prepared data is saved to `data/cache/`. Every run
after that reuses the cache and starts much faster. The cache is
automatically rebuilt if the files under `data/Archive` change.

### Using it

```
The system is ready. Loaded 2583991 sentences.
...
Enter your text (# to start a new sentence):
python
Here are 5 suggestions:
1. ...
2. ...
```

- Type text and press **Enter** → see the top 5 completions.
- Keep typing and press Enter again → it continues from what you already
  typed and re-searches.
- Type **`#`** and press Enter → resets back to an empty query.
- Press **Ctrl+C** (or Ctrl+Z then Enter) → exits cleanly.

## Run the tests

```
python -m pytest
```

or, equivalently (no extra install required):

```
python -m unittest discover tests
```

## Data

| Path | What it is | In git? |
|---|---|---|
| `data/Archive/sample/` | Tiny 6-sentence set for fast local testing | Yes, committed |
| `data/Archive/*.txt` | The real corpus (~120MB, ~2.6M sentences) | No — gitignored, fetched separately |
| `data/cache/` | Auto-generated prepared index + cache | No — gitignored, rebuilt automatically |

## Project structure & ownership

Shared contract lives in `src/models.py` (`Sentence`, `AutoCompleteData`) — do not
change these shapes without syncing with the other owners.

| Package | Owner | Responsibility |
|---|---|---|
| `src/loader` | Person 3 | Read all `.txt` files under a root path (recursively), normalize each line (`normalizer.py`), build the search index (`index.py`), and cache prepared data to disk (`cache.py`). |
| `src/matching` | Person 2 | Score an already-normalized query against one `Sentence` at a time (`matcher.py`), allowing at most one correction (substitution/insertion/deletion). Has no knowledge of the dataset or index. |
| `src/autocomplete` | Person 1 | The public entry point, `get_best_k_completions(prefix) -> List[AutoCompleteData]`. Asks Person 3 for a narrowed candidate list, scores each one via Person 2, filters/ranks, and returns the top 5 (ties broken alphabetically). |

### The route through the project

1. **Offline, once at startup:** `src/main.py` calls `load_or_build_cache`,
   which loads every `.txt` file under the root path, normalizes each line,
   and builds a search index (trigram index + a fast index for 1–2 character
   queries). Result is cached to `data/cache/`.
2. **Per query:** `get_best_k_completions(prefix)` asks Person 3's
   `get_candidates()` for a shortlist of sentences that could plausibly
   match — not the whole corpus.
3. It scores each candidate with Person 2's `calculate_score(query, sentence)`,
   which returns a score or `None` (no match).
4. It drops the `None`s, sorts by score (ties broken alphabetically), and
   returns the top 5 as `AutoCompleteData(completed_sentence, source_text,
   offset, score)`.

## Known performance limitation

Queries of exactly **3 characters** currently fall back to scoring the
*entire* corpus (no index narrows the candidate list for that length), which
is slow on the real ~2.6M-sentence dataset — tens of seconds per query.
Queries of length 1–2, 4–5, and 6+ are all fast (sub-few-seconds) because
they're narrowed by an index first. This is a known issue, not a bug in the
scoring logic itself.

## Branches

- `feature/data-loader` — Person 3
- `feature/matching` — Person 2
- `feature/autocomplete` — Person 1
- `dev` — integration branch; all three feature branches are merged in here
