# Project status

## Current state: full Stage-A pipeline implemented, tested, and integrated on `dev`

- Person 3 (Data Loader + trigram index), Person 2 (Matching), and Person 1
  (Autocomplete) are all implemented and merged into `dev`.
- **58/58 tests pass:** `python -m unittest discover tests -v`.
- The program is actually runnable end-to-end: `python -m src.main [root_path]`
  loads the corpus, builds the index, and runs an interactive REPL (type text,
  press Enter for top-5 suggestions, keep typing to extend the query, `#` to
  reset). Verified manually against both the sample data and the real dataset.

## Person numbering (per team assignment)

- **Person 1** = Autocomplete — `src/autocomplete/`, branch `feature/autocomplete`
- **Person 2** = Matching + Scoring — `src/matching/`, branch `feature/matching`
- **Person 3** = Data Loader + candidate search — `src/loader/`, branch `feature/data-loader`

## The route through the project

1. **Person 3** (offline, once) reads every `.txt` file under `data/Archive`,
   builds one `Sentence` per line, and builds a trigram inverted index over
   all the sentences.
2. **Person 1** (online, per query) normalizes the query and asks Person 3's
   `get_candidates` for a narrowed shortlist of sentences that could match —
   not the whole corpus.
3. **Person 1** loops over that shortlist and, for each one, calls Person 2's
   `calculate_score(query, sentence)`.
4. **Person 2** checks whether the query matches — exact substring, or with
   at most one correction — and returns a score or `None`. Person 2 never
   sees the dataset, the index, or more than one sentence at a time.
5. **Person 1** collects the valid scores, drops the `None`s, sorts (score
   descending, ties broken alphabetically), and returns the top 5 as
   `AutoCompleteData`.

## Shared contract (`src/models.py`)

- `Sentence(text, normalized_text, source, offset)` — `text` is the original
  line, kept exactly as in the source file (used for final display);
  `normalized_text` is lowercase/punctuation-free/whitespace-collapsed (used
  for matching/indexing), populated by Person 3 at load time.
- `AutoCompleteData(completed_sentence, source_text, offset, score)` —
  Person 1's final output shape, matching the spec exactly.

---

## Person 3 — Data Loader + Index (`src/loader/`, branch `feature/data-loader`) — done

- [x] `load_sentences(root_path)`: recursively finds every `.txt` file at any
      folder depth, one `Sentence` per non-empty line, 1-indexed offsets,
      UTF-8 (files that fail to decode are skipped entirely).
- [x] `normalize_text` (`src/loader/normalizer.py`): lowercase, strip
      punctuation, collapse whitespace.
- [x] Trigram inverted index (`src/loader/index.py`):
      `generate_trigrams`, `build_index` (built once, offline),
      `get_candidates` (query → narrowed candidate list). Short queries
      (below `MIN_SAFE_QUERY_LENGTH = 2 * TRIGRAM_SIZE`) safely fall back to
      the full corpus, since trigram filtering can't guarantee correctness
      below that length.
- [x] `tests/test_loader.py`, `tests/test_normalizer.py`,
      `tests/test_index.py`, `tests/test_loader_index_integration.py`.

## Person 2 — Matching (`src/matching/matcher.py`, branch `feature/matching`) — done

- [x] `calculate_score(query, sentence)`: expects `query` already normalized,
      reads `sentence.normalized_text` directly — does not normalize
      anything itself, has no knowledge of the dataset or index.
- [x] Exact substring match (start, middle, or end of the sentence).
- [x] Fuzzy match with **at most one** correction: substitution, insertion, or deletion.
- [x] Base score = 2 × number of matching characters; positional penalties
      per the spec (substitution: -5/-4/-3/-2/-1; insertion/deletion:
      -10/-8/-6/-4/-2).
- [x] Returns `None` when more than one correction would be needed.
- [x] Verified against every worked example in `README.md`.
- [x] `tests/test_matcher.py` — 6 tests.

## Person 1 — Autocomplete (`src/autocomplete/autocomplete.py`, branch `feature/autocomplete`) — done

- [x] Public contract matches the spec exactly:
      `get_best_k_completions(prefix: str) -> List[AutoCompleteData]`.
- [x] `initialize(sentences, index)` stores the offline-built state once;
      `get_best_k_completions` never reloads files or rebuilds the index.
- [x] Internally: calls `get_candidates` (Person 3), then the `_rank_candidates`
      helper loops the shortlist, calls `calculate_score` (Person 2) once per
      candidate, filters `None`s, sorts (score desc, alphabetical tiebreak),
      returns top 5.
- [x] `tests/test_autocomplete.py` — 6 tests, including that `get_best_k_completions`
      raises before `initialize()` and never touches `load_sentences`/`build_index` itself.

## `main.py` — done

- [x] Offline phase: `load_sentences` + `build_index` once at startup,
      `autocomplete.initialize(sentences, index)`.
- [x] Online phase: REPL loop — accumulates typed text across turns, shows
      top-5 on Enter, resets on `#`, exits cleanly on EOF.

---

## Integration issues found and fixed along the way

- `src/loader/normalizer.py` was accidentally committed empty at one point — fixed.
- `feature/data-loader`'s `load_sentences` and `feature/autocomplete`'s tests
  predated the `Sentence.normalized_text` field — fixed.
- `get_best_completions`/`get_best_k_completions` was passing the raw,
  unnormalized query straight into `calculate_score` — fixed.
- `MIN_SAFE_QUERY_LENGTH` was a separately hardcoded `6`; now derived as
  `2 * TRIGRAM_SIZE` so the two constants can't silently drift apart.
- The trigram index existed but nothing called it before `get_best_completions`
  — fixed by wiring `get_candidates` into the new `get_best_k_completions`.

## Still open / next steps

- [ ] Merge `dev` into `main` once the team is happy with it (PR #1 is open:
      `dev` → `main`).
- [ ] Unconfirmed: should `feature/matching` be renamed to `feature/matcher`
      to match the team's branch-naming message?
- [ ] Stage B (per spec): profiling, C++ rewrite of hot paths, Protobuf
      storage — not started, intentionally deferred until Stage A is signed off.
