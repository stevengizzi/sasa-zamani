# Sprint 3.5, Session S1b: Schema Integration (participants column)

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/db.py`
   - `app/models.py`
   - `scripts/init_supabase.sql`
2. Run scoped test baseline:
   ```
   python -m pytest tests/test_db.py -x -q
   ```
   Expected: all passing (full suite confirmed by S1a close-out)
3. Verify you are on the correct branch: `main`
4. Confirm the `participants` column has been added in Supabase:
   ```sql
   ALTER TABLE events ADD COLUMN participants jsonb DEFAULT '[]';
   ```
   This is a manual step the developer must complete before starting this session.

## Objective
Add `participants` support through the db/models layer so that events can store and return multi-speaker attribution.

## Requirements

1. **In `app/db.py` — update `insert_event()`:**
   - Add parameter: `participants: list[str] | None = None`
   - When not None, include `"participants": participants` in the insert data dict
   - Same conditional pattern as `cluster_id`, `xs`, `event_date`

2. **In `app/db.py` — update `get_events()` select list:**
   - Add `participants` to the select string (alongside existing fields)

3. **In `app/models.py` — update `EventResponse`:**
   - Add field: `participants: list[str] | None = None`

4. **In `scripts/init_supabase.sql` — document the column:**
   - Add `participants jsonb DEFAULT '[]'` to the events CREATE TABLE statement (documentation only — the actual migration is manual)

## Constraints
- Do NOT modify: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `app/segmentation.py`, `static/index.html`, `tests/conftest.py`
- Do NOT change: `insert_event()` behavior for existing callers (backward compatible — `participants` defaults to None)
- Do NOT change: any endpoint behavior or response shape beyond adding the `participants` field

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write:
  1. `test_insert_event_with_participants` — mock Supabase, call with `participants=["steven", "emma"]`, verify payload includes participants
  2. `test_insert_event_without_participants` — mock Supabase, call without participants, verify payload does NOT include participants key (backward compat)
  3. `test_event_response_includes_participants` — construct EventResponse with participants field, verify serialization
- Minimum new test count: 3
- Test command: `python -m pytest tests/test_db.py -x -q`

## Definition of Done
- [ ] `insert_event()` accepts optional `participants` parameter
- [ ] `get_events()` select includes `participants`
- [ ] `EventResponse` includes `participants` field
- [ ] `init_supabase.sql` documents the column
- [ ] Backward compatible — existing callers without `participants` still work
- [ ] All existing tests pass
- [ ] 3 new tests written and passing
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| `insert_event` backward compatible | Existing test_db tests pass without participants arg |
| `/events` endpoint still works | `python -m pytest tests/test_endpoints.py -x -q` |
| EventResponse serialization | New test verifies field present |
| No unintended files modified | `git diff --name-only` matches expected list |

## Close-Out
After all work is complete, follow the close-out skill in .claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-3.5/session-s1b-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer
subagent to perform the Tier 2 review within this same session.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-3.5/review-context.md`
2. The close-out report path: `docs/sprints/sprint-3.5/session-s1b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command (scoped): `python -m pytest tests/test_db.py tests/test_endpoints.py -x -q`
5. Files that should NOT have been modified: `app/config.py`, `app/embedding.py`, `app/myth.py`, `app/clustering.py`, `app/main.py`, `app/segmentation.py`, `static/index.html`, `tests/conftest.py`

The @reviewer will produce its review report and write it to:
docs/sprints/sprint-3.5/session-s1b-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the standard protocol.

## Session-Specific Review Focus (for @reviewer)
1. Verify `insert_event()` is backward compatible — `participants` defaults to None, omitted from payload when None
2. Verify `get_events()` select list includes `participants`
3. Verify `EventResponse` field type is `list[str] | None = None` (not `list[str]` which would fail on null DB values)
4. Verify `init_supabase.sql` change is documentation only (matches the actual ALTER TABLE)
5. Verify no changes to endpoint logic in `app/main.py`

## Sprint-Level Regression Checklist

### Test Suite Baseline
- Pre-sprint: 147 passed, 3 skipped, 3 pre-existing errors
- Hard floor: ≥118 pass

### Critical Invariants
- `insert_event()` backward compatible
- `/events` and `/clusters` endpoints return valid data
- Myth generation pipeline untouched

## Sprint-Level Escalation Criteria
1. Test pass count drops below 118
2. `insert_event()` backward compatibility broken
3. Schema change requires migration beyond single ALTER TABLE
