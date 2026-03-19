# Sprint 4, Session 4a: Granola Pipeline Integration

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/granola.py`
   - `app/segmentation.py` (post-Session 1 — significance, dedup, new Segment fields)
   - `app/clustering.py` (post-Session 3 — assign_or_create_cluster)
   - `app/db.py` (post-Session 2 — insert_raw_input, updated insert_event)
   - `docs/sprints/sprint-4/sprint-spec.md`
2. Run scoped test baseline:
   `python -m pytest tests/test_granola.py -x -q`
   Expected: all passing
3. Verify you are on branch: `sprint-4`
4. Verify migration has been applied: Session 2's `scripts/migrate_sprint4.sql` must have been run on the test DB (or tests mock the DB layer).

## Objective
Wire significance filtering, raw_input storage, label dedup, and new-cluster creation into the Granola upload pipeline (`process_granola_upload`).

## Requirements

1. In `app/granola.py`, update `process_granola_upload()` to follow this pipeline:
   1. **Store transcript** — Call `insert_raw_input(text=transcript, source="granola", source_metadata={"speaker_map": speaker_map, "default_participant": default_participant})`. Save the returned `raw_input_id`.
   2. **Segment** — Call `segment_transcript()` (unchanged call). Segments now carry start_line, end_line, significance.
   3. **Dedup labels** — Call `dedup_labels(segments)`.
   4. **Filter by significance** — Call `filter_by_significance(segments, get_settings().significance_threshold)`.
   5. **Embed** — Embed filtered segments (same as before).
   6. **Assign or create** — For each segment: call `assign_or_create_cluster()` instead of `assign_cluster()`. If `created=True`, refresh the centroids list by re-fetching from DB.
   7. **Insert event** — Call `insert_event()` with new fields: `raw_input_id=raw_input_id`, `start_line=segment.start_line`, `end_line=segment.end_line`.
   8. **Post-insert** — `increment_event_count()`, then `maybe_name_cluster(cluster_id)`, then `compute_xs()`.
   9. Return results as before.

2. Update imports in `app/granola.py`:
   - Add: `filter_by_significance`, `dedup_labels` from `app.segmentation`
   - Add: `assign_or_create_cluster` from `app.clustering`
   - Add: `insert_raw_input` from `app.db`
   - Add: `maybe_name_cluster` from `app.archetype_naming`
   - Add: `get_settings` from `app.config`

3. The centroid refresh pattern when a new cluster is created:
   ```python
   cluster_id, similarity, created = assign_or_create_cluster(embedding, centroids)
   if created:
       centroids = get_cluster_centroids()  # refresh so next event sees new cluster
   ```

4. Error handling for maybe_name_cluster: wrap in try/except, log warning on failure, do not block the pipeline.

## Constraints
- Do NOT modify: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/db.py`, `app/telegram.py`, `scripts/seed_transcript.py`
- Do NOT change: The function signature of `process_granola_upload()` — it still takes `(transcript, speaker_map, default_participant)` and returns `list[dict]`
- Do NOT change: The return dict structure — `{"event_id": ..., "participant": ..., "cluster_name": ...}`

## Test Targets
After implementation:
- Existing tests: all must still pass
- New/updated tests in `tests/test_granola.py`:
  1. process_granola_upload stores transcript in raw_inputs before segmentation
  2. process_granola_upload calls dedup_labels
  3. process_granola_upload filters by significance threshold
  4. process_granola_upload passes raw_input_id, start_line, end_line to insert_event
  5. process_granola_upload uses assign_or_create_cluster instead of assign_cluster
  6. process_granola_upload refreshes centroids when new cluster created
  7. process_granola_upload calls maybe_name_cluster after increment
- Minimum new test count: 6
- Test command: `python -m pytest tests/test_granola.py -x -q`

## Definition of Done
- [ ] All requirements implemented
- [ ] All existing tests pass
- [ ] ≥6 new tests written and passing
- [ ] Pipeline flow: store → segment → dedup → filter → embed → assign/create → insert → name
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| process_granola_upload still returns list[dict] | Existing test_granola.py structure tests |
| /granola endpoint still works | `python -m pytest tests/test_endpoints.py -x -q` |
| Empty transcript still raises ValueError | Existing test |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-4/session-4a-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer subagent.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-4/review-context.md`
2. The close-out report path: `docs/sprints/sprint-4/session-4a-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_granola.py tests/test_endpoints.py -x -q`
5. Files that should NOT have been modified: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/db.py`, `app/telegram.py`, `scripts/seed_transcript.py`

The @reviewer will write its report to: docs/sprints/sprint-4/session-4a-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the implementation
prompt template instructions.

## Session-Specific Review Focus (for @reviewer)
1. Verify raw_input is stored BEFORE segmentation (not after)
2. Verify centroid refresh happens only when created=True (not on every event)
3. Verify maybe_name_cluster failure does not block the pipeline
4. Verify significance filtering happens AFTER dedup (dedup all labels first, then filter)
5. Verify the old assign_cluster import is removed (replaced by assign_or_create_cluster)

## Sprint-Level Regression Checklist
- [ ] All pre-Sprint 4 tests pass
- [ ] Granola upload processes transcripts end-to-end
- [ ] event_date, participants, xs populated on new events
- [ ] insert_event() backward compatible

## Sprint-Level Escalation Criteria
1. Centroid refresh causes >120s per transcript upload → consider batching
2. Cluster explosion (>15 new clusters from existing data) → tune threshold
