# Sprint 2, Session S1: Backend xs Computation + API Response Enrichment

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/clustering.py`
   - `app/db.py`
   - `app/models.py`
   - `app/config.py`
   - `docs/sprints/sprint-2/sprint-spec.md` (acceptance criteria for deliverables 1 and 2)
2. Run the test baseline:
   Full suite: `python -m pytest -x -q -n auto`
   Expected: 93 tests (90 pass, 3 skip)
3. Verify you are on the correct branch: `main` (or `sprint-2` if branching)

## Objective
Add server-side xs computation to the cluster assignment flow so each event gets a semantic x-position stored in the database. Enrich API responses with fields the frontend needs (xs, day, glyph_id, myth_text, is_seed).

## Requirements

1. **In `app/clustering.py`:** Add a `compute_xs(cluster_name: str, event_index: int, cluster_event_count: int) -> float` function:
   - Map each seed cluster name to a canonical xs center on the inward↔social spectrum:
     - "The Gate" → 0.12
     - "The Silence" → 0.15
     - "The Hand" → 0.25
     - "The Root" → 0.38
     - "What the Body Keeps" → 0.50
     - "The Table" → 0.82
   - For unknown cluster names (future dynamic clusters), default to 0.50
   - Apply a per-event offset: spread events within a cluster across a range of ±0.06 around the center, using event_index and cluster_event_count to distribute evenly. Add a small deterministic jitter (hash-based, not random) so values are reproducible.
   - Clamp final result to [0.0, 1.0]
   - Call `compute_xs` at the end of the cluster assignment flow (after cluster_id is determined), pass the result to `insert_event`

2. **In `app/db.py`:**
   - Add `xs: float | None = None` parameter to `insert_event()`. When provided, include in the insert data dict.
   - Add `update_event_xs(event_id: str, xs: float) -> None` function for backfill use.
   - Verify `get_events()` already selects `xs` and `day` columns (it does — check the select string includes them).

3. **In `app/models.py`:**
   - Add `xs: float | None = None` and `day: int | None = None` to `EventResponse`
   - Add `glyph_id: str | None = None`, `myth_text: str | None = None`, and `is_seed: bool = False` to `ClusterResponse`

4. **Create `scripts/backfill_xs.py`:**
   - Script that fetches all events from the database, looks up each event's cluster name, and calls `compute_xs` to fill in missing xs values
   - Uses `update_event_xs` for each event
   - Idempotent: overwrites existing xs values (rerunning produces same results due to deterministic jitter)
   - Prints summary: "Updated N events with xs values"
   - Can be run with: `python -m scripts.backfill_xs` or `python scripts/backfill_xs.py`

## Constraints
- Do NOT modify: `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `Procfile`, any files in `scripts/` except the new `backfill_xs.py`
- Do NOT change: cluster assignment logic (threshold, centroid comparison). xs computation is an additive step after assignment completes.
- Do NOT change: the behavior of existing API endpoints. New fields in responses are additive only.
- Do NOT add: any new API endpoints. This session enriches existing responses.

## Test Targets
After implementation:
- Existing tests: all 90 passing tests must still pass (3 skips unchanged)
- New tests to write:
  1. `compute_xs` returns correct center for each of the 6 seed cluster names
  2. `compute_xs` returns 0.50 for unknown cluster name
  3. `compute_xs` output is in [0.0, 1.0] for all cluster names and various event_index/count values
  4. `compute_xs` produces different values for different event_index within same cluster (no stacking)
  5. `insert_event` stores xs when provided (mock Supabase call, verify xs in data dict)
  6. `EventResponse` serializes with xs and day fields (model validation test)
  7. `ClusterResponse` serializes with glyph_id, myth_text, is_seed fields (model validation test)
- Minimum new test count: 6
- Test file: `tests/test_clustering.py` (extend existing) and `tests/test_endpoints.py` (extend existing) or new `tests/test_models.py`
- Test command: `python -m pytest -x -q -n auto`

## Config Validation
No config changes in this session (ANTHROPIC_API_KEY is added in S3a).

## Definition of Done
- [ ] `compute_xs` function implemented and integrated into cluster assignment flow
- [ ] `insert_event` accepts and stores xs
- [ ] `update_event_xs` function exists for backfill
- [ ] `EventResponse` includes xs, day
- [ ] `ClusterResponse` includes glyph_id, myth_text, is_seed
- [ ] `scripts/backfill_xs.py` created and runnable
- [ ] All existing tests pass
- [ ] 6+ new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| Existing EventResponse shape preserved | `GET /events` returns id, label, note, participant, cluster_id, created_at, source (all still present) |
| Existing ClusterResponse shape preserved | `GET /clusters` returns id, name, event_count (all still present) |
| Telegram pipeline still works | Existing test_telegram.py tests pass |
| Cluster assignment logic unchanged | Existing test_clustering.py tests pass |
| insert_event backward compatible | Calls without xs param still work (default None) |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout. See the close-out skill for the
full schema and requirements.

**Write the close-out report to a file:**
docs/sprints/sprint-2/session-s1-closeout.md

Do NOT just print the report in the terminal. Create the file, write the
full report (including the structured JSON appendix) to it, and commit it.

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-2/review-context.md`
2. The close-out report path: `docs/sprints/sprint-2/session-s1-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_clustering.py tests/test_endpoints.py -x -q`
5. Files that should NOT have been modified: `app/telegram.py`, `app/granola.py`, `app/embedding.py`, `Procfile`, `scripts/init_supabase.sql`, `scripts/seed_clusters.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-2/session-s1-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the post-review fix
documentation protocol in the implementation prompt template.

## Session-Specific Review Focus (for @reviewer)
1. Verify `compute_xs` centers match the spec exactly (The Gate 0.12, The Silence 0.15, The Hand 0.25, The Root 0.38, What the Body Keeps 0.50, The Table 0.82)
2. Verify xs values are deterministic (same inputs → same outputs, no `random`)
3. Verify `insert_event` is backward compatible (xs defaults to None)
4. Verify `EventResponse` and `ClusterResponse` changes are additive (no fields removed or renamed)
5. Verify `get_events()` select string includes xs and day columns
6. Verify `get_clusters()` select string includes glyph_id, myth_text, is_seed columns

## Sprint-Level Regression Checklist (for @reviewer)
- [ ] All 90 existing passing tests still pass
- [ ] GET /events returns correct data with all existing fields (additive only)
- [ ] GET /clusters returns correct data with all existing fields (additive only)
- [ ] POST /telegram processes and stores events
- [ ] Embedding pipeline unchanged (except xs at end)
- [ ] Seed cluster initialization unchanged
- [ ] CLUSTER_JOIN_THRESHOLD=0.3 unchanged
- [ ] app/telegram.py not modified
- [ ] app/granola.py not modified
- [ ] app/embedding.py not modified

## Sprint-Level Escalation Criteria (for @reviewer)
- Any session requires more than 1 compaction recovery → log in work journal
- 5+ existing tests fail → stop and assess
- Any session exceeds 2 compaction recovery attempts → Tier 3 review
