# Tier 2 Review: Sprint 1, Session 2a

**Session:** Database Connection + Schema Creation
**Reviewer:** Tier 2 (automated)
**Date:** 2026-03-18
**Verdict:** PASS

---

## Test Results

```
python -m pytest tests/test_db.py -x -q  =>  9 passed
python -m pytest -x -q                   =>  14 passed (full suite)
```

No regressions. All 9 new tests pass, and all 5 pre-existing tests continue to pass.

---

## Session-Specific Review Focus

### 1. Events table has embedding column of type vector(1536)
**PASS.** `scripts/init_supabase.sql` line 27: `embedding VECTOR(1536)`. The Python code in `insert_event()` writes to this column, and `get_events()` explicitly omits it from the select list.

### 2. Clusters table has centroid column of type vector(1536)
**PASS with note.** `scripts/init_supabase.sql` line 9: `centroid VECTOR(1536)`. The SQL script uses `centroid`, not `centroid_embedding` as the sprint spec names it. The close-out correctly documents this naming deviation (judgment call #4) and the Python code is consistent with the SQL script. The SQL script is the source of truth for column names.

### 3. ensure_schema() is idempotent
**PASS with nuance.** `ensure_schema()` does not use `IF NOT EXISTS` DDL -- it does not create tables at all. Instead it probes each table with a zero-limit select. This is idempotent by nature (read-only operation). The close-out correctly documents that supabase-py cannot execute DDL, so schema creation is delegated to `scripts/init_supabase.sql`. The test `test_ensure_schema_is_idempotent` calls it twice without error and verifies all three tables are probed.

### 4. get_events() excludes embedding from returned data
**PASS.** `get_events()` uses an explicit column list in `.select()` that omits `embedding`. The test asserts `"embedding" not in events[0]`.

### 5. get_clusters() excludes centroid from returned data
**PASS.** `get_clusters()` uses an explicit column list that omits `centroid`. The test asserts `"centroid" not in clusters[0]`.

### 6. check_connection() handles Supabase being down gracefully
**PASS.** Wrapped in a bare `try/except Exception: return False`. Test `test_check_connection_returns_false_on_error` sets `table.side_effect = Exception("unreachable")` and asserts the return is `False`.

### 7. Escalation criteria #7: raw SQL for pgvector operations
**NO ESCALATION NEEDED.** Zero raw SQL is used in `app/db.py`. All operations use supabase-py's query builder (`.table().select()`, `.insert()`, `.update()`). The only SQL in the project is the one-time schema creation script (`scripts/init_supabase.sql`, 46 lines), which is expected and runs outside the application. Vector data is passed as Python lists through supabase-py's insert/select, which handles the pgvector serialization transparently.

---

## File Modification Audit

| File | Expected? | Verdict |
|------|-----------|---------|
| app/db.py | Yes (primary deliverable) | OK |
| app/main.py | Yes (health endpoint + startup) | OK |
| tests/conftest.py | Yes (DB mocks for lifespan) | OK |
| tests/test_health.py | Yes (assert new `database` field) | OK |
| tests/test_db.py | Yes (new, 9 tests) | OK |
| docs/sprints/sprint-1/session-2a-closeout.md | Yes (close-out report) | OK |
| docs/sprints/sprint-1/sprint-1-session-2a-impl.md | Yes (housekeeping section added + trailing newline) | OK |
| static/index.html | Must NOT be modified | NOT modified -- OK |

No forbidden files were touched.

---

## Code Quality

**Strengths:**
- Clean separation of concerns: `db.py` is a pure data-access module with no route logic
- Explicit column lists in `get_events()` and `get_clusters()` prevent leaking large vector data
- Singleton pattern with `reset_client()` escape hatch for tests is pragmatic
- `check_connection()` correctly swallows all exceptions and returns a boolean
- Test mocking strategy is well-structured with the `_chain` helper

**Observations (not blocking):**
- `increment_event_count()` is a read-then-write without atomicity. Documented in close-out as acceptable for v1 scale (3 users). Agree with this assessment.
- `ensure_schema()` will raise an opaque supabase exception if a table is missing. The error message won't directly tell the operator "run init_supabase.sql." A more descriptive error message could improve the operator experience, but this is minor.
- The `global _client` pattern in `get_db()` / `reset_client()` works but could eventually be replaced with dependency injection. Not a concern for v1.

---

## Regression Checklist Verification

| # | Invariant | Status |
|---|-----------|--------|
| 1 | Health endpoint returns 200 | PASS (test_health_returns_200) |
| 2 | Health endpoint reports DB status | PASS (asserts `database: connected`) |
| 3 | GET /events returns valid JSON array on empty DB | PASS (route still returns `[]` stub) |
| 12 | App starts cleanly with all env vars | PASS (full test suite passes) |
| 13 | App fails fast on missing env vars | PASS (test_missing_required_env_var_raises) |

Items 4-11, 14 are not yet testable (routes still return stubs; seed data not yet loaded). These will be verified in later sessions.

---

## Close-Out Report Accuracy

The close-out report is accurate. Self-assessment of MINOR_DEVIATIONS is appropriate given the `ensure_schema()` probe-vs-create deviation from what the review focus expected (`IF NOT EXISTS`). The judgment calls are well-reasoned and clearly documented.

---

## Findings Summary

| ID | Severity | Category | Description |
|----|----------|----------|-------------|
| F-1 | LOW | UX | `ensure_schema()` raises raw supabase exception on missing table -- could wrap with a more descriptive message pointing to `init_supabase.sql` |
| F-2 | INFO | Naming | `centroid` column name differs from spec's `centroid_embedding` -- correctly documented, SQL script is source of truth |
| F-3 | INFO | Atomicity | `increment_event_count` is not atomic -- documented, acceptable at v1 scale |

No blocking issues. No escalations required.

---

```json:structured-verdict
{
  "schema_version": "1.0",
  "sprint": "1",
  "session": "S2a",
  "reviewer": "tier-2",
  "verdict": "PASS",
  "tests_pass": true,
  "test_count": {
    "total": 14,
    "new": 9,
    "passing": 14,
    "failing": 0
  },
  "forbidden_file_violations": [],
  "scope_creep": false,
  "findings": [
    {
      "id": "F-1",
      "severity": "LOW",
      "category": "UX",
      "description": "ensure_schema() raises raw supabase exception on missing table; could wrap with descriptive message",
      "blocking": false,
      "file": "app/db.py",
      "line_range": "25-34"
    },
    {
      "id": "F-2",
      "severity": "INFO",
      "category": "naming",
      "description": "Column name 'centroid' differs from spec's 'centroid_embedding' -- SQL script is source of truth, documented in close-out",
      "blocking": false
    },
    {
      "id": "F-3",
      "severity": "INFO",
      "category": "atomicity",
      "description": "increment_event_count uses read+update pattern without atomic guarantee -- acceptable at v1 scale",
      "blocking": false,
      "file": "app/db.py",
      "line_range": "111-122"
    }
  ],
  "escalations": [],
  "regression_status": "PASS",
  "closeout_accurate": true,
  "recommendation": "Proceed to Session 2b"
}
```
