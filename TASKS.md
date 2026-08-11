# Project status

## What's been done (setup / foundation, on `main`)

- Reviewed the skeleton and confirmed the loader / matching / autocomplete split is workable for 3 parallel developers.
- Added `src/models.py` with the shared contract: `Sentence` (text, source, offset) and `AutoCompleteData` (completed_sentence, source_text, offset, score).
- Type-hinted the four interface functions against those shared types (bodies are still `pass` — no logic implemented):
  - `load_sentences(root_path: str) -> List[Sentence]`
  - `normalize_text(text: str) -> str`
  - `calculate_score(query: str, sentence: Sentence) -> Optional[int]`
  - `get_best_completions(query: str, sentences: List[Sentence]) -> List[AutoCompleteData]`
- Fixed `src/main.py` imports so it runs as a package (`python -m src.main` from repo root).
- Added `.gitignore` rules: real dataset (`data/Archive/*`, 120MB+) excluded from git.
- Added `data/Archive/sample/` — a small, committed dataset (incl. a nested folder) for local debugging, using the project spec's worked example sentence so scores can be checked against known values.
- Added `tests/fixtures.py` with `TEST_SENTENCES` as ready-made `Sentence` objects, so matching/autocomplete can be tested without the loader at all.
- Documented all of the above in `README.md` (run instructions, ownership table, sample data, worked score table).
- Committed everything to `main` and pushed it.
- Replaced the old unrelated branches with `feature/data-loader`, `feature/matching`, `feature/autocomplete`, pushed to origin, each tracking its remote counterpart.

None of the actual algorithm logic has been written yet — that's the checklist below.

---

## Person 1 — Data Loader (`src/loader/data_loader.py`, branch `feature/data-loader`)

- [ ] Recursively walk `root_path` and find every `.txt` file, at any folder depth.
- [ ] Read each file, treating each line as one sentence.
- [ ] For each line, build a `Sentence(text=<line>, source=<file path>, offset=<line number>)`.
- [ ] Decide and document the offset convention (0-indexed vs 1-indexed) — tell Person 2/3, since `AutoCompleteData.offset` in the final output depends on it.
- [ ] Decide how empty lines are handled (skip vs keep) and document it.
- [ ] Read files as UTF-8; decide what happens on a decode error (skip file? skip line?).
- [ ] Return the combined `List[Sentence]` across all files.
- [ ] Write `tests/test_loader.py` using `data/Archive/sample` (has a nested subfolder specifically to test recursion) — verify file discovery, correct `source` path, and correct `offset` per line.

## Person 2 — Matching (`src/matching/normalizer.py`, `matcher.py`, branch `feature/matching`)

- [ ] `normalize_text`: lowercase, and treat any amount of whitespace between words as equivalent (per spec, users may type extra/irregular spaces).
- [ ] `calculate_score`: implement the match definition —
  - [ ] Exact substring match (start, middle, or end of the sentence).
  - [ ] Fuzzy match allowed with **at most one** correction: substitution, insertion, or deletion.
  - [ ] Base score = 2 × number of matching characters (case-insensitive, including spaces, excluding punctuation).
  - [ ] Substitution penalty by position: 1st -5, 2nd -4, 3rd -3, 4th -2, 5th+ -1.
  - [ ] Insertion/deletion penalty by position: 1st -10, 2nd -8, 3rd -6, 4th -4, 5th+ -2.
  - [ ] Return `None` (no match) when more than one correction would be needed.
- [ ] Verify against the worked examples already in `README.md` (`To be` → 10, `or Not` → 12, `be, that` → 14, `2o be` → 5, `to pe` → 8, `or knot` → 8, `not be` → no match).
- [ ] Write `tests/test_matcher.py` using `tests/fixtures.py::TEST_SENTENCES`.

## Person 3 — Autocomplete (`src/autocomplete/autocomplete.py`, branch `feature/autocomplete`)

- [ ] `get_best_completions`: run `calculate_score` over every sentence.
- [ ] Filter out non-matches (`None` scores).
- [ ] Sort remaining matches by score descending; break ties alphabetically by the completed sentence text.
- [ ] Take the top 5 and build `AutoCompleteData` for each (`completed_sentence` = full original sentence text, `source_text`, `offset`, `score` copied from the `Sentence`/score).
- [ ] Write `tests/test_autocomplete.py` using `tests/fixtures.py::TEST_SENTENCES`.

## After all three branches merge (whoever picks it up)

- [ ] `main.py`: offline phase — call `load_sentences` once at startup against the real `data/Archive` path.
- [ ] `main.py`: online phase — REPL loop that reads typed characters, shows top-5 completions on Enter, lets the user keep typing from where they left off, and resets state on `#`.
