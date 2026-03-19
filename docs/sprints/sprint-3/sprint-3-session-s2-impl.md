# Sprint 3, Session S2: Granola Transcript Seeding (FF-004)

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/granola.py` (reference for pipeline functions)
   - `app/clustering.py` (for `assign_cluster`, `compute_xs`, `get_cluster_centroids`)
   - `app/embedding.py` (for `embed_text`)
   - `app/db.py` (for `insert_event`, `increment_event_count`, `update_event_xs`, `get_cluster_by_id`)
   - `docs/source/3-17-granola-transcript.md` (first 20 lines, to understand format)
   - `docs/source/3-18-granola-transcript.md` (first 20 lines, to understand format)
   - `tests/test_granola.py` (reference for test patterns)
2. Run scoped test baseline:
   ```
   python -m pytest tests/test_granola.py tests/test_db.py -x -q
   ```
   Expected: all passing (full suite confirmed by S1b close-out)
3. Verify you are on the correct branch: `main`

## Objective
Create a script that seeds the production database with real conversation data from two Granola transcripts. The script handles per-transcript speaker remapping, filters out short segments, and provides a dry-run mode for safe testing.

## Requirements

1. **Create `scripts/seed_transcript.py`:**

   The script should:

   a. **Parse command-line arguments:**
      - `--file` (required): path to transcript file
      - `--speaker-map` (required): JSON string mapping Speaker labels to participant names, e.g., `'{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}'`
      - `--default-participant` (optional, default `"shared"`): participant name for unmapped speakers
      - `--min-length` (optional, default `100`): minimum segment character length
      - `--dry-run` (optional flag): print analysis without DB/API calls

   b. **Read and parse the transcript:**
      - Read the file as text
      - Split on `^(Speaker [A-Z]):` pattern (same regex style as `app/granola.py`)
      - Map each speaker to participant using the provided speaker map; unmapped speakers get `default_participant`
      - Filter out segments shorter than `min_length` characters

   c. **Dry-run output:**
      When `--dry-run` is set, print:
      - Total segments found (before filtering)
      - Segments after filtering
      - Segment count per participant
      - First 80 chars of each segment (for visual inspection)
      - Do NOT call any API or DB functions

   d. **Live-run pipeline (per segment):**
      ```
      embed_text(segment_text)
      → assign_cluster(embedding, get_cluster_centroids())
      → insert_event(label, note, participant, embedding, source="granola", cluster_id)
      → increment_event_count(cluster_id)
      → get_cluster_by_id(cluster_id) → compute_xs → update_event_xs
      ```
      This mirrors the pipeline in `app/granola.py`'s `process_granola_upload`.

      - `label`: first 80 chars of segment text
      - `note`: full segment text
      - `source`: `"granola"`
      - Log progress every 10 segments: "Processed 10/178 segments..."
      - Log final summary: total inserted, per-participant counts, per-cluster counts

   e. **Error handling:**
      - If embedding fails for a segment, log the error and skip that segment (don't abort the entire run)
      - If DB insert fails for a segment, log and skip
      - Print final count of skipped segments

   f. **Usage examples (in docstring or comments):**
      ```
      # March 17 — dry run
      python -m scripts.seed_transcript \
        --file docs/source/3-17-granola-transcript.md \
        --speaker-map '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}' \
        --dry-run

      # March 17 — live
      python -m scripts.seed_transcript \
        --file docs/source/3-17-granola-transcript.md \
        --speaker-map '{"Speaker A": "steven", "Speaker B": "emma", "Speaker C": "jessie"}'

      # March 18 — live
      python -m scripts.seed_transcript \
        --file docs/source/3-18-granola-transcript.md \
        --speaker-map '{"Speaker B": "emma", "Speaker C": "jessie", "Speaker F": "steven"}'
      ```
      Note: March 18 unmapped speakers (A, D, E, G, H, I) default to "shared".

2. **Create `tests/test_seed_transcript.py`:**
   Test the parsing and filtering logic. Mock all external calls (embed_text, DB functions).

## Constraints
- Do NOT modify: any existing `app/` files, `static/index.html`, existing test files
- Do NOT add: new API endpoints, new DB tables, new dependencies
- Do NOT change: the existing `process_granola_upload` function or the `/granola` endpoint
- The script uses the same pipeline functions as `process_granola_upload` but is a standalone CLI tool, not integrated into the API

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `test_speaker_remapping_known` — "Speaker A" with map {"Speaker A": "steven"} → participant "steven"
  2. `test_speaker_remapping_unknown_defaults_shared` — "Speaker D" with no map entry → "shared"
  3. `test_min_length_filter_excludes_short` — segment "Yeah." (5 chars) excluded at min_length=100
  4. `test_min_length_filter_includes_long` — segment with 150 chars included at min_length=100
  5. `test_dry_run_no_api_calls` — with --dry-run, no embed_text/insert_event calls made (mock and verify call count = 0)
  6. `test_end_to_end_mock_pipeline` — parse a small test transcript (3 segments, 2 above threshold), mock pipeline, verify 2 events inserted with correct participants
- Minimum new test count: 6
- Test command: `python -m pytest -n auto -q`

## Definition of Done
- [ ] `scripts/seed_transcript.py` exists and runs without error on both transcripts (dry-run)
- [ ] Speaker remapping works correctly for both transcript formats
- [ ] Segments < 100 chars filtered out
- [ ] Dry-run mode prints analysis without API/DB calls
- [ ] Live-run mode processes segments through full pipeline
- [ ] Error handling: individual segment failures logged and skipped
- [ ] Progress logging implemented
- [ ] All existing tests pass
- [ ] 6 new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| No existing app/ files modified | `git diff --name-only` shows only scripts/ and tests/ |
| Existing granola tests pass | `python -m pytest tests/test_granola.py -x -q` |
| Existing telegram tests pass | `python -m pytest tests/test_telegram.py -x -q` |
| Script is importable | `python -c "import scripts.seed_transcript"` succeeds |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3/session-s2-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3/session-s2-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_seed_transcript.py -x -q`
5. Files that should NOT have been modified: all `app/` files, `static/index.html`, existing test files

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3/session-s2-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify the script does NOT modify any existing `app/` files
2. Verify speaker remapping handles both March 17 (3 speakers, all mapped) and March 18 (9 speakers, 3 mapped, 6 default to shared) formats
3. Verify dry-run mode truly makes zero API/DB calls (no embed_text, no insert_event)
4. Verify individual segment errors don't abort the entire run
5. Verify the pipeline matches `process_granola_upload` (embed → assign → insert → increment → xs)
6. Verify minimum length filter uses character count, not word count

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: ~125 collected, ~122 pass, ~3 skip
- Hard floor: ≥118 pass

### Critical Invariants
- No app/ files modified — all existing pipeline behavior unchanged
- All API endpoint contracts unchanged
- All existing tests pass

## Sprint-Level Escalation Criteria
1. Seeding produces >500 events → pause and assess
2. Test pass count drops below 118 → investigate
3. Script needs to modify app/ files → escalate to Work Journal
