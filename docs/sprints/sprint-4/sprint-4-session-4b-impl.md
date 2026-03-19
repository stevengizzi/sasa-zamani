# Sprint 4, Session 4b: Seed Script Integration

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `scripts/seed_transcript.py`
   - `app/granola.py` (post-Session 4a — reference for pipeline pattern)
   - `app/segmentation.py` (post-Session 1)
   - `app/clustering.py` (post-Session 3)
   - `app/db.py` (post-Session 2)
   - `docs/sprints/sprint-4/sprint-spec.md`
2. Run scoped test baseline:
   `python -m pytest tests/test_seed_transcript.py -x -q`
   Expected: all passing
3. Verify you are on branch: `sprint-4`

## Objective
Wire all Sprint 4 features into the batch seeding script (`seed_transcript.py`), mirroring the pipeline changes made to `granola.py` in Session 4a. Update dry-run output to show significance scores and filtering decisions.

## Requirements

1. In `scripts/seed_transcript.py`, update `main()`:
   - After reading the transcript file, store it in raw_inputs: `insert_raw_input(text=transcript_text, source="granola", source_metadata={"file": args.file, "speaker_map": speaker_map, "date": args.date})`
   - Save the returned `raw_input_id`

2. In `scripts/seed_transcript.py`, update the segment processing flow:
   - After `segment_transcript()`, apply `dedup_labels(segments)`
   - After dedup, apply `filter_by_significance(segments, get_settings().significance_threshold)`
   - Replace the existing `filter_by_length()` call: significance filtering replaces min-length filtering. Remove the `--min-length` CLI arg and `filter_by_length()` function. Significance is the new quality gate.

3. In `scripts/seed_transcript.py`, update `run_pipeline()`:
   - Use `assign_or_create_cluster()` instead of `assign_cluster()`
   - If `created=True`, refresh centroids: `centroids = get_cluster_centroids()`
   - Pass `raw_input_id`, `segment.start_line`, `segment.end_line` to `insert_event()`
   - Call `maybe_name_cluster(cluster_id)` after `increment_event_count()`
   - Wrap `maybe_name_cluster` in try/except, log warning on failure
   - Track and print cluster creation events in output summary

4. In `scripts/seed_transcript.py`, update `print_dry_run()`:
   - Show significance score for each segment: `[{i}] (sig={segment.significance:.2f}) ({participant} | speakers: {speakers}) {segment.label}`
   - Show which segments would be filtered: mark segments below threshold with `[FILTERED]`
   - Show summary: "Segments above significance threshold: N / M"

5. Update imports:
   - Add: `filter_by_significance`, `dedup_labels` from `app.segmentation`
   - Add: `assign_or_create_cluster` from `app.clustering`
   - Add: `insert_raw_input` from `app.db`
   - Add: `maybe_name_cluster` from `app.archetype_naming`
   - Add: `get_settings` from `app.config`

6. Remove the `--min-length` CLI argument and `filter_by_length()` function.

## Constraints
- Do NOT modify: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/db.py`, `app/granola.py`, `app/telegram.py`
- Do NOT change: The `--file`, `--speaker-map`, `--date`, `--dry-run`, `--default-participant` CLI args (except removing `--min-length`)

## Test Targets
After implementation:
- Existing tests: all must still pass (update tests that reference `--min-length` or `filter_by_length`)
- New/updated tests in `tests/test_seed_transcript.py`:
  1. run_pipeline stores transcript in raw_inputs before processing
  2. run_pipeline calls dedup_labels on segments
  3. run_pipeline filters by significance (not min-length)
  4. run_pipeline uses assign_or_create_cluster
  5. run_pipeline refreshes centroids on new cluster creation
  6. print_dry_run shows significance scores
  7. print_dry_run marks filtered segments
  8. --min-length arg removed (argparse test)
- Minimum new test count: 5
- Test command: `python -m pytest tests/test_seed_transcript.py -x -q`

## Definition of Done
- [ ] All requirements implemented
- [ ] All existing tests pass (updated where needed for --min-length removal)
- [ ] ≥5 new tests written and passing
- [ ] Dry-run output shows significance scores and filtering
- [ ] filter_by_length removed
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| seed_transcript still runs end-to-end | Manual dry-run test or mock pipeline test |
| Dry-run mode still works | Test print_dry_run with mock segments |
| parse_args still handles required args | Test parse_args without --min-length |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-4/session-4b-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer subagent.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-4/review-context.md`
2. The close-out report path: `docs/sprints/sprint-4/session-4b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_seed_transcript.py -x -q`
5. Files that should NOT have been modified: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/db.py`, `app/granola.py`, `app/telegram.py`

The @reviewer will write its report to: docs/sprints/sprint-4/session-4b-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the implementation
prompt template instructions.

## Session-Specific Review Focus (for @reviewer)
1. Verify filter_by_length and --min-length are fully removed (no dead code)
2. Verify pipeline pattern matches Session 4a's granola.py (store → segment → dedup → filter → embed → assign/create → insert → name)
3. Verify dry-run output includes significance scores for all segments (not just filtered ones)
4. Verify raw_input storage happens before any processing (not after)
5. Verify centroid refresh only happens when created=True

## Sprint-Level Regression Checklist
- [ ] All pre-Sprint 4 tests pass
- [ ] Seed script processes transcripts end-to-end
- [ ] event_date, participants populated on seeded events

## Sprint-Level Escalation Criteria
1. Cluster explosion (>15 new clusters from existing data) → tune threshold
