# Sprint 4, Session 2: DB Schema + Layer

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/db.py`
   - `scripts/init_supabase.sql`
   - `docs/sprints/sprint-4/sprint-spec.md`
2. Run scoped test baseline:
   `python -m pytest tests/test_db.py -x -q`
   Expected: all passing (full suite confirmed by Session 1 close-out)
3. Verify you are on branch: `sprint-4`

## Objective
Create the `raw_inputs` table for storing all incoming data (Granola transcripts and Telegram messages). Add `raw_input_id`, `start_line`, `end_line` columns to the events table. Implement the corresponding DB functions.

## Requirements

1. Create `scripts/migrate_sprint4.sql`:
   ```sql
   -- raw_inputs table
   CREATE TABLE raw_inputs (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     text TEXT NOT NULL,
     source TEXT NOT NULL,
     source_metadata JSONB DEFAULT '{}',
     created_at TIMESTAMPTZ DEFAULT now()
   );
   CREATE INDEX ON raw_inputs (source);

   -- Add FK columns to events
   ALTER TABLE events ADD COLUMN raw_input_id UUID REFERENCES raw_inputs(id);
   ALTER TABLE events ADD COLUMN start_line INTEGER;
   ALTER TABLE events ADD COLUMN end_line INTEGER;
   ```

2. Update `scripts/init_supabase.sql` to include the `raw_inputs` table (before events table, since events references it) and the new events columns. This is the canonical schema for fresh installations.

3. In `app/db.py`, add function:
   ```python
   def insert_raw_input(text: str, source: str, source_metadata: dict | None = None) -> dict:
       """Insert a raw input and return the inserted row."""
   ```

4. In `app/db.py`, add function:
   ```python
   def get_raw_input(raw_input_id: str) -> dict | None:
       """Return a raw input by ID, or None if not found."""
   ```

5. In `app/db.py`, update `insert_event()`:
   - Add optional parameters: `raw_input_id: str | None = None`, `start_line: int | None = None`, `end_line: int | None = None`
   - Include in the data dict only when not None (same pattern as existing optional fields)
   - Existing callers that don't pass these new params must continue to work unchanged

6. In `app/db.py`, update `ensure_schema()`:
   - Add `raw_inputs` to the list of tables to probe

7. In `app/db.py`, update `get_events()`:
   - Do NOT add raw_input_id, start_line, or end_line to the select list. The `/events` API contract must not change.

## Constraints
- Do NOT modify: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/granola.py`, `app/telegram.py`
- Do NOT change: The select list in `get_events()` or `get_clusters()` — API response schema must be preserved
- Do NOT add: New API endpoints

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write in `tests/test_db.py`:
  1. insert_raw_input returns row with id, text, source, source_metadata, created_at
  2. insert_raw_input stores source_metadata as JSONB correctly
  3. insert_raw_input with None source_metadata defaults to empty dict
  4. get_raw_input returns existing row by ID
  5. get_raw_input returns None for non-existent ID
  6. insert_event with raw_input_id, start_line, end_line stores correctly
  7. insert_event without new params still works (backward compatible)
  8. ensure_schema probes raw_inputs table
- Minimum new test count: 8
- Test command: `python -m pytest tests/test_db.py -x -q`

## Definition of Done
- [ ] All requirements implemented
- [ ] All existing tests pass
- [ ] ≥8 new tests written and passing
- [ ] Migration script ready to run on production
- [ ] init_supabase.sql updated as canonical schema
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Session-Specific)
| Check | How to Verify |
|-------|---------------|
| insert_event backward compatible | Existing test_db.py, test_granola.py, test_telegram.py pass |
| get_events does not return new columns | Inspect select list in get_events, run test_endpoints.py |
| ensure_schema checks raw_inputs | New test |

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-4/session-2-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
After the close-out is written to file and committed, invoke the @reviewer subagent.

Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-4/review-context.md`
2. The close-out report path: `docs/sprints/sprint-4/session-2-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_db.py tests/test_endpoints.py -x -q`
5. Files that should NOT have been modified: `app/main.py`, `app/myth.py`, `app/embedding.py`, `static/index.html`, `app/segmentation.py`, `app/clustering.py`, `app/granola.py`, `app/telegram.py`

The @reviewer will write its report to: docs/sprints/sprint-4/session-2-review.md

## Post-Review Fix Documentation
If the @reviewer reports CONCERNS and you fix the findings within this same
session, update both the close-out and review files per the implementation
prompt template instructions.

## Session-Specific Review Focus (for @reviewer)
1. Verify raw_inputs table DDL has correct column types and constraints
2. Verify events ALTER TABLE adds nullable FK (no NOT NULL — existing rows have no raw_input_id)
3. Verify get_events select list does NOT include raw_input_id, start_line, end_line
4. Verify insert_event backward compatibility (no required new params)
5. Verify migration script is idempotent-safe or has IF NOT EXISTS guards where appropriate

## Sprint-Level Regression Checklist
- [ ] All 166 pre-Sprint 4 tests pass
- [ ] `/events` GET returns valid JSON with existing field schema (no new columns)
- [ ] `/clusters` GET returns valid JSON with existing field schema
- [ ] insert_event() backward compatible
- [ ] ensure_schema() validates raw_inputs table
- [ ] New config fields have defaults

## Sprint-Level Escalation Criteria
1. Migration script fails on production → do not manually fix, escalate with error
2. raw_inputs FK or new event columns appear in API responses → escalate immediately
