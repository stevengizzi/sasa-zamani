# Sprint 1, Session 2b: Pydantic Models + Read Endpoints

## Pre-Flight Checks
Before making any changes:
1. Read these files to load context:
   - `app/main.py`
   - `app/config.py`
   - `app/db.py`
2. Run the test baseline:
   Scoped: `python -m pytest tests/test_db.py tests/test_health.py -x -q`
   Expected: ~13 tests, all passing
3. Verify you are on the correct branch: `sprint-1` (or `main`)

## Objective
Define Pydantic request/response models for all API data types and implement the GET /events (with participant filter) and GET /clusters read endpoints.

## Requirements

1. Create `app/models.py` — Pydantic models:
   - `EventResponse`: id (UUID), label (str), note (str | None), participant (str), cluster_id (UUID | None), created_at (datetime), source (str)
     - Note: does NOT include embedding field (too large for API response)
   - `ClusterResponse`: id (UUID), name (str), event_count (int)
     - Note: does NOT include centroid_embedding field
   - `HealthResponse`: status (str), database (str)
   - `ErrorResponse`: detail (str)
   - `GranolaRequest`: transcript (str) — for POST /granola (used in Session 4b, defined now for completeness)

2. Update `app/main.py`:
   - `GET /events` → calls `db.get_events(participant)`, returns `list[EventResponse]`
     - Optional query param: `participant: str | None = None`
     - Participant filter is case-insensitive (handle in db.py or endpoint)
     - Returns empty list `[]` when no events match, not an error
   - `GET /clusters` → calls `db.get_clusters()`, returns `list[ClusterResponse]`
   - Update `GET /health` to use `HealthResponse` model
   - Add proper response_model declarations to all endpoints for OpenAPI docs

3. Create `tests/test_endpoints.py`:
   - Test GET /events returns 200 with empty list when no events
   - Test GET /events returns correct event structure (all fields present, no embedding)
   - Test GET /events?participant=jessie filters correctly
   - Test GET /events?participant=Jessie (uppercase) returns same results as lowercase
   - Test GET /events?participant=nonexistent returns empty list, not error
   - Test GET /clusters returns 200 with list
   - Test GET /clusters response has correct structure (no centroid_embedding)
   - Test GET /health returns HealthResponse format
   - Test EventResponse model validates correctly
   - Test ClusterResponse model validates correctly

   **Note:** These tests need seed data in the DB. Either:
   - Use fixtures that insert test events/clusters via db.py functions before each test
   - Or mock db.py functions if using unit-test approach
   - Be consistent with the testing strategy chosen in Session 2a

## Constraints
- Do NOT modify: `static/index.html`, any files under `docs/`
- Do NOT create: POST endpoints (those are Sessions 4a, 4b)
- Do NOT add: embedding or clustering logic
- Do NOT change: db.py function signatures established in Session 2a (only call them)

## Test Targets
After implementation:
- Existing tests: all must still pass
- New tests to write: listed in Requirements #3
- Minimum new test count: 10
- Test command: `python -m pytest -x -q`

## Definition of Done
- [ ] All requirements implemented
- [ ] GET /events returns valid JSON, filters by participant (case-insensitive)
- [ ] GET /events returns empty array on empty DB (not error)
- [ ] GET /clusters returns valid JSON
- [ ] Response models exclude embedding and centroid_embedding fields
- [ ] All existing tests still pass
- [ ] All new tests pass
- [ ] Close-out report written to file
- [ ] Tier 2 review completed via @reviewer subagent

## Regression Checklist (Sprint-Level)
| Check | How to Verify |
|-------|---------------|
| Health endpoint returns 200 | `pytest tests/test_health.py -k health` |
| Health endpoint reports DB status | Verify "database" field in response |
| GET /events returns valid JSON on empty DB | `pytest tests/test_endpoints.py -k "events and empty"` |
| GET /events excludes embedding | Verify no "embedding" key in response |
| GET /clusters excludes centroid_embedding | Verify no "centroid_embedding" key in response |

## Sprint-Level Escalation Criteria
1. Supabase pgvector unavailable → STOP
2. Railway deployment fails 3+ consecutive times → STOP
3. OpenAI embedding dimensions ≠ 1536 → STOP
4. Degenerate cluster assignment (>80% to one cluster) → STOP
5. Cosine similarity uniformly > 0.95 or < 0.1 → STOP
6. Any session exceeds 2× estimated test count → STOP
7. supabase-py requires >20 lines raw SQL for vector ops → escalate
8. Telegram webhook needs different endpoint structure → escalate
9. Compaction in Session 4b → partial close-out + follow-up

## Close-Out
After all work is complete, follow the close-out skill in .claude/workflow/claude/skills/close-out.md.

The close-out report MUST include a structured JSON appendix at the end,
fenced with ```json:structured-closeout.

**Write the close-out report to a file:**
docs/sprints/sprint-1/session-2b-closeout.md

## Tier 2 Review (Mandatory — @reviewer Subagent)
Provide the @reviewer with:
1. The review context file: `docs/sprints/sprint-1/review-context.md`
2. The close-out report path: `docs/sprints/sprint-1/session-2b-closeout.md`
3. The diff range: `git diff HEAD~1`
4. The test command: `python -m pytest tests/test_endpoints.py -x -q`
5. Files that should NOT have been modified: `static/index.html`, `app/db.py` (should only be called, not modified), anything under `docs/` (except sprint reports)

The @reviewer will write its report to: docs/sprints/sprint-1/session-2b-review.md

## Session-Specific Review Focus (for @reviewer)
1. Verify EventResponse model does NOT include an embedding field
2. Verify ClusterResponse model does NOT include a centroid_embedding field
3. Verify participant filter is case-insensitive
4. Verify GET /events with unknown participant returns [] not 404
5. Verify response_model is declared on all endpoints for OpenAPI documentation
6. Verify db.py was not modified (only called)
