# google-autocomplete

Automatic sentence completion over a corpus of text files — type part of a
sentence, get the 5 best-matching completions from the corpus (typo-tolerant,
up to one correction: a substitution, insertion, or deletion).

## Requirements

- Python 3.9 or newer.
- No external packages — the whole project runs on the standard library only
  (see `requirements.txt`).

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
`python run.py`, it has to read every file and build a search index from
scratch, which takes roughly **5 minutes**. Let it finish — don't press
Ctrl+C, or you'll lose the work and have to rebuild from scratch next time.

Once it finishes, the prepared data is saved to `data/cache/`. Every run
after that reuses the cache and starts in well under a second. The cache is
automatically rebuilt if the files under `data/Archive` change (detected by
comparing file paths, sizes, and modification times).

### Using it

```
The system is ready. Loaded 2583997 sentences.

Prepared data loaded from cache.
System initialization completed in 0:00.05.
===================================

Enter your text (# to start a new sentence):
python
Here are 5 suggestions:
1. ...
2. ...

python

Search completed in 0:00.12.
===================================
```

- Type text and press **Enter** → see the top 5 completions, with a score
  and the source file/line each one came from.
- Keep typing and press Enter again → it continues from what you already
  typed and re-searches (the query accumulates across turns).
- Type **`#`** and press Enter → resets back to an empty query, so you can
  start a new sentence. `#` can also appear at the end of a longer line to
  reset immediately after that text is searched.
- Press **Ctrl+C**, or **Ctrl+Z then Enter** on Windows → exits cleanly.

## Run the tests

```
python -m unittest discover tests -v
```

This needs no extra install — `unittest` is part of the standard library.
(`python -m pytest` also works if you happen to have `pytest` installed
separately, but it is not a project dependency.)

## Data

| Path | What it is | In git? |
|---|---|---|
| `data/Archive/sample/` | Tiny 6-sentence set for fast local testing | Yes, committed |
| `data/Archive/*.txt` | The real corpus (~120MB, ~2.6M sentences) | No — gitignored, fetched separately |
| `data/cache/` | Auto-generated prepared index + cache (see below) | No — gitignored, rebuilt automatically |

## Project layout

```
run.py                          entry point: python run.py [root_path]
src/
  main.py                       offline init + interactive online loop
  models.py                     shared Sentence / AutoCompleteData contract
  loader/
    data_loader.py              reads .txt files -> List[Sentence]
    normalizer.py                normalize_text (lowercase, strip punctuation, collapse whitespace)
    index.py                    trigram index + candidate search, all query-length strategies
    cache.py                    pickle + manifest-based disk cache for the above
  matching/
    matcher.py                  calculate_score(query, one Sentence) -> score or None
  autocomplete/
    autocomplete.py             get_best_k_completions(prefix) -> top 5, orchestration only
tests/                          one test module per src module, plus integration tests
```

## Project structure & ownership

Shared contract lives in `src/models.py` (`Sentence`, `AutoCompleteData`) — do not
change these shapes without syncing with the other owners.

| Package | Owner | Responsibility |
|---|---|---|
| `src/loader` | Person 3 | Read all `.txt` files under a root path (recursively), normalize each line (`normalizer.py`), build the search index (`index.py`), and cache prepared data to disk (`cache.py`). Owns every decision about how a query of a given length is searched. |
| `src/matching` | Person 2 | Score an already-normalized query against one `Sentence` at a time (`matcher.py`), allowing at most one correction (substitution/insertion/deletion). Has no knowledge of the dataset, the index, or more than one sentence at a time. |
| `src/autocomplete` | Person 1 | The public entry point, `get_best_k_completions(prefix) -> List[AutoCompleteData]`. Asks Person 3 for a narrowed candidate list, scores each one via Person 2, filters/ranks, and returns the top 5 (ties broken alphabetically). Never touches the raw index or does its own matching/scoring. |

### The route through the project

1. **Offline, once at startup:** `src/main.py` calls `load_or_build_cache`,
   which loads every `.txt` file under the root path, normalizes each line,
   and builds the search index (a trigram index, plus a small bounded index
   for fast 1-2 character lookups). The result is cached to `data/cache/`.
2. **Per query:** `get_best_k_completions(prefix)` asks Person 3's
   `get_candidates()` for a shortlist of sentences that could plausibly
   match — not the whole corpus.
3. It scores each candidate with Person 2's `calculate_score(query, sentence)`,
   which returns a score or `None` (no match).
4. It drops the `None`s, sorts by score (ties broken alphabetically), and
   returns the top 5 as `AutoCompleteData(completed_sentence, source_text,
   offset, score)`.

### How candidate search handles different query lengths

| Query length | Strategy | Always fast? |
|---|---|---|
| 1-2 characters | Checks a precomputed index of the top-5 sentences containing that exact string; if 5+ exist, returns instantly. Otherwise falls back to scanning the whole corpus (needed to correctly consider typo-corrected matches too). | Usually — only slow for rare 1-2 character combinations. |
| 3 characters | Always falls back to scanning the whole corpus. A one-edit deletion match at this length would need to look up a 1-2 character substring, which no trigram-based index can represent, so no safe narrowing is possible. | No — always slow on the real dataset. |
| 4-5 characters | Generates every possible one-edit variant of the query and looks each one up in the trigram index. | Yes. |
| 6+ characters | Checks the query's 4 rarest trigrams in the index (a single typo can break at most 3 trigrams, so at least one of the 4 is always guaranteed to be untouched). | Yes. |

## Branches

- `feature/data-loader` — Person 3
- `feature/matching` — Person 2
- `feature/autocomplete` — Person 1
- `dev` — integration branch; all three feature branches are merged in here
