# Project status

## What's been done (setup / foundation, on `main`)

- Reviewed the skeleton and confirmed the loader / matching / autocomplete split is workable for 3 parallel developers.
- Added `src/models.py` with the shared contract: `Sentence` (text, normalized_text, source, offset) and `AutoCompleteData` (completed_sentence, source_text, offset, score).
- Type-hinted the four interface functions against those shared types:
  - `load_sentences(root_path: str) -> List[Sentence]`
  - `normalize_text(text: str) -> str` — owned by Person 1 (`src/loader/normalizer.py`)
  - `calculate_score(query: str, sentence: Sentence) -> Optional[int]` — implemented and tested (Person 2)
  - `get_best_completions(query: str, sentences: List[Sentence]) -> List[AutoCompleteData]`
- **Architecture update:** Person 1 now owns normalization and candidate search, not just file loading (see updated Person 1/2 sections below). `Sentence.normalized_text` is populated by Person 1 at load time; `calculate_score` no longer normalizes anything itself — it expects an already-normalized `query` and reads `sentence.normalized_text` directly. `Sentence.text` stays untouched (original casing/punctuation), since the final output must show the sentence as it appears in the source file.
- Fixed `src/main.py` imports so it runs as a package (`python -m src.main` from repo root).
- Added `.gitignore` rules: real dataset (`data/Archive/*`, 120MB+) excluded from git.
- Added `data/Archive/sample/` — a small, committed dataset (incl. a nested folder) for local debugging, using the project spec's worked example sentence so scores can be checked against known values.
- Added `tests/fixtures.py` with `TEST_SENTENCES` as ready-made `Sentence` objects, so matching/autocomplete can be tested without the loader at all.
- Documented all of the above in `README.md` (run instructions, ownership table, sample data, worked score table).
- Committed everything to `main` and pushed it.
- Replaced the old unrelated branches with `feature/data-loader`, `feature/matching`, `feature/autocomplete`, pushed to origin, each tracking its remote counterpart.

None of the actual algorithm logic has been written yet — that's the checklist below.

---

## Person 1 — Data Loader + Search (`src/loader/`, branch `feature/data-loader`)

- [ ] Recursively walk `root_path` and find every `.txt` file, at any folder depth.
- [ ] Read each file, treating each line as one sentence.
- [ ] For each line, build a `Sentence(text=<original line>, normalized_text=normalize_text(<line>), source=<file path>, offset=<line number>)`.
- [x] `normalize_text` (`src/loader/normalizer.py`): lowercase, strip punctuation, collapse whitespace — done, moved here from `matching`.
- [ ] Decide and document the offset convention (0-indexed vs 1-indexed) — tell Person 2/3, since `AutoCompleteData.offset` in the final output depends on it.
- [ ] Decide how empty lines are handled (skip vs keep) and document it.
- [ ] Read files as UTF-8; decide what happens on a decode error (skip file? skip line?).
- [ ] Return the combined `List[Sentence]` across all files.
- [ ] **Candidate search** — proposed design (n-gram/trigram inverted index), not yet finalized with the team: given a raw query, normalize it and return the shortlist of candidate `Sentence`s for Person 2 to score, instead of Person 3 scanning the whole corpus. Confirm interface shape (e.g. `get_candidates(query: str) -> List[Sentence]`) before building.
- [ ] Write `tests/test_loader.py` using `data/Archive/sample` (has a nested subfolder specifically to test recursion) — verify file discovery, correct `source` path, and correct `offset` per line.

## Person 2 — Matching (`src/matching/matcher.py`, branch `feature/matching`) — done

- [x] `calculate_score(query, sentence)`: assumes `query` is already normalized and reads `sentence.normalized_text` — does **not** normalize anything itself anymore.
  - [x] Exact substring match (start, middle, or end of the sentence).
  - [x] Fuzzy match allowed with **at most one** correction: substitution, insertion, or deletion.
  - [x] Base score = 2 × number of matching characters.
  - [x] Substitution penalty by position: 1st -5, 2nd -4, 3rd -3, 4th -2, 5th+ -1.
  - [x] Insertion/deletion penalty by position: 1st -10, 2nd -8, 3rd -6, 4th -4, 5th+ -2.
  - [x] Returns `None` when more than one correction would be needed.
- [x] Verified against the worked examples in `README.md`.
- [x] `tests/test_matcher.py` — 6 tests, all passing.

## Person 3 — Autocomplete (`src/autocomplete/autocomplete.py`, branch `feature/autocomplete`)

- [ ] `get_best_completions`: run `calculate_score` over the candidate sentences (from Person 1, once that exists — full corpus for now).
- [ ] **Open question, confirm with Person 1:** `calculate_score` needs an already-normalized `query`. Decide who normalizes the raw user input once — Person 1's search step, or `get_best_completions` itself — so it isn't normalized twice or missed.
- [ ] Filter out non-matches (`None` scores).
- [ ] Sort remaining matches by score descending; break ties alphabetically by the completed sentence text.
- [ ] Take the top 5 and build `AutoCompleteData` for each (`completed_sentence` = full **original** `sentence.text`, not `normalized_text`; plus `source_text`, `offset`, `score`).
- [ ] Write `tests/test_autocomplete.py` using `tests/fixtures.py::TEST_SENTENCES`.

## After all three branches merge (whoever picks it up)

- [ ] `main.py`: offline phase — call `load_sentences` once at startup against the real `data/Archive` path.
- [ ] `main.py`: online phase — REPL loop that reads typed characters, shows top-5 completions on Enter, lets the user keep typing from where they left off, and resets state on `#`.
