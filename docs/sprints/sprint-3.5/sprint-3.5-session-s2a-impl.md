# Sprint 3.5, Session S2a: Granola + Seed Transcript Pipeline Integration

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/segmentation.py` (the module being integrated — understand `segment_transcript`, `Segment` dataclass)
   - `app/granola.py` (current implementation being replaced)
   - `scripts/seed_transcript.py` (current implementation being replaced)
2. Run scoped test baseline:
   ```
   python -m pytest tests/test_granola.py tests/test_seed_transcript.py -x -q
   ```
   Expected: all passing (full suite confirmed by S1b close-out)
3. Verify you are on the correct branch: `main`

## Objective
Replace speaker-turn regex parsing in both `app/granola.py` and `scripts/seed_transcript.py` with thematic segmentation from `app/segmentation.py`. Events now get LLM-generated labels and multi-participant attribution.

## Requirements

1. **In `app/granola.py` — replace parsing with segmentation:**

   a. Remove the existing regex-based `parse_transcript()` function (or replace its body).

   b. In `process_granola_upload()`, replace the call to `parse_transcript()` with a call to `segment_transcript()` from `app/segmentation`:
   ```python
   from app.segmentation import segment_transcript, SegmentationError
   segments = segment_transcript(transcript_text, speaker_map, default_participant)
   ```

   c. For each segment:
   - `participant = "shared"` if `len(segment.participants) > 1` else `segment.participants[0]` if segment.participants else "shared"
   - `label = segment.label` (LLM-generated, replaces `text[:80]`)
   - `note = segment.text` (full segment content)
   - Pass `participants=segment.participants` to `insert_event()`

   d. If `segment_transcript()` raises `SegmentationError`, let it propagate — the upload fails with a descriptive error. Do NOT fall back to regex splitting silently.

   e. Preserve existing error handling for per-segment failures (embed, insert, increment, xs — each in try/except, skip on failure).

   f. The `speaker_map` and `default_participant` parameters must come from the request or be configurable. Check the current `process_granola_upload` signature and preserve it, adding `speaker_map` and `default_participant` if not already present.

2. **In `scripts/seed_transcript.py` — replace parsing with segmentation:**

   a. Remove the `Speaker [A-Z]:` regex and the local `parse_transcript()` function.

   b. In the pipeline, replace with:
   ```python
   from app.segmentation import segment_transcript
   segments = segment_transcript(transcript_text, speaker_map, default_participant)
   ```

   c. Same participant logic as granola.py (requirement 1c above).

   d. `--dry-run` must still work. During dry-run, segmentation IS called (it's part of parsing), but no DB/embedding calls are made. The dry-run output should print thematic segments with their labels and attributed speakers.

   e. `--min-length` filter applied AFTER segmentation (filter out segments where `len(segment.text) < min_length`).

   f. `--date`, `--speaker-map`, `--default-participant` flags preserved.

   g. Progress logging and final summary preserved (total inserted, per-participant, per-cluster).

   h. `--speaker-map` format stays the same (JSON string), but its purpose changes: it maps raw speaker labels from the transcript to participant names. Update the help text to reflect thematic segmentation context.

## Constraints
- Do NOT modify: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `app/db.py`, `app/models.py`, `app/segmentation.py`, `static/index.html`, `tests/conftest.py`
- Do NOT change: the embedding, clustering, increment, or xs computation logic (only the parsing/segmentation stage changes)
- Do NOT change: the `insert_event()` call pattern beyond adding `participants` parameter
- Do NOT add: new API endpoints

## Test Targets
After implementation:
- Existing tests: update tests that mock the old parsing to mock `segment_transcript` instead. Tests that test embedding/insert/increment/xs behavior should still pass with the new segment shape.
- New tests to write:
  1. `test_granola_uses_segmentation` — mock `segment_transcript`, verify it's called with transcript text and speaker_map
  2. `test_granola_multi_speaker_sets_shared` — mock segment with 2 participants, verify `participant="shared"` and `participants=["steven", "emma"]` passed to insert
  3. `test_granola_single_speaker_sets_name` — mock segment with 1 participant, verify `participant="steven"` and `participants=["steven"]`
  4. `test_seed_uses_segmentation` — mock `segment_transcript`, verify integration
  5. `test_seed_dry_run_calls_segmentation` — dry-run calls `segment_transcript` but not `insert_event`
- Minimum new test count: 5
- Test command: `python -m pytest tests/test_granola.py tests/test_seed_transcript.py -x -q`

## Definition of Done
- [ ] `app/granola.py` uses `segment_transcript()` instead of regex parsing
- [ ] `scripts/seed_transcript.py` uses `segment_transcript()` instead of regex parsing
- [ ] Multi-speaker segments produce `participant="shared"` with full `participants` array
- [ ] Single-speaker segments use that speaker's name
- [ ] Labels come from segmentation (LLM-generated), not `text[:80]`
- [ ] `--dry-run` still works (segmentation called, no DB)
- [ ] `--min-length` applied post-segmentation
- [ ] Segmentation failure fails the upload (no silent fallback)
- [ ] All existing tests pass (updated as needed for new parsing)
- [ ] 5 new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Granola upload pipeline end-to-end | Updated test_granola tests pass |
| seed_transcript dry-run works | Updated test confirms segmentation called, DB not called |
| seed_transcript live pipeline | Updated test_seed_transcript tests pass |
| Per-segment error handling preserved | Existing error-handling tests still pass |
| No changes to embedding/clustering/xs logic | `app/clustering.py`, `app/embedding.py` not modified |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3.5/session-s2a-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3.5/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3.5/session-s2a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_granola.py tests/test_seed_transcript.py -x -q`
5. Files that should NOT have been modified: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `app/db.py`, `app/models.py`, `app/segmentation.py`, `static/index.html`, `tests/conftest.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3.5/session-s2a-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify `parse_transcript()` regex logic is fully removed (no dead code left behind)
2. Verify `segment_transcript()` is called with the correct speaker_map and default_participant
3. Verify multi-speaker participant logic: `"shared"` when >1, single name when 1, `"shared"` when 0
4. Verify `participants` array is passed through to `insert_event()`
5. Verify segmentation failure propagates (not caught silently — the upload should fail)
6. Verify `--dry-run` calls segmentation but NOT `insert_event`, `embed_text`, or any DB function
7. Verify `--min-length` is applied to `segment.text` after segmentation, not to raw speaker turns
8. Verify labels come from `segment.label`, not `text[:80]`

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass

### Critical Invariants
- Granola pipeline processes uploads (with new segmentation)
- seed_transcript.py dry-run works
- Embedding/clustering/xs logic untouched
- Myth generation pipeline untouched

## Sprint-Level Escalation Criteria
1. Segmentation output ratio anomaly: < 50% or > 150% of speaker-turn count
2. Test pass count drops below 118
3. Changes needed to `app/segmentation.py` discovered during integration → escalate to work journal
