# Sprint 3, Session S1b: Pipeline Fixes

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/telegram.py`
   - `app/granola.py`
   - `app/db.py`
   - `tests/test_telegram.py`
   - `tests/test_granola.py`
2. Run scoped test baseline:
   ```
   python -m pytest tests/test_telegram.py tests/test_granola.py tests/test_db.py -x -q
   ```
   Expected: all passing (full suite confirmed by S1a close-out)
3. Verify you are on the correct branch: `main`

## Objective
Fix three pipeline-level deferred items: add error handling around the insert+increment sequence (DEF-012), cap the Telegram dedup set (DEF-013), and verify/fix the Granola upload return contract (DEF-014).

## Requirements

1. **In `app/telegram.py` — cap `_processed_update_ids` (DEF-013):**
   The in-memory set `_processed_update_ids` currently grows without bound. Add a cap of 10,000 entries. When a new update_id would exceed the cap, discard the oldest entries to make room.

   Implementation approach: convert from a plain `set` to an `OrderedDict` (used as ordered set) or maintain a companion list for ordering. When `len(_processed_update_ids) >= 10000`, remove the oldest entry before adding the new one.

   Update `is_duplicate()` to work with the new structure. The external behavior is identical: returns True for seen IDs, False for new ones. Add a log message at WARNING level when the cap is first hit (once, not on every eviction).

2. **In `app/granola.py` — insert+increment error handling (DEF-012):**
   In `process_granola_upload`, the sequence `insert_event(...)` followed by `increment_event_count(cluster_id)` is non-atomic. If the increment fails after the insert succeeds, the event exists but the cluster's event_count is stale by 1.

   Wrap the `increment_event_count` call in a try/except:
   ```python
   try:
       increment_event_count(cluster_id)
   except Exception as exc:
       logger.warning(
           "increment_event_count failed for cluster %s after event %s was inserted: %s",
           cluster_id, row.get("id"), exc,
       )
   ```
   Do NOT wrap `insert_event` — if that fails, the event wasn't created and no increment is needed. The function should still raise on insert failure.

   Apply the same pattern in `app/telegram.py`'s `process_telegram_update` function for its `increment_event_count` call.

3. **In `app/granola.py` — verify return contract (DEF-014):**
   `process_granola_upload` currently returns dicts with `cluster_name` field. Verify that this field contains the actual cluster name string (e.g., "The Gate"), NOT the cluster UUID. The current code (lines 112-119) looks up the cluster by ID and uses `cluster["name"]` — this should already be correct. If it is, add a brief code comment confirming the fix is in place. If for some reason it returns the UUID, fix it.

## Constraints
- Do NOT modify: `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `app/clustering.py`, `app/myth.py`, `static/index.html`, `scripts/seed_clusters.py`
- Do NOT change: any API endpoint response schemas
- Do NOT change: `extract_message`, `parse_transcript` function signatures or return types
- The dedup cap must not change the external behavior of `is_duplicate()` for IDs within the cap window

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `test_dedup_set_cap_enforced` — add 10,001 update_ids, verify set size stays ≤ 10,000
  2. `test_dedup_set_oldest_evicted` — add IDs 1–10,000, then add 10,001. Verify ID 1 is no longer considered a duplicate (evicted), but ID 10,000 still is (retained).
  3. `test_granola_return_contract_cluster_name` — call process_granola_upload with a mock pipeline, verify the returned `cluster_name` field is a string name (not a UUID pattern)
  4. `test_granola_increment_failure_event_survives` — mock `increment_event_count` to raise, verify `process_granola_upload` still returns the event (insert succeeded), and the error is logged
  5. `test_telegram_increment_failure_event_survives` — mock `increment_event_count` to raise in the telegram pipeline, verify event is still stored and function returns `processed: True`
- Minimum new test count: 5
- Test command: `python -m pytest -n auto -q`

## Definition of Done
- [ ] `_processed_update_ids` capped at 10,000 with oldest-eviction
- [ ] `increment_event_count` failures in granola pipeline are caught and logged (event preserved)
- [ ] `increment_event_count` failures in telegram pipeline are caught and logged (event preserved)
- [ ] Granola return contract verified (cluster_name = string name, not UUID)
- [ ] All existing tests pass
- [ ] 5 new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| `is_duplicate` still returns True for seen IDs | Existing telegram tests pass |
| `is_duplicate` still returns False for new IDs | Existing telegram tests pass |
| `process_telegram_update` happy path unchanged | Existing test_telegram tests pass |
| `process_granola_upload` happy path unchanged | Existing test_granola tests pass |
| Granola empty transcript still raises ValueError | Existing test |
| Granola embedding failure still raises EmbeddingError | Existing test |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3/session-s1b-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3/session-s1b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_telegram.py tests/test_granola.py -x -q`
5. Files that should NOT have been modified: `app/config.py`, `app/models.py`, `app/embedding.py`, `app/main.py`, `app/clustering.py`, `app/myth.py`, `static/index.html`, `scripts/seed_clusters.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3/session-s1b-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify dedup set cap actually evicts oldest entries (not random or newest)
2. Verify increment_event_count failure in granola pipeline doesn't suppress the event — the event must still be returned
3. Verify increment_event_count failure in telegram pipeline doesn't change the return value — must still return `processed: True`
4. Verify no changes to `extract_message` or `parse_transcript` signatures
5. Check that the warning log for dedup cap only fires once (not on every eviction)

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: ~125 collected, ~122 pass, ~3 skip
- Hard floor: ≥118 pass

### Critical Invariants
- All API endpoint contracts unchanged
- Telegram pipeline happy path: extract → dedup → embed → assign → store → xs
- Granola pipeline happy path: parse → embed → assign → store → increment → xs
- Myth generation unchanged
- Frontend unchanged

## Sprint-Level Escalation Criteria
1. Test pass count drops below 118 → investigate
2. File not in session's "Modifies" list needs changes → escalate to Work Journal
3. Deferred item fix reveals deeper architectural issue → escalate
