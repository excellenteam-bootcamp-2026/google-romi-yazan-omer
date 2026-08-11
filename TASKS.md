# Project status

## Current state: all three parts implemented, tested, and integrated on `dev`

- Person 3 (Data Loader), Person 2 (Matching), and Person 1 (Autocomplete) are all
  implemented and merged into `dev`.
- 15/15 tests pass: `python -m unittest discover tests -v`.
- Verified end-to-end with real files (not just mocks/fixtures): loading
  `data/Archive/sample` through to `get_best_completions` returns correct,
  ranked, typo-tolerant results.

## Person numbering (per team assignment)

- **Person 1** = Autocomplete — `src/autocomplete/`, branch `feature/autocomplete`
- **Person 2** = Matching + Scoring — `src/matching/`, branch `feature/matching`
- **Person 3** = Data Loader — `src/loader/`, branch `feature/data-loader`

## The route through the project

1. **Person 3** reads every `.txt` file under `data/Archive`, and builds one
   `Sentence` per line (original `text` + `normalized_text`).
2. **Person 1** takes the user's query and the sentences, normalizes the query,
   and for each sentence calls Person 2.
3. **Person 2** checks whether the (normalized) query matches the sentence —
   exact substring, or with at most one correction — and returns a score or `None`.
4. **Person 1** collects the scores, drops the `None`s, sorts (score desc, then
   alphabetically), and returns the top 5.

## Shared contract (`src/models.py`)

- `Sentence(text, normalized_text, source, offset)` — `text` is the original
  line, kept exactly as in the source file (used for final display);
  `normalized_text` is lowercase/punctuation-free/whitespace-collapsed (used
  for matching), populated by Person 3 at load time.
- `AutoCompleteData(completed_sentence, source_text, offset, score)` —
  Person 1's final output shape.

---

## Person 3 — Data Loader (`src/loader/`, branch `feature/data-loader`) — done

- [x] Recursively finds every `.txt` file under `root_path`, any folder depth.
- [x] Each line → one `Sentence`; `normalized_text` computed via
      `normalize_text` (`src/loader/normalizer.py`).
- [x] Offsets are 1-indexed, original line numbers; empty lines are skipped
      but still count toward the line number.
- [x] Files read as UTF-8; a file that fails to decode is skipped entirely.
- [x] `tests/test_loader.py` — 6 tests, all passing.
- [ ] **Not yet built:** candidate search/indexing (e.g. a trigram index) to
      narrow the corpus before Person 2 scores it — right now Person 1 scores
      the *entire* corpus on every query. Correctness-first for now; revisit
      once the team wants to optimize (see Stage B in the spec).

## Person 2 — Matching (`src/matching/matcher.py`, branch `feature/matching`) — done

- [x] `calculate_score(query, sentence)`: expects `query` already normalized,
      reads `sentence.normalized_text` — does **not** normalize anything itself.
- [x] Exact substring match (start, middle, or end of the sentence).
- [x] Fuzzy match with **at most one** correction: substitution, insertion, or deletion.
- [x] Base score = 2 × number of matching characters.
- [x] Substitution penalty by position: 1st -5, 2nd -4, 3rd -3, 4th -2, 5th+ -1.
- [x] Insertion/deletion penalty by position: 1st -10, 2nd -8, 3rd -6, 4th -4, 5th+ -2.
- [x] Returns `None` when more than one correction would be needed.
- [x] Verified against the worked examples in `README.md`.
- [x] `tests/test_matcher.py` — 6 tests, all passing.

## Person 1 — Autocomplete (`src/autocomplete/autocomplete.py`, branch `feature/autocomplete`) — done

- [x] `get_best_completions(query, candidates)`: normalizes the query itself,
      then calls `calculate_score` per candidate.
- [x] Filters out `None`s (non-matches).
- [x] Sorts by score descending, ties broken alphabetically.
- [x] Returns the top 5 as `AutoCompleteData`, using each sentence's original
      `text` (not `normalized_text`) for `completed_sentence`.
- [x] `tests/test_autocomplete.py` — 3 tests, all passing.

---

## Integration issues found and fixed on `dev`

These all came from branches being built before the shared `Sentence.normalized_text`
field / normalization-ownership change landed — worth knowing about, not because
anything is still broken, but as a heads-up for future merges:

- `src/loader/normalizer.py` was accidentally committed **empty** at one point — fixed.
- `feature/data-loader`'s `load_sentences` wasn't populating `normalized_text` — fixed.
- `feature/autocomplete`'s tests were constructing `Sentence` without `normalized_text` — fixed.
- `get_best_completions` was passing the **raw, unnormalized** query straight into
  `calculate_score`, which no longer normalizes anything itself — fixed (now
  normalizes the query before scoring).

## Still open / next steps

- [ ] Candidate search/indexing for Person 3 — performance, not correctness;
      full corpus scan works correctly today but won't scale to the real dataset.
- [ ] `main.py`: offline phase (call `load_sentences` once at startup) + online
      phase (REPL: show top-5 on Enter, keep typing from where you left off,
      reset state on `#`).
- [ ] Merge `dev` into `main` once the team is happy with it.
- [ ] Unconfirmed: should `feature/matching` be renamed to `feature/matcher`
      to match the team's branch-naming message?
